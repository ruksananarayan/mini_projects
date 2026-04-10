# backend/preload.py
from backend.process_docs import process_all

if __name__ == "__main__":
    total = process_all()
    print(f"✅ Preloaded {total} chunks of laws into ChromaDB")
