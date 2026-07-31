import os
import time
import requests
import json

def get_api_key():
    from dotenv import load_dotenv
    load_dotenv()
    return os.environ.get("SENSENOVA_API_KEY")

API_KEY = get_api_key()
BASE_URL = "https://token.sensenova.cn/v1"

def test_chat():
    print("--- 1. Testing sensenova-6.7-flash-lite Chat ---")
    url = f"{BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "sensenova-6.7-flash-lite",
        "messages": [
            { "role": "system", "content": "你是一个有用的助手。" },
            { "role": "user", "content": "你好，请回复'连通正常'。" }
        ]
    }
    try:
        start_time = time.time()
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        elapsed = time.time() - start_time
        print(f"Status: {response.status_code}, Time: {elapsed:.2f}s")
        if response.status_code == 200:
            print("Response:", response.json()["choices"][0]["message"]["content"])
        else:
            print("Error:", response.text)
    except Exception as e:
        print(f"Error: {e}")

def test_deepseek_reasoning():
    print("\n--- 2. Testing deepseek-v4-flash Reasoning ---")
    url = f"{BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-v4-flash",
        "messages": [
            { "role": "user", "content": "如果我有一个苹果，吃了一半，还剩多少？" }
        ],
        "reasoning_effort": "high"
    }
    try:
        start_time = time.time()
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        elapsed = time.time() - start_time
        print(f"Status: {response.status_code}, Time: {elapsed:.2f}s")
        if response.status_code == 200:
            data = response.json()
            reasoning = data["choices"][0]["message"].get("reasoning_content", "None")
            content = data["choices"][0]["message"].get("content", "")
            print(f"Reasoning:\n{reasoning}\n")
            print(f"Content:\n{content}")
        else:
            print("Error:", response.text)
    except Exception as e:
        print(f"Error: {e}")

def test_vision():
    print("\n--- 3. Testing sensenova-6.7-flash-lite Vision ---")
    url = f"{BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "sensenova-6.7-flash-lite",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "图片里是什么logo？"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "https://www.sensenova.cn/images/logo.png"
                        }
                    }
                ]
            }
        ]
    }
    try:
        start_time = time.time()
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        elapsed = time.time() - start_time
        print(f"Status: {response.status_code}, Time: {elapsed:.2f}s")
        if response.status_code == 200:
            print("Response:", response.json()["choices"][0]["message"]["content"])
        else:
            print("Error:", response.text)
    except Exception as e:
        print(f"Error: {e}")
        
def test_image_generation():
    print("\n--- 4. Testing sensenova-u1-fast Image Generation ---")
    url = f"{BASE_URL}/images/generations"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "sensenova-u1-fast",
        "prompt": "一只可爱的卡通小猫，粉色背景，高画质",
        "size": "2048x2048",
        "n": 1
    }
    try:
        start_time = time.time()
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        elapsed = time.time() - start_time
        print(f"Status: {response.status_code}, Time: {elapsed:.2f}s")
        if response.status_code == 200:
            print("Response:", response.json())
        else:
            print("Error:", response.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if not API_KEY:
        print("SENSENOVA_API_KEY is not set.")
        exit(1)
        
    print(f"Using API KEY: {API_KEY[:6]}...{API_KEY[-4:]}\n")
    
    test_chat()
    time.sleep(3) # Simple backoff
    test_deepseek_reasoning()
    time.sleep(3)
    test_vision()
    time.sleep(3)
    test_image_generation()
