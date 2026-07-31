import os
import requests

api_key = "sk-ht2JTSzdhXVfCDlQQnrqPV5dHADV43vr"
url = "https://api.sensenova.cn/v1/models"
headers = {
    "Authorization": f"Bearer {api_key}"
}
response = requests.get(url, headers=headers)
print("Status:", response.status_code)
try:
    print(response.json())
except Exception as e:
    print("Response text:", response.text)
