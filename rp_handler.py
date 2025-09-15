import os, io, base64, json, time, requests
from PIL import Image
import runpod

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
MODEL_NAME  = os.environ.get("MODEL_NAME", "scb10x/typhoon-ocr-7b")

def _load_image(inp):
    if "image_b64" in inp:
        return base64.b64decode(inp["image_b64"])
    if "image_url" in inp:
        r = requests.get(inp["image_url"], timeout=30)
        r.raise_for_status()
        return r.content
    raise ValueError("Provide image_b64 or image_url")

def _to_png(img_bytes):
    im = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    buf = io.BytesIO(); im.save(buf, format="PNG")
    return buf.getvalue()

def _ollama_chat_vision(png_bytes, prompt):
    b64img = base64.b64encode(png_bytes).decode("utf-8")
    payload = {
        "model": MODEL_NAME,
        "stream": False,
        "messages": [{
            "role":"user",
            "content":[
                {"type":"text","text": prompt},
                {"type":"image","image": b64img}
            ]
        }],
        "options": {"temperature": 0}
    }
    r = requests.post(f"{OLLAMA_HOST}/api/chat", json=payload, timeout=900)
    r.raise_for_status()
    return r.json()

def handler(job):
    t0 = time.time()
    try:
        inp = job.get("input") or {}
        prompt = inp.get("prompt") or "Extract Thai/English text with structure (headings, lists, tables). Return natural text."
        png = _to_png(_load_image(inp))
        res = _ollama_chat_vision(png, prompt)
        text = res.get("message", {}).get("content", "")
        return {
            "ok": True,
            "model": MODEL_NAME,
            "elapsed_sec": round(time.time()-t0, 3),
            "output_text": text
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

runpod.serverless.start({"handler": handler})
 