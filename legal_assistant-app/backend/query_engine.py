# backend/query_engine.py
from sentence_transformers import SentenceTransformer
from backend.rag_store import query_by_embedding
from backend.llm_service import generate_text

embedder = SentenceTransformer("all-MiniLM-L6-v2")

def build_context_block(retrieved):
    docs = retrieved.get("documents", [[]])[0]
    metas = retrieved.get("metadatas", [[]])[0]
    dists = retrieved.get("distances", [[]])[0]
    pieces = []
    for i, d in enumerate(docs):
        md = metas[i] if i < len(metas) else {}
        dist = dists[i] if i < len(dists) else None
        src = md.get("source_file", "unknown")
        idx = md.get("chunk_index", -1)
        pieces.append(f"[source: {src} | chunk: {idx} | dist: {dist:.4f}]\n{d}")
    return "\n\n---\n\n".join(pieces)

def rag_answer(query: str, top_k: int = 4):
    q_emb = embedder.encode([query], convert_to_numpy=True)[0].tolist()
    retrieved = query_by_embedding(q_emb, n_results=top_k)
    context = build_context_block(retrieved)

    prompt = f"""You are a legal assistant for non-lawyers. Use ONLY the context below to:
1) Give a short plain-language summary (1-3 sentences).
2) List legal risks (bullet points).
3) Provide immediate practical steps (1-3 items).
Cite the context in square brackets where appropriate.

CONTEXT:
{context}

QUESTION:
{query}

Answer:"""

    answer = generate_text(prompt, max_length=512)

    return {
        "answer": answer,
        "retrieved": [
            {"metadata": retrieved["metadatas"][0][i], "text": retrieved["documents"][0][i], "distance": retrieved["distances"][0][i]}
            for i in range(len(retrieved["documents"][0]))
        ]
    }
