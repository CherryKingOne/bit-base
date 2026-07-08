"""引擎包初始化 — 注册所有可用引擎"""

from bit.engines.base import BaseEngine
from bit.engines.llamacpp import LlamaCppEngine
from bit.engines.vllm import VllmEngine
from bit.engines.sglang import SglangEngine

ENGINES: dict[str, type[BaseEngine]] = {
    "llama.cpp": LlamaCppEngine,
    "vllm": VllmEngine,
    "sglang": SglangEngine,
}


def get_engine(name: str) -> BaseEngine:
    """获取引擎实例"""
    engine_cls = ENGINES.get(name)
    if not engine_cls:
        raise ValueError(f"不支持的引擎: {name}. 可用引擎: {list(ENGINES.keys())}")
    return engine_cls()


def list_engines() -> list[str]:
    """列出所有可用引擎"""
    return list(ENGINES.keys())
