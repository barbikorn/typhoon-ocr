#!/bin/bash

# Deploy script for Typhoon OCR to RunPod

set -e

# Configuration
DOCKER_USERNAME=${DOCKER_USERNAME:-"your-username"}
IMAGE_NAME="typhoon-ocr"
TAG="latest"
FULL_IMAGE_NAME="${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}"

echo "🚀 Starting deployment process..."

# Step 1: Build Docker image
echo "📦 Building Docker image..."
docker build -t ${IMAGE_NAME}:${TAG} .

# Step 2: Tag image for Docker Hub
echo "🏷️  Tagging image..."
docker tag ${IMAGE_NAME}:${TAG} ${FULL_IMAGE_NAME}

# Step 3: Login to Docker Hub (if not already logged in)
echo "🔐 Logging into Docker Hub..."
docker login

# Step 4: Push image
echo "⬆️  Pushing image to Docker Hub..."
docker push ${FULL_IMAGE_NAME}

# Step 5: Display deployment instructions
echo "✅ Image pushed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Go to https://console.runpod.io/"
echo "2. Navigate to Serverless → My Endpoints"
echo "3. Click 'Create Endpoint'"
echo "4. Use this image: ${FULL_IMAGE_NAME}"
echo "5. Set environment variables:"
echo "   - MODEL_NAME=scb10x/typhoon-ocr-7b"
echo "   - OLLAMA_HOST=http://127.0.0.1:11434"
echo "   - OLLAMA_NUM_PARALLEL=1"
echo "6. Choose GPU: RTX 4090 or A100"
echo "7. Set Max Execution Time: 300 seconds"
echo ""
echo "🎉 Deployment complete!"
