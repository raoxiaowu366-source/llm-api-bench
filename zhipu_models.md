# 智谱 AI 模型接入与代码范例

> [!NOTE]
> ⚠️ **重要提示**：所有模型的核心能力参数（如上下文限制、是否支持视觉、工具调用等），已统一迁移至全局速查表 **[ALL_MODELS.md](file:///d:/api/ALL_MODELS.md)**。
> 本文档专门用于记录智谱 API 在不同模态下的**具体 Python 代码调用范例**。

## 1. 代码接入实战范例

根据不同模型的支持模态，必须采用对应的请求 Payload 结构。

### 场景一：带工具调用的纯文本模型 (如 `GLM-4.7-Flash`)
**适用模型**：`GLM-4.7-Flash`, `GLM-4-Flash-250414`
```python
payload = {
    "model": "GLM-4.7-Flash",
    "messages": [{"role": "user", "content": "帮我查一下北京天气"}],
    "tools": [{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的天气",
            "parameters": {
                "type": "object", 
                "properties": {"city": {"type": "string"}}, 
                "required": ["city"]
            }
        }
    }]
}
```

### 场景二：视觉与深度思考模型 (如 `GLM-4.1V-Thinking-Flash`)
**适用模型**：`GLM-4.1V-Thinking-Flash`, `GLM-4.6V-Flash`, `GLM-4V-Flash`
*注意：传递图片必须在 content 数组中使用 `image_url` 结构。*
```python
payload = {
    "model": "GLM-4.1V-Thinking-Flash",
    "messages": [
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": "https://example.com/chart.png"}},
                {"type": "text", "text": "请仔细分析这张图表，推理出增长最快的类目。"}
            ]
        }
    ]
}
```
*响应特点*：对于 Thinking 模型，返回的 `choices[0].message` 中可能包含额外推理信息或过程输出。

### 场景三：文生图任务 (CogView)
**适用模型**：`CogView-3-Flash`
*支持多分辨率：1024x1024、768x1344、864x1152、1344x768、1152x864、1440x720、720x1440 等*
```python
# 注意：接口端点需改为 /images/generations
payload = {
    "model": "cogview-3-flash",
    "prompt": "一只戴着墨镜在赛博朋克城市骑摩托的猫，超高清，虚幻引擎5"
}
```

### 场景四：文/图生视频任务 (CogVideoX)
**适用模型**：`CogVideoX-Flash`
```python
# 注意：接口端点需改为 /videos/generations (此为异步接口)
payload = {
    "model": "cogvideox-flash",
    "prompt": "镜头穿过一片发光的紫色森林，跟随一只飞舞的机械蝴蝶",
    "image_url": "https://example.com/start_frame.png" # 可选，图生视频起点
}
```
*响应特点*：返回一个 `id`，需使用该任务 ID 轮询查询视频生成进度。

---

## 3. 注意事项
1. **免费额度与并发**：这 7 个模型均提供免费调用，但共享同一个极低的并发限制（通常 QPS=1）。在生产或批量测试中，极易遇到 `HTTP 429 该模型当前访问量过大`，**必须**在代码侧实现指数退避重试 (Exponential Backoff)。
2. **多模态参数互斥**：对于不支持 `tools` 的模型（如 `GLM-4.1V-Thinking-Flash`），如果强行传入 tools 数组，API 将会报错拦截。
3. **图片格式要求**：图片通常需为 JPG/PNG 等常见标准格式，对于 SVG、过大图片或非标准格式，可能触发 `HTTP 400 图片输入格式/解析错误`。
