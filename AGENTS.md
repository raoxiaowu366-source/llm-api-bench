# AGENTS.md - 大模型 API 测试与记录系统说明

## 项目简介
本项目用于测试各大模型厂商（如 DeepSeek、智谱 AI、月之暗面 Kimi、硅基流动 SiliconFlow、OpenRouter、阿里云通义千问等）申请到的 API Key 可用性，并记录其连通状态、响应延迟、支持模型等信息。

## 部署与 Git 信息
- GitHub 账号：`raoxiaowu366-source`
- 建议仓库名：`llm-api-bench` (或 `api-test`)
- 远程推送命令：`git push -u origin main`

1. **配置管理**：所有敏感 API Key 统一存放在 `.env` 文件中（如 `ZHIPU_API_KEY`、`SENSENOVA_API_KEY` 等），严禁提交到 Git 仓库。
2. **检测脚本 (`test_api.py`)**：
   - 自动解析 `.env` 中的各厂商 API 配置。
   - 使用 OpenAI 兼容的 HTTP 接口标准发送极简测试请求。
   - 测量 HTTP 响应时间（延迟），校验返回内容。
3. **数据记录与导出**：
   - `api_records.json`：持久化存储已验证可用的 API 信息（包含时间戳、延迟、响应样例）。
   - `api_list.md`：生成可读性高的 Markdown 格式 API 可用清单报告。

## 文件规范与敏感信息隔离
- `.env`：本地环境变量文件（包含真实 API Key），被 `.gitignore` 保护。
- `.env.template`：示例模板文件，提供各厂商环境变量命名范例。

## 常用命令
- 运行全量测试：`python test_api.py`
- 自动同步拉取 LMSYS Arena 评分并填表：`python fetch_arena_scores.py`
- 单次测试命令行传入：`python test_api.py --provider deepseek --key <YOUR_KEY>`


## AI 代理工作规范：接入新模型 API 的标准流程 (SOP)
在为本项目添加新厂商（如智谱、商汤、Kimi 等）的模型测试时，AI 代理**必须**严格遵循以下流程，绝不可仅凭旧有知识“盲猜”或仅做最基础的纯文本连通性测试：

1. **精准获取官方文档**：必须亲自阅读该厂商最新的官方文档，提取模型列表。若遇动态网页（如 Mintlify 框架等）导致无法抓取到正文，**必须主动要求用户提供截图**或建议使用 `/browser` 工具，绝不允许捏造或沿用过时参数。
2. **更新全局大模型能力矩阵 (`ALL_MODELS.md`)**：测试前，必须查阅全量资料，并将该新厂商的所有模型能力参数**新增到 [ALL_MODELS.md](file:///d:/api/ALL_MODELS.md) 的统一对比总表中**。必须通过表格精准、无遗漏地记录每个模型的：
   - **输入模态**（必须细化：纯文本 / 图像 / 视频 / 文件等，绝不能遗漏）
   - **工具与思考**（Function Calling 工具调用、Reasoning 深度思考模式）
   - **上下文窗口**（Context Length，如 128K、200K）
   - **并发数量 (QPS)**（必须找到官方限流说明或并发清单并明确填入）
   - **高级特性支持**（如 MCP、结构化 JSON 输出、上下文缓存、网页检索等，见文知意）
3. **编写厂商专属代码范例 (`<vendor>_models.md`)**：在上述全局表格更新后，必须创建一个专门用于记录该厂商独有特性和 Python 调用代码的独立文档。**严禁**在此专属文档内重复维护能力对比表格，以防数据不一致。
4. **编写深度模态测试脚本 (`test_<vendor>_all.py`)**：不能只发简单的“你好”。
   - **视觉模型**：必须传入 `image_url` 进行测试（注意防范 400 格式错误，必要时转 Base64）。
   - **工具模型**：必须传入 `tools` 结构，验证模型是否能正确进入工具调用逻辑。
   - **思考模型**：检查并提取响应内容中的 `<think>` 或 `reasoning_content`。
   - **生图/生视频模型**：必须调用专用的端点（如 `/images/generations`）。
5. **基于并发指标的容错与限流处理**：免费 API 往往存在苛刻的并发限制。脚本必须结合能力矩阵中的**并发数量(QPS)**预设退避策略。对于 QPS=1 的模型，必须在代码中强制实现更严格的锁或指数退避重试（如延迟 3~5 秒甚至更长），优雅处理 HTTP 429 报错。
