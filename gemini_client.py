import os, json, re
from dotenv import load_dotenv
load_dotenv()

TEXT_MODEL = os.getenv("GEMINI_TEXT_MODEL", "gemini-2.5-flash")
IMAGE_MODEL = os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")

_CLIENT = None  # client unique, gardé en vie (sinon il est fermé avant l'envoi de la requête)


def _client():
    global _CLIENT
    if _CLIENT is None:
        from google import genai
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise RuntimeError("GEMINI_API_KEY manquante (voir .env)")
        _CLIENT = genai.Client(api_key=key)
    return _CLIENT


def generer_json(prompt: str) -> dict:
    from google.genai import types
    rep = _client().models.generate_content(
        model=TEXT_MODEL, contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.9))
    txt = re.sub(r"^```json|```$", "", rep.text.strip(), flags=re.M).strip()
    return json.loads(txt)


def generer_image(prompt: str) -> bytes | None:
    rep = _client().models.generate_content(model=IMAGE_MODEL, contents=prompt)
    for cand in rep.candidates or []:
        for part in cand.content.parts:
            if getattr(part, "inline_data", None) and part.inline_data.data:
                return part.inline_data.data
    return None
