"""模型类型定义 — 支持的模型类型及其元信息"""

from __future__ import annotations

# 支持的模型类型（规范化名称）
MODEL_TYPES = {
    "llm": {
        "name": "llm",
        "has_precision": True,
        "default_engine": "llama.cpp",
    },
    "video": {
        "name": "video",
        "has_precision": False,
        "default_engine": "vllm",
    },
    "tts": {
        "name": "tts",
        "has_precision": False,
        "default_engine": "custom",
    },
    "asr": {
        "name": "asr",
        "has_precision": False,
        "default_engine": "custom",
    },
    "ocr": {
        "name": "ocr",
        "has_precision": False,
        "default_engine": "custom",
    },
    "embedding": {
        "name": "embedding",
        "has_precision": False,
        "default_engine": "custom",
    },
    "reranker": {
        "name": "reranker",
        "has_precision": False,
        "default_engine": "custom",
    },
}

# 大小写别名映射 → 规范化名称
_TYPE_ALIASES = {
    # LLM
    "llm": "llm",
    "llms": "llm",
    "large_language_model": "llm",
    # Video
    "video": "video",
    "videos": "video",
    "vlm": "video",
    "vision": "video",
    "multimodal": "video",
    # TTS
    "tts": "tts",
    "text_to_speech": "tts",
    "speech": "tts",
    # ASR
    "asr": "asr",
    "stt": "asr",
    "speech_to_text": "asr",
    # OCR
    "ocr": "ocr",
    # Embedding
    "embedding": "embedding",
    "embeddings": "embedding",
    "embed": "embedding",
    # Reranker
    "reranker": "reranker",
    "rerank": "reranker",
    "rerankers": "reranker",
    "ranker": "reranker",
}


def resolve_model_type(type_str: str) -> str | None:
    """将用户输入的类型字符串解析为规范化类型名。

    大小写不敏感，支持常见别名。

    Args:
        type_str: 用户输入的类型字符串（如 "LLM", "ocr", "Embedding"）

    Returns:
        规范化类型名（如 "llm", "ocr", "embedding"），不支持的类型返回 None
    """
    if not type_str:
        return None
    key = type_str.lower().strip()
    return _TYPE_ALIASES.get(key)


def get_model_type_info(model_type: str) -> dict:
    """获取模型类型的元信息"""
    return MODEL_TYPES.get(model_type, {
        "name": model_type,
        "has_precision": False,
        "default_engine": "custom",
    })


def list_model_types() -> list[str]:
    """列出所有支持的模型类型"""
    return list(MODEL_TYPES.keys())
