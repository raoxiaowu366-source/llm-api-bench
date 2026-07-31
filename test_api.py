import os
import sys
import json
import time
import urllib.request
import urllib.error

# 尝试手动解析 .env 文件（无需依赖第三方包即可零依赖运行）
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

def save_records(records, json_path="api_records.json", md_path="api_list.md"):
    # 写入 JSON 数据文件
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    # 生成 Markdown 易读报告
    md_content = "# 大模型 API 可用性与测试记录报告\n\n"
    md_content += f"> **最后更新时间**：{time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    md_content += "| 厂商/标识 | 状态 | 测试模型 | 响应延迟 (秒) | Base URL | 测试时间 |\n"
    md_content += "| :--- | :---: | :--- | :---: | :--- | :--- |\n"

    for r in records:
        status_icon = "✅ 可用" if r["status"] == "SUCCESS" else f"❌ 失败 ({r.get('error_code', 'ERR')})"
        latency = f"{r['latency']:.2f}s" if r["latency"] is not None else "N/A"
        md_content += f"| {r['provider']} | {status_icon} | `{r['model']}` | {latency} | `{r['base_url']}` | {r['timestamp']} |\n"

    md_content += "\n\n## 接口回复样例\n\n"
    for r in records:
        if r["status"] == "SUCCESS":
            md_content += f"### {r['provider']} (`{r['model']}`)\n"
            md_content += f"- **延迟**: {r['latency']:.2f}s\n"
            md_content += f"- **回复内容**: {r.get('response_text', '')}\n\n"

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

def test_api_endpoint(provider, api_key, base_url, model):
    if not base_url.endswith("/"):
        base_url += "/"
    
    # 默认针对 openai 兼容标准 /chat/completions 接口
    if not base_url.endswith("chat/completions"):
        if base_url.endswith("v1/"):
            url = base_url + "chat/completions"
        else:
            url = base_url.rstrip("/") + "/chat/completions"
    else:
        url = base_url

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "APITester/1.0"
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Hi"}],
        "max_tokens": 15
    }

    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")

    start_time = time.time()
    result = {
        "provider": provider,
        "base_url": base_url,
        "model": model,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "FAILED",
        "latency": None,
        "response_text": "",
        "error_code": None
    }

    print(f"正在测试 [{provider}] (模型: {model})... ", end="", flush=True)

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            elapsed = time.time() - start_time
            body = resp.read().decode("utf-8")
            res_json = json.loads(body)
            
            # 提取回复内容
            choices = res_json.get("choices", [])
            content = ""
            if choices and len(choices) > 0:
                message = choices[0].get("message", {})
                content = message.get("content", "").strip()

            result["status"] = "SUCCESS"
            result["latency"] = elapsed
            result["response_text"] = content
            print(f"✅ 成功! 延迟: {elapsed:.2f}s | 响应: {content[:30]!r}")
            return result

    except urllib.error.HTTPError as e:
        elapsed = time.time() - start_time
        err_msg = e.read().decode("utf-8", errors="ignore")
        result["error_code"] = e.code
        result["response_text"] = err_msg[:100]
        print(f"❌ 失败! HTTP 状态码: {e.code}")
        return result
    except Exception as e:
        result["error_code"] = "EXCEPTION"
        result["response_text"] = str(e)
        print(f"❌ 失败! 错误信息: {e}")
        return result

def main():
    print("=" * 60)
    print("      大模型 API 可用性与延迟检测工具")
    print("=" * 60)

    env_config = load_dotenv_custom(".env")

    # 预定义支持的厂商列表及其官方默认地址和模型
    providers = [
        {"name": "DeepSeek", "prefix": "DEEPSEEK", "default_url": "https://api.deepseek.com", "default_model": "deepseek-chat"},
        {"name": "智谱AI (Zhipu)", "prefix": "ZHIPU", "default_url": "https://open.bigmodel.cn/api/paas/v4", "default_model": "glm-4-flash"},
        {"name": "月之暗面 (Moonshot)", "prefix": "MOONSHOT", "default_url": "https://api.moonshot.cn/v1", "default_model": "moonshot-v1-8k"},
        {"name": "硅基流动 (SiliconFlow)", "prefix": "SILICONFLOW", "default_url": "https://api.siliconflow.cn/v1", "default_model": "Qwen/Qwen2.5-7B-Instruct"},
        {"name": "OpenRouter", "prefix": "OPENROUTER", "default_url": "https://openrouter.ai/api/v1", "default_model": "google/gemini-2.5-flash"},
        {"name": "通义千问 (DashScope)", "prefix": "DASHSCOPE", "default_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "default_model": "qwen-turbo"},
        {"name": "零一万物 (Yi)", "prefix": "YI", "default_url": "https://api.lingyiwanwu.com/v1", "default_model": "yi-spark"},
        {"name": "OpenAI", "prefix": "OPENAI", "default_url": "https://api.openai.com/v1", "default_model": "gpt-4o-mini"},
        {"name": "商汤科技 (SenseNova)", "prefix": "SENSENOVA", "default_url": "https://token.sensenova.cn/v1", "default_model": "sensenova-6.7-flash-lite"},
        {"name": "自定义API", "prefix": "CUSTOM", "default_url": "", "default_model": ""},
    ]

    active_tests = []

    for p in providers:
        prefix = p["prefix"]
        key = env_config.get(f"{prefix}_API_KEY", "").strip()
        if key:
            base_url = env_config.get(f"{prefix}_BASE_URL", "").strip() or p["default_url"]
            model = env_config.get(f"{prefix}_MODEL", "").strip() or p["default_model"]
            active_tests.append({
                "provider": p["name"],
                "key": key,
                "base_url": base_url,
                "model": model
            })

    if not active_tests:
        print("\n[!] 在 .env 文件中未找到任何已填写的 API Key。")
        print("请按以下步骤操作：")
        print(" 1. 复制 .env.template 为 .env")
        print(" 2. 在 .env 中填入您的真实 API Key")
        print(" 3. 重新运行 `python test_api.py` 进行验证\n")
        return

    print(f"\n找到 {len(active_tests)} 个已配置的 API，开始测试...\n")

    results = []
    for test in active_tests:
        res = test_api_endpoint(test["provider"], test["key"], test["base_url"], test["model"])
        results.append(res)

    save_records(results)
    print("\n" + "=" * 60)
    print("测试完成！已保存结果：")
    print(" - 结构化 JSON 记录: api_records.json")
    print(" - Markdown 可视化报告: api_list.md")
    print("=" * 60)

if __name__ == "__main__":
    main()
