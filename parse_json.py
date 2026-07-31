import json
import re

def extract_text_from_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            html = f.read()
        match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
        if match:
            data = json.loads(match.group(1))
            # Find the actual markdown content in pageProps
            page_props = data.get('props', {}).get('pageProps', {})
            # Typically Mintlify puts content in mdxSource or fallback
            return str(page_props)[:5000]
    except Exception as e:
        return str(e)
    return 'No NEXT_DATA found'

print('--- 4.7 ---')
print(extract_text_from_file(r'C:\Users\admin\.gemini\antigravity\brain\5a4241a4-38a4-495b-9347-0dd80b64b0a4\.system_generated\steps\171\content.md'))
print('--- 4.6V ---')
print(extract_text_from_file(r'C:\Users\admin\.gemini\antigravity\brain\5a4241a4-38a4-495b-9347-0dd80b64b0a4\.system_generated\steps\172\content.md'))
