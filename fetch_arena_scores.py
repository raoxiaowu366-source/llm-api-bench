"""
fetch_arena_scores.py
自动化从三大权威榜单实时抓取大模型性能数据：
1. LMSYS Chatbot Arena (lmarena.ai)
2. BenchLM.ai (benchlm.ai)
3. OpenClawProBench (suyoumo.github.io/bench)

并将数据持久化保存至 arena_scores.json、benchlm_scores.json、clawbench_scores.json，
同时全量同步填充至 ALL_MODELS.md。
"""

import json
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

# 设置标准输出编码为 UTF-8，防止 Windows 终端 Emoji 或中文字符打印报错
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# 文件路径配置
BASE_DIR = Path(__file__).parent.resolve()
ALL_MODELS_PATH = BASE_DIR / "ALL_MODELS.md"
ARENA_JSON_PATH = BASE_DIR / "arena_scores.json"
BENCHLM_JSON_PATH = BASE_DIR / "benchlm_scores.json"
CLAWBENCH_JSON_PATH = BASE_DIR / "clawbench_scores.json"

# 特定模型 ID 到各榜单显示名称的显式映射表（优先级从左到右）
MODEL_NAME_ALIAS_MAP = {
    "GLM-4.7-Flash": ["glm-4.7-flash"],
    "GLM-4.6V-Flash": ["glm-4.6v-flash"],
    "GLM-4.1V-Thinking-Flash": ["glm-4.1v-thinking-flash", "glm-4.1v-thinking"],
    "GLM-4-Flash-250414": ["glm-4-flash", "glm-4-flash-250414"],
    "GLM-4V-Flash": ["glm-4v-flash"],
    "deepseek-v4-flash": ["deepseek-v4-flash", "deepseek-v4-flash-thinking"],
    "sensenova-6.7-flash-lite": ["sensenova-6.7-flash-lite"],
}

# 针对榜单未单独收录或专用类型的模型提供明确专业标注
MODEL_N_A_EXPLANATIONS = {
    "CogView-3-Flash": "N/A (生图专用 API)",
    "CogVideoX-Flash": "N/A (生视频专用 API)",
    "sensenova-u1-fast": "N/A (信息图生成 API)",
    "GLM-4.6V-Flash": "N/A (视觉特化快照)",
    "GLM-4.1V-Thinking-Flash": "N/A (推理视觉快照)",
    "GLM-4-Flash-250414": "N/A (低延迟文本 API)",
    "GLM-4V-Flash": "N/A (基础视觉 API)",
    "sensenova-6.7-flash-lite": "N/A (专攻智能体榜单)",
    "GLM-4.7-Flash": "N/A (参考主模型 54.58)",
}



def fetch_lmsys_payload() -> str:
    """从 lmarena.ai/leaderboard 获取页面并拼接 Next.js payload 内容"""
    url = "https://lmarena.ai/leaderboard"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    req = urllib.request.Request(url, headers=headers)

    print(f"🌐 正在请求 LMSYS Chatbot Arena 网页: {url} ...")
    with urllib.request.urlopen(req, timeout=20) as resp:
        html = resp.read().decode("utf-8", errors="ignore")

    pushes = re.findall(r'self\.__next_f\.push\(\[1,\s*"(.*?)"\]\)', html, re.DOTALL)
    combined_payload = ""
    for p in pushes:
        try:
            decoded = json.loads('"' + p + '"')
            combined_payload += decoded
        except Exception:
            combined_payload += p

    print(f"✅ 成功获取 LMSYS Arena Payload (共 {len(combined_payload)} 字符)")
    return combined_payload


def parse_arena_ratings(payload: str) -> dict:
    """从 LMSYS Payload 中解析所有模型及其 Rating，并自动计算全局 Rank"""
    ratings_raw = {}
    matches = re.finditer(r'\{[^{}]*"modelDisplayName":"([^"]+)"[^{}]*"rating":([0-9\.]+)[^{}]*\}', payload)

    for m in matches:
        name = m.group(1).strip()
        rating = float(m.group(2))
        if name not in ratings_raw or rating > ratings_raw[name]:
            ratings_raw[name] = rating

    sorted_items = sorted(ratings_raw.items(), key=lambda x: x[1], reverse=True)
    parsed_models = {}
    for rank, (name, rating) in enumerate(sorted_items, 1):
        parsed_models[name.lower()] = {
            "display_name": name,
            "rating": round(rating, 1),
            "rank": rank
        }

    print(f"📊 解析出 {len(parsed_models)} 个 LMSYS Arena 大模型评分数据。")
    return parsed_models


def fetch_and_parse_benchlm() -> dict:
    """从 benchlm.ai 抓取并解析全量模型及其 BenchLM Score 和 Rank"""
    url = "https://benchlm.ai"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    req = urllib.request.Request(url, headers=headers)

    print(f"🌐 正在请求 BenchLM.ai 网页: {url} ...")
    with urllib.request.urlopen(req, timeout=20) as resp:
        html = resp.read().decode("utf-8", errors="ignore")

    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
    if not match:
        print("⚠️ 未能在 BenchLM 页面找到 __NEXT_DATA__")
        return {}

    data = json.loads(match.group(1))
    rows = data.get("props", {}).get("pageProps", {}).get("homepageData", {}).get("leaderboard", {}).get("rows", [])

    parsed_benchlm = {}
    for r in rows:
        if len(r) > 26:
            rank = r[0]
            model_name = str(r[1])
            slug = str(r[2])
            score = None
            for item in [r[26], r[28], r[27]]:
                if isinstance(item, (int, float)) and 0 <= item <= 100:
                    score = round(float(item), 2)
                    break
            
            if score is not None:
                info = {
                    "display_name": model_name,
                    "slug": slug,
                    "score": score,
                    "rank": rank
                }
                parsed_benchlm[slug.lower()] = info
                parsed_benchlm[model_name.lower()] = info

    print(f"📊 解析出 {len(parsed_benchlm)} 个 BenchLM.ai 大模型评分数据。")
    return parsed_benchlm


def fetch_and_parse_clawbench() -> dict:
    """从 OpenClawProBench (suyoumo.github.io/bench) 抓取并解析智能体得分与排名"""
    url = "https://suyoumo.github.io/bench/"
    headers = {"User-Agent": "Mozilla/5.0"}
    req = urllib.request.Request(url, headers=headers)

    print(f"🌐 正在请求 OpenClawProBench 网页: {url} ...")
    with urllib.request.urlopen(req, timeout=20) as resp:
        html = resp.read().decode("utf-8", errors="ignore")

    pattern = r'data-model-id="([^"]+)".*?data-open-rank="(\d+)".*?<span class="bench-score">([0-9\.]+)</span>'
    matches = re.finditer(pattern, html, re.DOTALL)

    parsed_clawbench = {}
    for m in matches:
        raw_id = m.group(1).strip()
        rank = int(m.group(2))
        score = float(m.group(3))
        model_name = raw_id.split("__")[-1] if "__" in raw_id else raw_id
        
        info = {
            "raw_id": raw_id,
            "display_name": model_name,
            "score": round(score, 2),
            "rank": rank
        }
        parsed_clawbench[model_name.lower()] = info

    print(f"📊 解析出 {len(parsed_clawbench)} 个 OpenClawProBench 智能体大模型评分数据。")
    return parsed_clawbench


def match_score(model_id: str, parsed_models: dict, score_key: str = "rating") -> tuple:
    """通用算法：匹配 Model ID 在指定字典中的 Score 和 Rank"""
    model_id_clean = model_id.strip()
    model_id_lower = model_id_clean.lower()

    # 1. 显式映射表匹配
    if model_id_clean in MODEL_NAME_ALIAS_MAP:
        for alias in MODEL_NAME_ALIAS_MAP[model_id_clean]:
            if alias.lower() in parsed_models:
                info = parsed_models[alias.lower()]
                return info[score_key], info["rank"], info["display_name"]

    # 2. 精确完全相等匹配
    if model_id_lower in parsed_models:
        info = parsed_models[model_id_lower]
        return info[score_key], info["rank"], info["display_name"]

    return None, None, None


def update_all_models_markdown(arena_models: dict, benchlm_models: dict, clawbench_models: dict):
    """同步更新 ALL_MODELS.md 文件中的能力对比总表，包含 Arena、BenchLM 和 OpenClaw 三大榜单列"""
    if not ALL_MODELS_PATH.exists():
        print(f"⚠️ 文件未找到: {ALL_MODELS_PATH}")
        return

    content = ALL_MODELS_PATH.read_text(encoding="utf-8")
    lines = content.splitlines()

    new_lines = []
    in_table = False

    for line in lines:
        stripped = line.strip()

        # 检测表格头部
        if stripped.startswith("| 厂商 (Vendor)") and "模型名称 (Model ID)" in stripped:
            in_table = True
            header_parts = [p.strip() for p in line.split("|")[1:-1]]
            base_header = header_parts[:8]
            new_header = "| " + " | ".join(base_header) + " | Arena 积分 (Rank) | BenchLM 评分 (Rank) | OpenClaw 智能体评分 (Rank) |"
            new_lines.append(new_header)
            continue

        if in_table and stripped.startswith("| :---"):
            align_line = "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: | :---: | :---: |"
            new_lines.append(align_line)
            continue

        # 数据行
        if in_table and stripped.startswith("|") and not stripped.startswith("---"):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 8:
                model_id_raw = parts[1].strip("` ")
                
                # 1. Arena 评分
                arena_score, arena_rank, _ = match_score(model_id_raw, arena_models, "rating")
                if arena_score is not None:
                    arena_str = f"{arena_score:.1f} (#{arena_rank})"
                else:
                    arena_str = MODEL_N_A_EXPLANATIONS.get(model_id_raw, "N/A")

                # 2. BenchLM 评分
                benchlm_score, benchlm_rank, _ = match_score(model_id_raw, benchlm_models, "score")
                if benchlm_score is not None:
                    benchlm_str = f"{benchlm_score:.2f} (#{benchlm_rank})"
                else:
                    benchlm_str = MODEL_N_A_EXPLANATIONS.get(model_id_raw, "N/A")

                # 3. OpenClawProBench 智能体评分
                claw_score, claw_rank, _ = match_score(model_id_raw, clawbench_models, "score")
                if claw_score is not None:
                    claw_str = f"{claw_score:.2f} (#{claw_rank})"
                else:
                    claw_str = MODEL_N_A_EXPLANATIONS.get(model_id_raw, "N/A")

                row_parts = parts[:8] + [arena_str, benchlm_str, claw_str]
                formatted_line = "| " + " | ".join(row_parts) + " |"
                new_lines.append(formatted_line)
                print(f"  ➜ {model_id_raw:30s} => Arena: {arena_str:14s} | BenchLM: {benchlm_str:14s} | OpenClaw: {claw_str}")
            else:
                new_lines.append(line)
        else:
            if stripped.startswith("---"):
                in_table = False
            new_lines.append(line)

    # 写入新内容
    ALL_MODELS_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print(f"\n📝 成功更新 [{ALL_MODELS_PATH.name}] 中的三大权威榜单 (Arena + BenchLM + OpenClaw) 评分矩阵！")


def main():
    print("=" * 80)
    print("🚀 开始大模型 Arena、BenchLM.ai 与 OpenClawProBench 三大榜单评分自动抓取任务")
    print("=" * 80)

    # 1. 抓取 LMSYS Chatbot Arena
    arena_payload = fetch_lmsys_payload()
    parsed_arena = parse_arena_ratings(arena_payload)

    # 2. 抓取 BenchLM.ai
    parsed_benchlm = fetch_and_parse_benchlm()

    # 3. 抓取 OpenClawProBench
    parsed_clawbench = fetch_and_parse_clawbench()

    # 4. 保存 JSON 记录文件
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ARENA_JSON_PATH.write_text(json.dumps({"updated_at": now_str, "total_models": len(parsed_arena), "models": parsed_arena}, ensure_ascii=False, indent=2), encoding="utf-8")
    BENCHLM_JSON_PATH.write_text(json.dumps({"updated_at": now_str, "total_models": len(parsed_benchlm), "models": parsed_benchlm}, ensure_ascii=False, indent=2), encoding="utf-8")
    CLAWBENCH_JSON_PATH.write_text(json.dumps({"updated_at": now_str, "total_models": len(parsed_clawbench), "models": parsed_clawbench}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"💾 评分数据已分别保存至 [{ARENA_JSON_PATH.name}]、[{BENCHLM_JSON_PATH.name}] 与 [{CLAWBENCH_JSON_PATH.name}]")

    # 5. 同步更新 Markdown 表格
    print("\n🔄 开始同步填充 ALL_MODELS.md ...")
    update_all_models_markdown(parsed_arena, parsed_benchlm, parsed_clawbench)

    print("=" * 80)
    print("✨ 三大榜单数据全量同步完成！")
    print("=" * 80)

if __name__ == "__main__":
    main()
