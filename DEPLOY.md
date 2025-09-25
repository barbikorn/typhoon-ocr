# การ Deploy Typhoon OCR ไปยัง RunPod Serverless

## วิธีที่ 1: ใช้ Bash Script (ง่ายที่สุด)

```bash
# ตั้งค่า Docker username
export DOCKER_USERNAME="your-username"

# รัน deploy script
./deploy.sh
```

## วิธีที่ 2: ใช้ Python Script (อัตโนมัติ)

```bash
# รัน Python deploy script
python deploy.py
```

## วิธีที่ 3: ใช้ GitHub Actions (CI/CD)

1. Push โค้ดไปยัง GitHub
2. ตั้งค่า secrets ใน GitHub:
   - `DOCKER_USERNAME`
   - `DOCKER_PASSWORD`
3. GitHub Actions จะ build และ push image อัตโนมัติ

## วิธีที่ 4: Manual Deploy

```bash
# 1. Build image
docker build -t typhoon-ocr .

# 2. Tag image
docker tag typhoon-ocr:latest your-username/typhoon-ocr:latest

# 3. Login to Docker Hub
docker login

# 4. Push image
docker push your-username/typhoon-ocr:latest
```

## วิธีที่ 5: ใช้ Docker Compose (Local Testing)

```bash
# รัน local testing
docker-compose up -d

# ทดสอบ API
curl -X POST "http://localhost:11434/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"input": {"image_b64": "base64_data", "prompt_type": "default"}}'
```

## การตั้งค่า RunPod Endpoint

### Environment Variables:
```
MODEL_NAME=scb10x/typhoon-ocr-7b
OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_NUM_PARALLEL=1
```

### GPU Requirements:
- **Minimum**: RTX 4090 (8GB VRAM)
- **Recommended**: A100 (40GB VRAM)
- **Model Size**: 17GB

### Endpoint Settings:
- **Min Workers**: 0
- **Max Workers**: 5
- **Idle Timeout**: 30 seconds
- **Max Execution Time**: 300 seconds

## การทดสอบ Endpoint

```python
import requests
import base64

def test_endpoint(endpoint_url, image_path):
    with open(image_path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode()
    
    payload = {
        "input": {
            "image_b64": image_b64,
            "prompt_type": "default"
        }
    }
    
    response = requests.post(endpoint_url, json=payload)
    return response.json()

# ทดสอบ
result = test_endpoint("https://api.runpod.ai/v2/your-endpoint-id/runsync", "document.jpg")
print(result)
```

## การ Monitor และ Debug

1. **ดู Logs**: RunPod Console → Endpoints → Logs
2. **ตรวจสอบ Resource Usage**: Monitor GPU memory และ CPU
3. **ดู Execution Time**: ตรวจสอบ performance metrics
4. **Debug Errors**: ใช้ debug logs ที่เพิ่มไว้ในโค้ด

## ข้อควรระวัง

- **Cold Start**: ครั้งแรกจะใช้เวลานานในการโหลด model
- **GPU Memory**: ต้องมี VRAM เพียงพอสำหรับ model
- **Cost**: ตรวจสอบ pricing ของ GPU ที่เลือก
- **Rate Limits**: ตรวจสอบ API rate limits

## การแก้ไขปัญหา

### ปัญหา 400 Bad Request:
- ตรวจสอบ model ถูกโหลดหรือไม่
- ตรวจสอบ payload format
- ดู debug logs

### ปัญหา Timeout:
- เพิ่ม Max Execution Time
- ตรวจสอบ GPU performance
- ลดขนาดรูปภาพ

### ปัญหา Memory:
- ใช้ GPU ที่มี VRAM เพียงพอ
- ลด OLLAMA_NUM_PARALLEL
- ใช้ model ที่เล็กกว่า
