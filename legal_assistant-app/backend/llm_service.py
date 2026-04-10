# backend/llm_service.py
import torch
from transformers import pipeline

GEN_MODEL = "google/flan-t5-small"

device = 0 if torch.cuda.is_available() else -1
generator = pipeline("text2text-generation", model=GEN_MODEL, device=device)

def generate_text(prompt: str, max_length: int = 256) -> str:
    out = generator(prompt, max_length=max_length, do_sample=False)
    return out[0]["generated_text"]
