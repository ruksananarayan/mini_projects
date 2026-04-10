import os
import chromadb
from chromadb.config import Settings
from uuid import uuid4

# Base directory and Chroma DB folder
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")
os.makedirs(CHROMA_DIR, exist_ok=True)

# Initialize Chroma client with persistence
client = chromadb.Client(
    Settings(
        persist_directory=CHROMA_DIR,
        anonymized_telemetry=False  # disable telemetry
    )
)

COLLECTION_NAME = "laws"

# Function to get or create the collection
def get_collection():
    try:
        return client.get_collection(COLLECTION_NAME)
    except Exception:  # Fallback (works for all versions)
        return client.create_collection(name=COLLECTION_NAME)

# Function to add documents to the collection
def add_documents(chunks, metadatas=None, embeddings=None):
    col = get_collection()
    ids = [str(uuid4()) for _ in chunks]
    col.add(
        documents=chunks,
        metadatas=metadatas if metadatas else [{} for _ in chunks],
        ids=ids,
        embeddings=embeddings
    )
    return ids  # removed client.persist()

# Function to query by embedding
def query_by_embedding(embedding, n_results=5):
    col = get_collection()
    res = col.query(
        query_embeddings=[embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )
    return res
