import os
import json
import time
import urllib.request
import urllib.error

# 读取 .env 配置
def load_dotenv_custom(dotenv_path=".env"):
    if not os.path.exists(dotenv_path):
        return {}
    config = {}
    with open(dotenv_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                config[key.strip()] = val.strip().strip("'\"")
    return config

def http_post(url, headers, payload):
    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")
    # 遇到 429 频控重试最多 3 次
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8")
                return True, json.loads(body)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 3:
                time.sleep(5) # 429 退避等待时间加长
                continue
            err_msg = e.read().decode("utf-8", errors="ignore")
            return False, f"HTTP {e.code}: {err_msg[:80]}"
        except Exception as e:
            return False, str(e)
    return False, "Max retries exceeded"

def test_model(api_key, model_info):
    name = model_info["name"]
    model_type = model_info["type"]
    print(f"正在测试 [{name}] ({model_info['desc']})... ", end="", flush=True)

    base_url = "https://open.bigmodel.cn/api/paas/v4"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    start_time = time.time()
    result = {
        "model": name,
        "type": model_type,
        "status": "FAILED",
        "latency": None,
        "response": "",
        "error": None
    }

    payload = {"model": name}

    if model_type == "text_tool":
        url = base_url + "/chat/completions"
        payload["messages"] = [{"role": "user", "content": "查一下今天北京天气"}]
        payload["max_tokens"] = 50
        # 添加工具调用测试
        payload["tools"] = [{
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "获取天气",
                "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}
            }
        }]
    elif model_type == "vision":
        url = base_url + "/chat/completions"
        # 传入一张 PNG 测试图片
        test_img_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d9/Node.js_logo.svg/320px-Node.js_logo.svg.png" 
        payload["messages"] = [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": test_img_url}},
                    {"type": "text", "text": "这幅图里有什么文字或图案？用一句话描述。"}
                ]
            }
        ]
        payload["max_tokens"] = 50
    elif model_type == "image_gen":
        url = base_url + "/images/generations"
        payload["prompt"] = "一只可爱的小猫"
    elif model_type == "video_gen":
        url = base_url + "/videos/generations"
        payload["prompt"] = "一只小花猫在草地上快乐跑动"
    else:
        url = base_url + "/chat/completions"
        payload["messages"] = [{"role": "user", "content": "你好"}]

    success, res_data = http_post(url, headers, payload)
    elapsed = time.time() - start_time
    result["latency"] = elapsed

    if success:
        result["status"] = "SUCCESS"
        content = ""
        if model_type in ["text_tool", "vision", "text"]:
            choices = res_data.get("choices", [])
            if choices:
                msg = choices[0].get("message", {})
                content = msg.get("content", "").strip()
                # 提取思考内容或工具调用信息
                if "reasoning_content" in msg and msg["reasoning_content"]:
                    content = f"<think>... </think> {content}"
                elif "tool_calls" in msg and msg["tool_calls"]:
                    content = f"[调用工具: {msg['tool_calls'][0]['function']['name']}]"
        elif model_type == "image_gen":
            data_list = res_data.get("data", [])
            if data_list:
                content = f"图片URL生成成功 ({data_list[0].get('url', '')[:40]}...)"
        elif model_type == "video_gen":
            task_id = res_data.get("id", "")
            content = f"视频异步任务创建成功 (ID: {task_id})"

        result["response"] = content
        print(f"✅ 成功! 耗时: {elapsed:.2f}s | 响应: {content[:35]!r}")
    else:
        result["error"] = res_data
        print(f"❌ 失败! {res_data}")

    return result

def main():
    env_config = load_dotenv_custom(".env")
    api_key = env_config.get("ZHIPU_API_KEY", "").strip()

    if not api_key:
        print("[-] 未在 .env 文件中找到 ZHIPU_API_KEY！")
        return

    print("=" * 70)
    print("      智谱 AI 7 大免费模型深度模态测试 (视觉/工具/思考/音视频)")
    print("=" * 70 + "\n")

    # 7 个免费模型详细配置
    free_models = [
        {"name": "GLM-4.7-Flash", "type": "text_tool", "desc": "纯文本+工具调用"},
        {"name": "GLM-4.6V-Flash", "type": "vision", "desc": "多模态+图片输入"},
        {"name": "GLM-4.1V-Thinking-Flash", "type": "vision", "desc": "多模态+深度思考"},
        {"name": "GLM-4-Flash-250414", "type": "text_tool", "desc": "纯文本+工具调用"},
        {"name": "GLM-4V-Flash", "type": "vision", "desc": "多模态+图片输入"},
        {"name": "CogView-3-Flash", "type": "image_gen", "desc": "文生图模型"},
        {"name": "CogVideoX-Flash", "type": "video_gen", "desc": "视频生成模型"}
    ]

    results = []
    for item in free_models:
        res = test_model(api_key, item)
        results.append(res)
        time.sleep(1.5) # 增加延迟避免 429

    with open("zhipu_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print("全模态深度测试完成！")
    print("=" * 70)

if __name__ == "__main__":
    main()
