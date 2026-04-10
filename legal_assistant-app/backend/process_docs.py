# backend/process_docs.py
import os
from sentence_transformers import SentenceTransformer
from backend.rag_store import add_documents
from backend.text_extract import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_txt,
    chunk_text
)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DOCS_DIR = os.path.join(BASE_DIR, "legal_docs")
os.makedirs(DOCS_DIR, exist_ok=True)

embedder = SentenceTransformer("all-MiniLM-L6-v2")

def load_and_extract(path: str) -> str:
    """Detect file type and extract text."""
    with open(path, "rb") as f:
        content = f.read()
    
    if path.lower().endswith(".pdf"):
        return extract_text_from_pdf(content)
    elif path.lower().endswith(".docx"):
        return extract_text_from_docx(content)
    elif path.lower().endswith(".txt"):
        return extract_text_from_txt(content)
    else:
        print(f"⚠️ Unsupported file type: {path}")
        return ""

def process_and_store_one(path, filename=None):
    filename = filename or os.path.basename(path)
    text = load_and_extract(path)
    if not text.strip():
        print(f"⚠️ No text extracted from {filename}")
        return 0
    
    # ✅ Consistent overlapping chunking
    chunks = chunk_text(text, chunk_size=1000, overlap=200)
    
    embeddings = embedder.encode(chunks, convert_to_numpy=True).tolist()
    metadatas = [{"source_file": filename, "chunk_index": idx} for idx in range(len(chunks))]
    add_documents(chunks, metadatas, embeddings)
    print(f"✅ Indexed {filename}: {len(chunks)} chunks")
    return len(chunks)

def process_all():
    files = [f for f in os.listdir(DOCS_DIR) if f.lower().endswith((".pdf", ".docx", ".txt"))]
    total = 0
    for f in files:
        path = os.path.join(DOCS_DIR, f)
        total += process_and_store_one(path, f)
    print(f"Total chunks indexed: {total}")
    return total

if __name__ == "__main__":
    process_all()


