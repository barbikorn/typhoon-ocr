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

def _get_typhoon_prompt(prompt_type="default", base_text=""):
    """Get the specific prompt required by Typhoon OCR model"""
    PROMPTS_SYS = {
        "default": lambda base_text: (f"Below is an image of a document page along with its dimensions. "
            f"Simply return the markdown representation of this document, presenting tables in markdown format as they naturally appear.\n"
            f"If the document contains images, use a placeholder like dummy.png for each image.\n"
            f"Your final output must be in JSON format with a single key `natural_text` containing the response.\n"
            f"RAW_TEXT_START\n{base_text}\nRAW_TEXT_END"),
        "structure": lambda base_text: (
            f"Below is an image of a document page, along with its dimensions and possibly some raw textual content previously extracted from it. "
            f"Note that the text extraction may be incomplete or partially missing. Carefully consider both the layout and any available text to reconstruct the document accurately.\n"
            f"Your task is to return the markdown representation of this document, presenting tables in HTML format as they naturally appear.\n"
            f"If the document contains images or figures, analyze them and include the tag <figure>IMAGE_ANALYSIS</figure> in the appropriate location.\n"
            f"Your final output must be in JSON format with a single key `natural_text` containing the response.\n"
            f"RAW_TEXT_START\n{base_text}\nRAW_TEXT_END"
        ),
    }
    return PROMPTS_SYS.get(prompt_type, PROMPTS_SYS["default"])(base_text)

def _ollama_chat_vision(png_bytes, prompt_type="default", base_text=""):
    """Call Typhoon OCR model with proper parameters"""
    b64img = base64.b64encode(png_bytes).decode("utf-8")
    typhoon_prompt = _get_typhoon_prompt(prompt_type, base_text)
    
    payload = {
        "model": MODEL_NAME,
        "stream": False,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": typhoon_prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64img}"}}
            ]
        }],
        "options": {
            "temperature": 0.1,
            "top_p": 0.6,
            "repetition_penalty": 1.2
        }
    }
    
    # Add retry logic with shorter timeout for serverless
    for attempt in range(3):
        try:
            r = requests.post(f"{OLLAMA_HOST}/api/chat", json=payload, timeout=300)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.Timeout:
            print(f"Attempt {attempt + 1} timed out after 300 seconds")
            if attempt == 2:
                raise Exception("Ollama request timed out after 3 attempts")
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt == 2:  # Last attempt
                raise
            time.sleep(2)  # Wait before retry

def handler(job):
    t0 = time.time()
    try:
        inp = job.get("input") or {}
        prompt_type = inp.get("prompt_type", "default")  # "default" or "structure"
        base_text = inp.get("base_text", "")  # Optional base text for structure mode
        pdf_path = inp.get("pdf_path", "")  # Optional PDF path for get_anchor_text
        
        # Check if Ollama is ready with better error handling
        try:
            health_check = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=10)
            health_check.raise_for_status()
        except requests.exceptions.RequestException as e:
            return {"ok": False, "error": f"Ollama service not ready: {str(e)}"}
        
        # Load and process image
        png = _to_png(_load_image(inp))
        
        # Extract base_text from PDF metadata if pdf_path is provided and base_text is empty
        if pdf_path and not base_text:
            try:
                # For now, we'll use empty base_text since typhoon-ocr package is not available
                # In production, you would need to implement PDF text extraction
                base_text = ""
                print(f"PDF path provided but base_text extraction not implemented: {pdf_path}")
            except Exception as e:
                print(f"Warning: Could not extract base_text from PDF: {e}")
                base_text = ""
        
        # Call Typhoon OCR model
        res = _ollama_chat_vision(png, prompt_type, base_text)
        response_content = res.get("message", {}).get("content", "")
        
        # Try to parse JSON response from Typhoon OCR
        try:
            parsed_response = json.loads(response_content)
            output_text = parsed_response.get("natural_text", response_content)
        except json.JSONDecodeError:
            # If not JSON, use raw content
            output_text = response_content
        
        return {
            "ok": True,
            "model": MODEL_NAME,
            "elapsed_sec": round(time.time()-t0, 3),
            "output_text": output_text,
            "prompt_type": prompt_type,
            "base_text_length": len(base_text)
        }
    except Exception as e:
        print(f"Handler error: {str(e)}")
        return {"ok": False, "error": str(e)}

runpod.serverless.start({"handler": handler})
 