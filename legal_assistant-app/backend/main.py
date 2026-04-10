# backend/main.py
import os
import shutil
import base64
from fastapi import FastAPI, UploadFile, File, Form, Query
from pydantic import BaseModel
from typing import Optional




from backend.text_extract import extract_text_from_pdf, extract_text_from_docx, extract_text_from_txt, paragraph_split
from backend.process_docs import process_and_store_one, process_all, DOCS_DIR
from backend.query_engine import rag_answer
from backend.audio_service import text_to_audio_base64

app = FastAPI(title="Local Legal Assistant API")

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/ingest_law/")
async def ingest_law(file: UploadFile = File(...)):
    os.makedirs(DOCS_DIR, exist_ok=True)
    path = os.path.join(DOCS_DIR, file.filename)
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    count = process_and_store_one(path, file.filename)
    return {"status": "ok", "indexed_chunks": count}

@app.post("/process_all/")
def process_all_docs():
    total = process_all()
    return {"status": "ok", "total_indexed_chunks": total}

class AnalyzeParams(BaseModel):
    top_k: int = 4
    max_paragraphs: int = 6
    target_lang: str = "en"
    want_audio: bool = False

@app.post("/analyze_document/")
async def analyze_document(file: UploadFile = File(...), top_k: int = Form(4), max_paragraphs: int = Form(6), target_lang: str = Form("en"), want_audio: bool = Form(False)):
    content = await file.read()
    fname = file.filename
    if fname.lower().endswith(".pdf"):
        text = extract_text_from_pdf(content)
    elif fname.lower().endswith(".docx"):
        text = extract_text_from_docx(content)
    else:
        text = extract_text_from_txt(content)

    paragraphs = paragraph_split(text)[:max_paragraphs]
    results = []
    for i, para in enumerate(paragraphs):
        res = rag_answer(para, top_k=top_k)
        results.append({"paragraph_index": i, "paragraph": para, "analysis": res["answer"], "retrieved": res["retrieved"]})

    combined = "\n\n".join([r["analysis"] for r in results])

    response = {"filename": fname, "paragraphs_analyzed": len(results), "results": results}

    # translation via LLM (simple prompt) if target_lang != 'en'
    if target_lang and target_lang != "en":
        from backend.llm_service import generate_text
        trans_prompt = f"Translate the following text into {target_lang} preserving legal meaning:\n\n{combined}"
        translation = generate_text(trans_prompt, max_length=800)
        response["translation"] = translation
        final_text_for_audio = translation
    else:
        final_text_for_audio = combined

    if want_audio:
        try:
            audio_b64 = text_to_audio_base64(final_text_for_audio, lang=target_lang if target_lang else "en")
            response["audio_base64"] = audio_b64
        except Exception as e:
            response["audio_error"] = str(e)

    return response

@app.get("/ask/")
def ask(query: str = Query(...), top_k: int = Query(4), target_lang: str = Query("en"), want_audio: bool = Query(False)):
    res = rag_answer(query, top_k=top_k)
    answer_text = res["answer"]

    final_text = answer_text
    if target_lang and target_lang != "en":
        from backend.llm_service import generate_text
        trans_prompt = f"Translate the following into {target_lang} preserving legal meaning:\n\n{answer_text}"
        translated = generate_text(trans_prompt, max_length=400)
        final_text = translated

    payload = {"answer": final_text, "retrieved": res["retrieved"]}

    if want_audio:
        try:
            payload["audio_base64"] = text_to_audio_base64(final_text, lang=target_lang if target_lang else "en")
        except Exception as e:
            payload["audio_error"] = str(e)

    return payload

