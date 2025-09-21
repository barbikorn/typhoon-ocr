# Typhoon OCR - RunPod Serverless

OCR service สำหรับการสกัดข้อความไทย/อังกฤษจากเอกสาร โดยใช้ Ollama และ Typhoon OCR model

## คุณสมบัติ

- สกัดข้อความไทยและอังกฤษจากเอกสาร
- รองรับการส่งรูปภาพผ่าน base64 หรือ URL
- ใช้ Typhoon OCR model ที่ออกแบบมาสำหรับเอกสารไทยและอังกฤษ
- รองรับการรันบน RunPod Serverless
- รองรับทั้ง default และ structure mode

## Environment Variables

- `MODEL_NAME`: ชื่อ model ที่จะใช้ (default: `scb10x/typhoon-ocr-7b`)
- `OLLAMA_HOST`: URL ของ Ollama server (default: `http://127.0.0.1:11434`)
- `OLLAMA_NUM_PARALLEL`: จำนวน parallel requests (default: `1`)

## การใช้งาน

### Input Format

#### Default Mode (สำหรับเอกสารทั่วไป)
```json
{
  "input": {
    "image_b64": "base64_encoded_image_data",
    "prompt_type": "default"
  }
}
```

#### Structure Mode (สำหรับเอกสารที่มีโครงสร้างซับซ้อน)
```json
{
  "input": {
    "image_b64": "base64_encoded_image_data",
    "prompt_type": "structure",
    "base_text": "optional_base_text_from_pdf_metadata"
  }
}
```

#### ใช้ URL แทน base64
```json
{
  "input": {
    "image_url": "https://example.com/document.jpg",
    "prompt_type": "default"
  }
}
```

### Output Format

```json
{
  "ok": true,
  "model": "scb10x/typhoon-ocr-7b",
  "elapsed_sec": 2.345,
  "output_text": "ข้อความที่สกัดได้จากเอกสารในรูปแบบ markdown",
  "prompt_type": "default"
}
```

### Prompt Types

- **default**: สำหรับเอกสารทั่วไป จะคืนค่าเป็น markdown format
- **structure**: สำหรับเอกสารที่มีโครงสร้างซับซ้อน จะคืนค่าเป็น HTML format สำหรับตาราง

## การ Deploy บน RunPod

1. สร้าง Docker image:
```bash
docker build -t typhoon-ocr .
```

2. Push ไปยัง Docker registry
3. สร้าง Serverless endpoint บน RunPod
4. ตั้งค่า environment variables ตามต้องการ

## ข้อกำหนดระบบ

- Python 3.11+
- Ollama
- RAM: อย่างน้อย 8GB (สำหรับ Typhoon OCR 7B model)
- GPU: แนะนำใช้ GPU สำหรับประสิทธิภาพที่ดี
- Model Size: 17GB (Typhoon OCR 7B)

## Generation Parameters

Typhoon OCR model ใช้ parameters ดังนี้:
- `temperature`: 0.1 (ไม่แนะนำให้ใช้สูงกว่า 0.1)
- `top_p`: 0.6
- `repetition_penalty`: 1.2

## หมายเหตุสำคัญ

- Typhoon OCR model ต้องใช้ prompt ที่เฉพาะเจาะจงเท่านั้น
- Model นี้ไม่มี guardrails หรือ VQA capability
- อาจเกิด hallucination ได้บ้าง ควรตรวจสอบผลลัพธ์ก่อนใช้งาน
- สำหรับ macOS หากได้ผลลัพธ์ที่ไม่ถูกต้อง ให้ตั้งค่า `num_gpu` เป็น 0

## การใช้งาน Typhoon OCR Package

หากต้องการใช้ typhoon-ocr package โดยตรง:

```python
from typhoon_ocr import ocr_document

markdown = ocr_document(
    "test.png", 
    base_url="http://localhost:11434/v1", 
    api_key="ollama", 
    model='scb10x/typhoon-ocr-7b'
)
print(markdown)
```
