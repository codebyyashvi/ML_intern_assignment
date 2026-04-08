import os

DATA_DIR = "../data"
OUTPUT_FILE = "../chunks/chunks.txt"

def chunk_verilog(file_path):
    with open(file_path, 'r', errors='ignore') as f:
        code = f.read()

    parts = code.split("module ")
    chunks = []

    for p in parts:
        p = p.strip()
        if p:
            chunk = "module " + p
            if "endmodule" in chunk:
                chunks.append(chunk)

    return chunks


def load_riscv_rules():
    path = os.path.join(DATA_DIR, "riscv_rules.txt")
    if os.path.exists(path):
        with open(path, "r", errors='ignore') as f:
            content = f.read()
            # Split into large semantic blocks (keep as fewer chunks)
            return [content]
    return []


def load_riscv_spec():
    path = os.path.join(DATA_DIR, "riscv_spec.txt")
    if os.path.exists(path):
        with open(path, "r", errors='ignore') as f:
            content = f.read()
            # Return as 2-3 chunks: RV32I basics, instructions, extensions
            # Split by major sections only
            chunks = []
            
            # Split on "## " (major section marker) or numbered sections like "2. ", "3. "
            parts = content.split("\n2.")
            if len(parts) > 1:
                # First part (intro/overview)
                if parts[0].strip():
                    chunks.append("Part 0: RISC-V Overview\n2." + parts[0])
                # Base integers section
                if parts[1].strip():
                    chunks.append("Part 1: RV32I Base Integer Instructions\n2." + parts[1])
            else:
                # If no split found, keep as one chunk
                chunks.append(content)
            
            return chunks
    return []


def process_all():
    all_chunks = []

    for root, _, files in os.walk(DATA_DIR):
        for file in files:
            if file.endswith(".v"):
                path = os.path.join(root, file)
                try:
                    all_chunks.extend(chunk_verilog(path))
                except:
                    continue

    # Add rules (as single chunk)
    all_chunks.extend(load_riscv_rules())
    
    # Add spec (as 2-3 large chunks)
    all_chunks.extend(load_riscv_spec())

    return all_chunks


if __name__ == "__main__":
    chunks = process_all()

    os.makedirs("../chunks", exist_ok=True)

    with open(OUTPUT_FILE, "w") as f:
        for c in chunks:
            f.write(c.strip() + "\n\n---\n\n")

    print(f"✅ Total chunks created: {len(chunks)}")