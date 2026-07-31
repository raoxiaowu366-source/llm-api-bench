# SenseNova 商汤日日新接入说明与代码范例

> [!NOTE]
> ⚠️ **重要提示**：所有模型的核心能力参数（如上下文限制、是否支持视觉、工具调用等），已统一迁移至全局速查表 **[ALL_MODELS.md](file:///d:/api/ALL_MODELS.md)**。
> 本文档专门用于记录商汤 API 的特殊鉴权方式及**具体 Python 代码调用范例**。

> [!IMPORTANT]
> - **API 鉴权协议**：通过标准的 OpenAI HTTP Bearer 协议进行鉴权 `Authorization: Bearer $SENSENOVA_API_KEY`
> - **请求地址 (Base URL)**： `https://token.sensenova.cn/v1`

## 1. 深度功能专项支持说明

### 2.1 图像识别与多模态理解
- **支持模型**：`sensenova-6.7-flash-lite`
- **使用方式**：在 `messages.content` 数组中使用 `image_url` 传入图片链接。

### 2.2 工具调用 (Function Calling)
- **支持模型**：`sensenova-6.7-flash-lite`，`deepseek-v4-flash`
- **使用方式**：支持标准的 `tools` 字段列表，并在响应中正确返回 `tool_calls`。

### 2.3 深度思考 (Reasoning)
- **支持模型**：`deepseek-v4-flash`
- **使用方式**：内置思考模式。可在请求体中设置 `reasoning_effort` 为 `"low"` / `"medium"` / `"high"` / `"none"`（设为 none 即关闭）。思考过程会在响应结果中的 `reasoning_content` 字段返回。

### 2.4 结构化 JSON 输出
- **支持模型**：`deepseek-v4-flash`
- **使用方式**：在请求体中设置 `"response_format": { "type": "json_object" }` 开启。

### 2.5 文本生图 (Infographics)
- **支持模型**：`sensenova-u1-fast`
- **专属端点**：**必须调用 `/images/generations` 端点**，而不是 chat completions。

---

## 3. 标准化 Python 测试用例

以下测试代码提供了不同模态和高级特性的调用方式。

### 3.1 基础文本对话测试
```python
import os
import requests

API_KEY = os.environ.get("SENSENOVA_API_KEY")
url = "https://token.sensenova.cn/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": "sensenova-6.7-flash-lite",
    "messages": [
        { "role": "system", "content": "你是一个有用的助手。" },
        { "role": "user", "content": "介绍一下商汤科技。" }
    ]
}

response = requests.post(url, headers=headers, json=payload)
print(response.json())
```

### 3.2 深度思考 (Reasoning) 模型测试
```python
payload = {
    "model": "deepseek-v4-flash",
    "messages": [
        { "role": "user", "content": "9.11 和 9.8 哪个更大？" }
    ],
    "reasoning_effort": "high"
}

response = requests.post(url, headers=headers, json=payload)
data = response.json()
# 提取思考内容
reasoning = data["choices"][0]["message"].get("reasoning_content", "")
print("思考过程：", reasoning)
```

### 3.3 视觉理解 (Vision) 模型测试
```python
payload = {
    "model": "sensenova-6.7-flash-lite",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "图片里面有什么？"
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
response = requests.post(url, headers=headers, json=payload)
print(response.json())
```

### 3.4 专有生图端点 (图像生成)
> [!CAUTION]
> 必须使用 `/images/generations` 端点

```python
img_url = "https://token.sensenova.cn/v1/images/generations"
payload = {
    "model": "sensenova-u1-fast",
    "prompt": "生成一张可爱的猫咪插画",
    "size": "2752x1536",
    "n": 1
}
response = requests.post(img_url, headers=headers, json=payload)
print(response.json())
```
