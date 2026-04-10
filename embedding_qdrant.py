import os
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Load embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize Qdrant Cloud with longer timeout
qdrant_url = os.getenv("QDRANT_URL")
qdrant_api_key = os.getenv("QDRANT_API_KEY")

if not qdrant_url or not qdrant_api_key:
    raise ValueError("QDRANT_URL and QDRANT_API_KEY environment variables must be set")

client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, timeout=60.0)

collection_name = "rtl_rag"

# Check if collection exists, if so delete and recreate
if client.collection_exists(collection_name):
    client.delete_collection(collection_name)

# Create collection
client.create_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
)

# Load chunks
with open("./chunks/chunks.txt", "r") as f:
    raw = f.read()

chunks = raw.split("\n\n---\n\n")

print(f"📦 Loaded {len(chunks)} chunks")

# Insert embeddings in batches with retry logic
points = []
batch_size = 50  # Reduced from 100 to prevent timeout
max_retries = 3

for i, chunk in enumerate(chunks):
    chunk = chunk.strip()
    if not chunk:
        continue

    embedding = model.encode(chunk).tolist()

    points.append(PointStruct(
        id=i,
        vector=embedding,
        payload={"text": chunk}
    ))

    # Upload batch when it reaches batch_size
    if len(points) >= batch_size:
        for attempt in range(max_retries):
            try:
                client.upsert(collection_name=collection_name, points=points)
                print(f"✅ Uploaded {len(points)} points (Total: {i+1}/{len(chunks)})")
                points = []
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    print(f"⚠️  Upload failed, retrying in {wait_time}s... ({attempt+1}/{max_retries})")
                    print(f"   Error: {str(e)[:100]}")
                    time.sleep(wait_time)
                else:
                    print(f"❌ Upload failed after {max_retries} attempts")
                    raise

# Upload remaining points
if points:
    for attempt in range(max_retries):
        try:
            client.upsert(collection_name=collection_name, points=points)
            print(f"✅ Uploaded {len(points)} remaining points")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"⚠️  Upload failed, retrying in {wait_time}s... ({attempt+1}/{max_retries})")
                time.sleep(wait_time)
            else:
                print(f"❌ Upload failed after {max_retries} attempts")
                raise

print("✅ All data stored in Qdrant!")