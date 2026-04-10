# backend/audio_service.py
import os
import base64
from gtts import gTTS

TMP_DIR = os.path.join(os.path.dirname(__file__), "tmp")
os.makedirs(TMP_DIR, exist_ok=True)

def text_to_audio_base64(text: str, lang: str = "hi"):
    """
    lang: 2-letter lang code used by gTTS (e.g., 'hi', 'ta', 'te', 'ml', 'en')
    returns base64-encoded mp3 bytes
    """
    filename = os.path.join(TMP_DIR, "answer.mp3")
    tts = gTTS(text=text, lang=lang)
    tts.save(filename)
    with open(filename, "rb") as f:
        b = f.read()
    return base64.b64encode(b).decode("utf-8")
