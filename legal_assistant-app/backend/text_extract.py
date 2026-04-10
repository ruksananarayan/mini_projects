# backend/text_extract.py
import io, re
from PyPDF2 import PdfReader
from docx import Document

def extract_text_from_pdf(file_bytes: bytes):
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        pages = []
        for i, p in enumerate(reader.pages):
            txt = p.extract_text() or ""
            pages.append(f"[page:{i+1}]\n{txt}")
        return "\n\n".join(pages)
    except Exception as e:
        print("PDF extract error:", e)
        return ""

def extract_text_from_docx(file_bytes: bytes):
    try:
        doc = Document(io.BytesIO(file_bytes))
        return "\n".join([p.text for p in doc.paragraphs])
    except Exception as e:
        print("DOCX extract error:", e)
        return ""

def extract_text_from_txt(file_bytes: bytes):
    try:
        return file_bytes.decode("utf-8", errors="ignore")
    except Exception:
        return ""

def chunk_text(text, chunk_size=1000, overlap=200):
    text = re.sub(r"\s+", " ", text).strip()
    chunks = []
    i = 0
    while i < len(text):
        chunk = text[i:i+chunk_size]
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks

def paragraph_split(text, min_len=80):
    paras = [p.strip() for p in text.split("\n\n") if len(p.strip()) >= min_len]
    if len(paras) == 0:
        parts = text.split(". ")
        paras = [p.strip() + "." for p in parts if len(p.strip()) >= min_len]
    return paras
