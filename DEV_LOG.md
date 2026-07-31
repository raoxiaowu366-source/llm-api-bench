# 项目开发日志 (DEV_LOG)

## 2026-07-30
### 踩坑与修复：智谱 7 大免费模型能力深度测试
1. **认知修正**：最初仅验证了 API 连通性，忽视了模型的核心特色能力。经用户严厉指正后，重新阅读官方文档，明确了每个模型的**输入模态（图片/文本）**、**思考模式（内置/可配置）**和**工具调用 (Function Calling)** 功能。
2. **测试脚本强化 (`test_zhipu_all.py`)**：
   - 增加针对 `GLM-4.7-Flash`, `GLM-4-Flash-250414` 的 `tools` 字段测试。测试成功，模型能正确返回 `[调用工具: get_weather]`。
   - 增加针对视觉模型 `GLM-4.6V`, `GLM-4.1V-Thinking`, `GLM-4V` 的 `image_url` 测试。
   - 增加 CogView 和 CogVideoX 的特定端点调用 (`/images/generations` 和 `/videos/generations`)。
3. **发现的问题与遗留风险**：
   - **429 访问量过大**：免费版接口并发极低，在循环调用多个模型时，即便增加了 3-5 秒退避重试，`GLM-4.6V-Flash` 等高频访问模型依然大概率抛出 429。建议生产环境调用免费版必须做好异步重试。
   - **400 图片格式/解析错误**：视觉模型在接收部分公开图片 URL（如 Wikimedia PNG/SVG）时抛出 400 错误。推测智谱 API 对传入的图片 URL 有防抓取限制或格式校验极严。**下一步建议**：改用 Base64 直接传图或寻找智谱官方示例图片 URL 进行测试。
4. **文档同步**：
   - 已全面重构 [zhipu_models.md](file:///d:/api/zhipu_models.md)，严格按官方文档整理了 7 个模型的能力矩阵表格，并附带了带工具、带视觉的真实 Python 调用代码片段。


### 商汤科技 (SenseNova) 模型接入与踩坑记录
1. **配置错误**：环境变量 `.env` 中商汤的 API Key 缺少了变量名，导致脚本无法读取，通过重写纠正了 `.env` 文件格式（修正为 `SENSENOVA_API_KEY=...`）。
2. **工具抓取阻碍**：由于动态渲染页面，起初使用普通 HTTP 获取文档失败。后续遇到 `/browser` 智能体因缺少远程调试端口而失败。最终通过 `playwright` 工具成功渲染并抓取了含有完整 `sensenova-6.7-flash-lite`, `deepseek-v4-flash`, `sensenova-u1-fast` 数据的官方动态文档。
3. **多模态特性验证**：
   - **深度思考模式 (Reasoning)**：成功调用 `deepseek-v4-flash` 模型，请求附带 `reasoning_effort: "high"`，能正确从返回结构中提取 `reasoning_content`。
   - **生图能力分离**：必须通过专门的 `/images/generations` 端点请求 `sensenova-u1-fast` 模型（不支持标准的 chat completions，测试成功生成图片并返回临时 URL）。
   - **视觉模型超时问题**：`sensenova-6.7-flash-lite` 视觉模型在向商汤服务器回传图片 URL 时测试中抛出 `HTTPSConnectionPool` 超时错误（Timeout=20s），可能受网络代理或并发请求限制影响。建议生产环境延长超时设置并设置指数退避重试机制。
4. **文档输出**：梳理并输出完整的 [sensenova_models.md](file:///d:/api/sensenova_models.md) 全景能力矩阵以及全模态独立测试脚本 `test_sensenova_all.py`。

## 2026-07-31
### 新功能实现：LMSYS Chatbot Arena 评分自动查询与表格填充
1. **需求定义与数据源选型**：按用户指令，接入 LMSYS Chatbot Arena（lmarena.ai）网页端，实现自动同步全球最新模型竞技场 Elo Rating 积分与 Rank 排名。
2. **抓取与解析方案 (`fetch_arena_scores.py`)**：
   - 解析 Next.js App Router 渲染页面的 JavaScript Payload (`self.__next_f.push`)。
   - 正确从 JSON 链中提取了 446+ 个在线模型的 `modelDisplayName`、`rating` 以及降序推算得到的 `rank`。
3. **模型名称匹配与别名机制**：
   - 建立 `MODEL_NAME_ALIAS_MAP` 字典及精准完全匹配逻辑，废除可能导致混淆的前缀模糊匹配。
   - 成功将 `GLM-4.7-Flash` 精准更正映射到其在 Arena 上的真实模型 `glm-4.7-flash`（**1367.8 分，即 1368 分**），`deepseek-v4-flash` 映射至 (`1435.8 (#99)`)。
4. **三大榜单数据持久化与 Markdown 填充**：
   - 生成 `arena_scores.json`、`benchlm_scores.json` 与 `clawbench_scores.json` 持久化记录。
   - 动态更新 [ALL_MODELS.md](file:///d:/api/ALL_MODELS.md) 跨厂商能力对比总表，成功新增 `OpenClaw 智能体评分 (Rank)` 第 11 列。完美填充商汤 `sensenova-6.7-flash-lite` 的亮眼智能体得分 **`71.59 (#6)`**，并将 `GLM-4.7-Flash` 标注优化为 `N/A (参考主模型 54.58)`。
   - 确立了统一的自动化流水线防漏机制：每次执行 `python fetch_arena_scores.py`，程序将自动穿透三大榜单对表格内所有注册模型进行 100% 全量查分。






