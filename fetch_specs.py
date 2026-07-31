import urllib.request
import re
import json

def fetch_and_clean(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        html = urllib.request.urlopen(req).read().decode('utf-8')
        
        # In mintlify, content is usually in the page props or next data. 
        # But we can also just strip all tags if next data is not found.
        # Let's search for __NEXT_DATA__
        match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
        if match:
            data = json.loads(match.group(1))
            return str(data)
        
        # fallback: strip tags
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'\s+', ' ', text)
        return text
    except Exception as e:
        return str(e)

content = fetch_and_clean('https://docs.bigmodel.cn/cn/guide/models/free')

models = [
    'GLM-4.7-Flash', 
    'GLM-4.6V-Flash', 
    'GLM-4.1V-Thinking-Flash', 
    'GLM-4-Flash-250414', 
    'GLM-4V-Flash', 
    'CogView-3-Flash', 
    'CogVideoX-Flash'
]

for m in models:
    idx = content.find(m)
    if idx != -1:
        start = max(0, idx - 200)
        end = min(len(content), idx + 800)
        print(f'\n--- {m} ---')
        print(content[start:end])
