# frontend/app.py
import streamlit as st
import requests
import base64
import os

st.set_page_config(page_title="Local Legal Assistant", layout="wide")
BACKEND = st.sidebar.text_input("Backend URL", "http://127.0.0.1:8000")

st.title("Local Legal Assistant — Simplify & Explain Laws")

st.header("1. Index law documents (these will be the knowledge base)")
uploaded_laws = st.file_uploader("Upload laws (PDF/DOCX/TXT)", accept_multiple_files=True, type=["pdf","docx","txt"])
if st.button("Upload & Index Laws"):
    if not uploaded_laws:
        st.warning("Choose files to upload.")
    else:
        for f in uploaded_laws:
            files = {"file": (f.name, f.getvalue())}
            resp = requests.post(f"{BACKEND}/ingest_law/", files=files)
            st.write(f"{f.name} → {resp.json()}")

st.markdown("---")
st.header("2. Analyze a legal document (uses only uploaded laws)")
doc = st.file_uploader("Upload the document you want explained", type=["pdf","docx","txt"])
cols = st.columns(3)
top_k = cols[0].slider("Top K retrieved", 1, 8, 4)
max_paras = cols[1].slider("Max paragraphs to analyze", 1, 8, 4)
lang = cols[2].selectbox("Language for translation/audio", ["en","hi","ta","te","ml"], index=0)
want_audio = st.checkbox("Return audio (mp3)", value=False)

if st.button("Analyze Document"):
    if not doc:
        st.warning("Please upload a document to analyze.")
    else:
        files = {"file": (doc.name, doc.getvalue())}
        data = {"top_k": top_k, "max_paragraphs": max_paras, "target_lang": lang, "want_audio": want_audio}
        # FastAPI form fields: use 'files' and 'data' with requests
        resp = requests.post(f"{BACKEND}/analyze_document/", files=files, data=data)
        result = resp.json()
        st.subheader("Analysis")
        st.write(f"File: {result.get('filename')}")
        st.write(f"Paragraphs analyzed: {result.get('paragraphs_analyzed')}")
        for r in result.get("results", []):
            st.markdown(f"**Paragraph {r['paragraph_index']}**")
            st.write(r["paragraph"])
            st.write(r["analysis"])
            with st.expander("Show retrieved law chunks used"):
                for chunk in r.get("retrieved", []):
                    md = chunk.get("metadata", {})
                    st.write(f"- Source: {md.get('source_file')} | chunk: {md.get('chunk_index')} | dist: {chunk.get('distance')}")
                    st.write(chunk.get("text")[:1000] + ("..." if len(chunk.get("text"))>1000 else ""))
        if result.get("translation"):
            st.markdown("### Translation")
            st.write(result["translation"])
        if result.get("audio_base64"):
            audio_bytes = base64.b64decode(result["audio_base64"])
            st.audio(audio_bytes, format="audio/mp3")
            st.download_button("Download MP3", audio_bytes, file_name="analysis.mp3", mime="audio/mpeg")

st.markdown("---")
st.header("3. Quick Q&A (single question against law DB)")
q = st.text_input("Ask a question about the laws indexed:")
q_topk = st.slider("Top K (Q&A)", 1, 8, 4, key="qtop")
q_lang = st.selectbox("Language (Q&A)", ["en","hi","ta","te","ml"], index=0, key="qlang")
q_audio = st.checkbox("Audio (Q&A)", value=False, key="qaudio")

if st.button("Ask"):
    if not q:
        st.warning("Type a question.")
    else:
        params = {"query": q, "top_k": q_topk, "target_lang": q_lang, "want_audio": q_audio}
        resp = requests.get(f"{BACKEND}/ask/", params=params)
        out = resp.json()
        st.write("### Answer")
        st.write(out.get("answer"))
        if out.get("audio_base64"):
            audio_bytes = base64.b64decode(out["audio_base64"])
            st.audio(audio_bytes, format="audio/mp3")
            st.download_button("Download Q&A MP3", audio_bytes, file_name="answer.mp3", mime="audio/mpeg")
        st.subheader("Retrieved chunks (from vector DB)")
        for r in out.get("retrieved", []):
            md = r.get("metadata", {})
            st.write(f"- Source: {md.get('source_file')} | chunk: {md.get('chunk_index')} | dist: {r.get('distance')}")
            with st.expander("Show text"):
                st.write(r.get("text")[:1000] + ("..." if len(r.get("text"))>1000 else ""))
