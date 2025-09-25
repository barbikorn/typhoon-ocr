#!/usr/bin/env python3
"""
Deploy script for Typhoon OCR to RunPod Serverless
"""

import os
import subprocess
import sys
import json
import requests
from pathlib import Path

class RunPodDeployer:
    def __init__(self, docker_username, image_name="typhoon-ocr", tag="latest"):
        self.docker_username = docker_username
        self.image_name = image_name
        self.tag = tag
        self.full_image_name = f"{docker_username}/{image_name}:{tag}"
        
    def build_image(self):
        """Build Docker image"""
        print("📦 Building Docker image...")
        try:
            subprocess.run(["docker", "build", "-t", f"{self.image_name}:{self.tag}", "."], 
                         check=True, capture_output=True, text=True)
            print("✅ Docker image built successfully!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error building image: {e.stderr}")
            sys.exit(1)
    
    def tag_image(self):
        """Tag image for Docker Hub"""
        print("🏷️  Tagging image...")
        try:
            subprocess.run(["docker", "tag", f"{self.image_name}:{self.tag}", self.full_image_name], 
                         check=True, capture_output=True, text=True)
            print("✅ Image tagged successfully!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error tagging image: {e.stderr}")
            sys.exit(1)
    
    def push_image(self):
        """Push image to Docker Hub"""
        print("⬆️  Pushing image to Docker Hub...")
        try:
            subprocess.run(["docker", "push", self.full_image_name], 
                         check=True, capture_output=True, text=True)
            print("✅ Image pushed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error pushing image: {e.stderr}")
            sys.exit(1)
    
    def create_runpod_endpoint(self, api_key):
        """Create RunPod endpoint (requires API key)"""
        print("🔧 Creating RunPod endpoint...")
        
        endpoint_config = {
            "name": "typhoon-ocr",
            "image": self.full_image_name,
            "gpu_type": "RTX 4090",
            "min_workers": 0,
            "max_workers": 5,
            "idle_timeout": 30,
            "max_execution_time": 300,
            "env": {
                "MODEL_NAME": "scb10x/typhoon-ocr-7b",
                "OLLAMA_HOST": "http://127.0.0.1:11434",
                "OLLAMA_NUM_PARALLEL": "1"
            }
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                "https://api.runpod.ai/v2/serverless/endpoints",
                headers=headers,
                json=endpoint_config
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Endpoint created successfully!")
                print(f"🔗 Endpoint ID: {result.get('id')}")
                print(f"🌐 Endpoint URL: https://api.runpod.ai/v2/{result.get('id')}/runsync")
            else:
                print(f"❌ Error creating endpoint: {response.text}")
                
        except Exception as e:
            print(f"❌ Error creating endpoint: {e}")
    
    def deploy(self, create_endpoint=False, api_key=None):
        """Main deployment process"""
        print("🚀 Starting deployment process...")
        
        # Build and push image
        self.build_image()
        self.tag_image()
        self.push_image()
        
        # Create endpoint if requested
        if create_endpoint and api_key:
            self.create_runpod_endpoint(api_key)
        else:
            print("\n📋 Manual steps:")
            print("1. Go to https://console.runpod.io/")
            print("2. Navigate to Serverless → My Endpoints")
            print("3. Click 'Create Endpoint'")
            print(f"4. Use this image: {self.full_image_name}")
            print("5. Set environment variables:")
            print("   - MODEL_NAME=scb10x/typhoon-ocr-7b")
            print("   - OLLAMA_HOST=http://127.0.0.1:11434")
            print("   - OLLAMA_NUM_PARALLEL=1")
            print("6. Choose GPU: RTX 4090 or A100")
            print("7. Set Max Execution Time: 300 seconds")
        
        print("\n🎉 Deployment complete!")

def main():
    # Get Docker username from environment or prompt
    docker_username = os.getenv("DOCKER_USERNAME")
    if not docker_username:
        docker_username = input("Enter your Docker Hub username: ")
    
    # Initialize deployer
    deployer = RunPodDeployer(docker_username)
    
    # Ask if user wants to create endpoint automatically
    create_endpoint = input("Do you want to create RunPod endpoint automatically? (y/n): ").lower() == 'y'
    
    api_key = None
    if create_endpoint:
        api_key = input("Enter your RunPod API key: ")
    
    # Deploy
    deployer.deploy(create_endpoint, api_key)

if __name__ == "__main__":
    main()
