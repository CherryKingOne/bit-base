"""推理引擎抽象接口"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, AsyncGenerator


class BaseEngine(ABC):
    """推理引擎基类"""

    @abstractmethod
    def name(self) -> str:
        """引擎名称"""

    @abstractmethod
    def load_model(self, model_path: Path, precision: str, **kwargs) -> None:
        """加载模型"""

    @abstractmethod
    def chat(self, messages: list[dict], stream: bool = False, **kwargs) -> Any:
        """对话推理"""

    async def chat_stream(
        self, messages: list[dict], **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式对话推理（默认实现：调用非流式后逐字输出）"""
        result = self.chat(messages, stream=False, **kwargs)
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        # 逐字输出模拟流式
        for char in content:
            yield char

    @abstractmethod
    def unload(self) -> None:
        """卸载模型"""

    @abstractmethod
    def stats(self) -> dict:
        """获取运行指标"""
