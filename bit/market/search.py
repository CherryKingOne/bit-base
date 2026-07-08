"""模型市场 — 搜索和浏览模型"""

from __future__ import annotations

import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from bit.config import BitConfig, load_config

console = Console()

# 默认 HF API 地址，运行时可通过 config.hf_base 使用镜像
HF_API = f"{load_config().hf_base}/api/models"

# 常用模型预定义（快速访问）
CURATED_MODELS = {
    "llm": [
        {"name": "Qwen/Qwen3-8B", "desc": "通义千问3 8B，中英文双语", "size": "~5GB"},
        {"name": "Qwen/Qwen2.5-7B-Instruct", "desc": "通义千问2.5 7B 指令版", "size": "~4GB"},
        {"name": "meta-llama/Llama-3.1-8B-Instruct", "desc": "Meta Llama 3.1 8B", "size": "~5GB"},
        {"name": "THUDM/glm-4-9b-chat", "desc": "智谱 GLM-4 9B", "size": "~6GB"},
        {"name": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B", "desc": "DeepSeek R1 蒸馏版 7B", "size": "~4GB"},
    ],
    "embedding": [
        {"name": "BAAI/bge-small-zh-v1.5", "desc": "BGE 中文小模型", "size": "~100MB"},
        {"name": "BAAI/bge-large-zh-v1.5", "desc": "BGE 中文大模型", "size": "~1.3GB"},
    ],
    "video": [
        {"name": "Qwen/Qwen2-VL-7B-Instruct", "desc": "通义千问2 视觉语言 7B", "size": "~5GB"},
    ],
    "tts": [
        {"name": "microsoft/speecht5_tts", "desc": "Microsoft SpeechT5 TTS", "size": "~500MB"},
    ],
    "asr": [
        {"name": "openai/whisper-large-v3", "desc": "OpenAI Whisper Large v3", "size": "~3GB"},
        {"name": "openai/whisper-small", "desc": "OpenAI Whisper Small", "size": "~500MB"},
    ],
    "ocr": [
        {"name": "PaddlePaddle/PP-OCRv4", "desc": "PaddleOCR PP-OCRv4", "size": "~200MB"},
    ],
    "reranker": [
        {"name": "BAAI/bge-reranker-base", "desc": "BGE Reranker Base", "size": "~300MB"},
        {"name": "BAAI/bge-reranker-large", "desc": "BGE Reranker Large", "size": "~1.3GB"},
    ],
}


def search_models(
    keyword: str,
    limit: int = 10,
    category: str | None = None,
) -> list[dict]:
    """搜索 HuggingFace 模型"""
    results = []

    # 先搜索预定义模型
    for cat, models in CURATED_MODELS.items():
        if category and cat != category:
            continue
        for m in models:
            if keyword.lower() in m["name"].lower() or keyword.lower() in m["desc"].lower():
                results.append({
                    "name": m["name"],
                    "desc": m["desc"],
                    "engine": "llama.cpp",
                    "precision": "多版本",
                    "size": m["size"],
                    "source": "curated",
                })

    # 如果预定义不够，搜索 HuggingFace
    if len(results) < limit:
        try:
            hf_results = _search_hf(keyword, limit - len(results))
            results.extend(hf_results)
        except Exception as e:
            console.print(f"[yellow]HF 搜索失败: {e}[/yellow]")

    return results[:limit]


def get_model_info(model_name: str) -> dict | None:
    """获取模型详细信息"""
    try:
        api_base = f"{load_config().hf_base}/api/models"
        resp = httpx.get(f"{api_base}/{model_name}", timeout=30, follow_redirects=True)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        console.print(f"[red]获取模型信息失败: {e}[/red]")
        return None

    siblings = data.get("siblings", [])
    files = []
    total_size = 0

    for s in siblings:
        filename = s.get("rfilename", "")
        size = s.get("size", 0)
        total_size += size
        if filename.endswith(".gguf"):
            files.append({"name": filename, "size": _format_size(size), "type": "gguf"})
        elif filename.endswith(".safetensors"):
            files.append({"name": filename, "size": _format_size(size), "type": "safetensors"})

    # 判断支持的引擎
    has_gguf = any(f["type"] == "gguf" for f in files)
    has_safetensors = any(f["type"] == "safetensors" for f in files)

    engines = []
    if has_gguf:
        engines.append("llama.cpp")
    if has_safetensors:
        engines.extend(["vllm", "sglang"])

    return {
        "name": model_name,
        "desc": data.get("description", "")[:200],
        "downloads": data.get("downloads", 0),
        "likes": data.get("likes", 0),
        "engines": engines,
        "total_size": _format_size(total_size),
        "files": files[:20],  # 最多显示20个文件
        "tags": data.get("tags", [])[:10],
    }


def list_categories() -> list[dict]:
    """列出模型分类"""
    from bit.i18n.translator import t

    category_labels = {
        "llm": t("categories_llm"),
        "embedding": t("categories_embedding"),
        "video": t("categories_video"),
        "tts": t("categories_tts"),
        "asr": t("categories_asr"),
        "ocr": t("categories_ocr"),
        "reranker": t("categories_reranker"),
    }

    result = []
    for cat_name in ["llm", "video", "tts", "asr", "ocr", "embedding", "reranker"]:
        result.append({
            "name": cat_name,
            "desc": category_labels.get(cat_name, cat_name),
            "count": len(CURATED_MODELS.get(cat_name, [])),
        })
    return result


def _search_hf(keyword: str, limit: int) -> list[dict]:
    """搜索 HuggingFace"""
    api_base = f"{load_config().hf_base}/api/models"
    resp = httpx.get(
        api_base,
        params={
            "search": keyword,
            "sort": "downloads",
            "direction": "-1",
            "limit": limit,
        },
        timeout=30,
    )
    resp.raise_for_status()

    results = []
    for m in resp.json():
        model_id = m.get("id", "")
        siblings = m.get("siblings", [])
        has_gguf = any(s.get("rfilename", "").endswith(".gguf") for s in siblings)

        engine = "llama.cpp" if has_gguf else "vllm"
        downloads = m.get("downloads", 0)

        results.append({
            "name": model_id,
            "desc": m.get("description", "")[:100] if m.get("description") else "",
            "engine": engine,
            "precision": "多版本",
            "size": f"{downloads:,} downloads",
            "source": "huggingface",
        })

    return results


def _format_size(size: int) -> str:
    """格式化文件大小"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}PB"
