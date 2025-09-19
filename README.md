# Typhoon OCR - RunPod Serverless

OCR service สำหรับการสกัดข้อความไทย/อังกฤษจากรูปภาพ โดยใช้ Ollama และ Typhoon OCR model

## คุณสมบัติ

- สกัดข้อความไทยและอังกฤษจากรูปภาพ
- รองรับการส่งรูปภาพผ่าน base64 หรือ URL
- ใช้ Ollama และ Typhoon OCR model
- รองรับการรันบน RunPod Serverless

## Environment Variables

- `MODEL_NAME`: ชื่อ model ที่จะใช้ (default: `scb10x/typhoon-ocr-7b`)
- `OLLAMA_HOST`: URL ของ Ollama server (default: `http://127.0.0.1:11434`)
- `OLLAMA_NUM_PARALLEL`: จำนวน parallel requests (default: `1`)

## การใช้งาน

### Input Format

```json
{
  "input": {
    "image_b64": "base64_encoded_image_data",
    "prompt": "Extract Thai/English text with structure (headings, lists, tables). Return natural text."
  }
}
```

หรือ

```json
{
  "input": {
    "image_url": "https://example.com/image.jpg",
    "prompt": "Extract Thai/English text with structure (headings, lists, tables). Return natural text."
  }
}
```

### Output Format

```json
{
  "ok": true,
  "model": "scb10x/typhoon-ocr-7b",
  "elapsed_sec": 2.345,
  "output_text": "ข้อความที่สกัดได้จากรูปภาพ"
}
```

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
