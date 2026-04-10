import os
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from dotenv import load_dotenv

load_dotenv()

# Load model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Connect to Qdrant Cloud
qdrant_url = os.getenv("QDRANT_URL")
qdrant_api_key = os.getenv("QDRANT_API_KEY")

if not qdrant_url or not qdrant_api_key:
    raise ValueError("QDRANT_URL and QDRANT_API_KEY environment variables must be set")

client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, timeout=60.0)
collection_name = "rtl_rag"

query = "ALU module for addition and subtraction"

q_emb = model.encode(query).tolist()

results = client.query_points(
    collection_name=collection_name,
    query=q_emb,
    limit=3
)

for i, res in enumerate(results.points):
    print(f"\n--- Result {i+1} ---\n")
    
    # Handle tuple format
    if isinstance(res, tuple):
        payload = res[2]
    else:
        payload = res.payload
    
    print(payload["text"][:500])