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
    
    # Try different payload formats for Ollama API
    payload_formats = [
        # Format 1: OpenAI-compatible format
        {
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
        },
        # Format 2: Simplified format
        {
            "model": MODEL_NAME,
            "stream": False,
            "messages": [{
                "role": "user",
                "content": f"{typhoon_prompt}\n\n[IMAGE: data:image/png;base64,{b64img}]"
            }],
            "options": {
                "temperature": 0.1,
                "top_p": 0.6,
                "repetition_penalty": 1.2
            }
        },
        # Format 3: Alternative format
        {
            "model": MODEL_NAME,
            "stream": False,
            "prompt": typhoon_prompt,
            "images": [b64img],
            "options": {
                "temperature": 0.1,
                "top_p": 0.6,
                "repetition_penalty": 1.2
            }
        }
    ]
    
    # Debug logging
    print(f"DEBUG: Sending request to {OLLAMA_HOST}/api/chat")
    print(f"DEBUG: Model: {MODEL_NAME}")
    print(f"DEBUG: Prompt type: {prompt_type}")
    print(f"DEBUG: Base text length: {len(base_text)}")
    print(f"DEBUG: Image size: {len(png_bytes)} bytes")
    
    # Try different endpoints and payload formats
    endpoints = [
        f"{OLLAMA_HOST}/api/chat",
        f"{OLLAMA_HOST}/api/generate",
        f"{OLLAMA_HOST}/v1/chat/completions"
    ]
    
    for endpoint in endpoints:
        print(f"DEBUG: Trying endpoint: {endpoint}")
        
        # Try different payload formats
        for format_idx, payload in enumerate(payload_formats):
            print(f"DEBUG: Trying payload format {format_idx + 1} on endpoint {endpoint}")
            print(f"DEBUG: Payload keys: {list(payload.keys())}")
            
            # Add retry logic with shorter timeout for serverless
            for attempt in range(3):
                try:
                    print(f"DEBUG: Attempt {attempt + 1} - Sending request...")
                    r = requests.post(endpoint, json=payload, timeout=300)
                    print(f"DEBUG: Response status: {r.status_code}")
                    print(f"DEBUG: Response headers: {dict(r.headers)}")
                    
                    if r.status_code == 200:
                        print(f"DEBUG: Success with endpoint {endpoint} and payload format {format_idx + 1}")
                        return r.json()
                    else:
                        print(f"DEBUG: Error response body: {r.text}")
                        if attempt == 2:  # Last attempt for this format
                            continue  # Try next format
                        
                except requests.exceptions.Timeout:
                    print(f"Attempt {attempt + 1} timed out after 300 seconds")
                    if attempt == 2:
                        continue  # Try next format
                except requests.exceptions.RequestException as e:
                    print(f"Attempt {attempt + 1} failed: {e}")
                    if attempt == 2:  # Last attempt for this format
                        continue  # Try next format
                    time.sleep(2)  # Wait before retry
    
    # If all formats fail, try to get more information about the error
    print("DEBUG: All payload formats and endpoints failed")
    
    # Try to get more information about the API
    try:
        info_response = requests.get(f"{OLLAMA_HOST}/api/version", timeout=10)
        if info_response.status_code == 200:
            print(f"DEBUG: Ollama version info: {info_response.json()}")
    except Exception as e:
        print(f"DEBUG: Could not get Ollama version info: {e}")
    
    raise Exception("All payload formats and endpoints failed for Ollama API. Check if the model supports vision capabilities.")

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
            
            # Check if model is available
            models_data = health_check.json()
            available_models = [model.get("name", "") for model in models_data.get("models", [])]
            print(f"DEBUG: Available models: {available_models}")
            
            if MODEL_NAME not in available_models:
                return {"ok": False, "error": f"Model {MODEL_NAME} not found. Available models: {available_models}"}
            
            # Check model details and capabilities
            model_details = None
            for model in models_data.get("models", []):
                if model.get("name") == MODEL_NAME:
                    model_details = model
                    break
            
            if model_details:
                print(f"DEBUG: Model details: {model_details}")
                # Check if model supports vision
                if "vision" not in str(model_details).lower() and "multimodal" not in str(model_details).lower():
                    print(f"WARNING: Model {MODEL_NAME} may not support vision/multimodal capabilities")
                    
                # Check model size and parameters
                model_size = model_details.get("size", 0)
                print(f"DEBUG: Model size: {model_size} bytes")
                
                # Check if model is loaded
                if model_details.get("modified_at"):
                    print(f"DEBUG: Model was last modified: {model_details.get('modified_at')}")
                else:
                    print(f"WARNING: Model {MODEL_NAME} may not be properly loaded")
                
        except requests.exceptions.RequestException as e:
            return {"ok": False, "error": f"Ollama service not ready: {str(e)}"}
        
        # Load and process image
        try:
            png = _to_png(_load_image(inp))
            print(f"DEBUG: Image processed successfully, size: {len(png)} bytes")
        except Exception as e:
            return {"ok": False, "error": f"Failed to process image: {str(e)}"}
        
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
        try:
            res = _ollama_chat_vision(png, prompt_type, base_text)
            print(f"DEBUG: Ollama response received: {type(res)}")
            response_content = res.get("message", {}).get("content", "")
            print(f"DEBUG: Response content length: {len(response_content)}")
        except Exception as e:
            return {"ok": False, "error": f"Failed to call Ollama API: {str(e)}"}
        
        # Try to parse JSON response from Typhoon OCR
        try:
            parsed_response = json.loads(response_content)
            output_text = parsed_response.get("natural_text", response_content)
            print(f"DEBUG: Parsed JSON response successfully")
        except json.JSONDecodeError:
            # If not JSON, use raw content
            output_text = response_content
            print(f"DEBUG: Using raw response content (not JSON)")
        
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
 