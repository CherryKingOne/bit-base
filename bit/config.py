"""配置管理"""

from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class BitConfig:
    """全局配置"""

    # 模型存储根目录
    model_dir: Path = field(default_factory=lambda: _default_model_dir())

    # API 服务默认端口范围
    port_range: tuple[int, int] = (10000, 60000)

    # HF 镜像源（可选）
    hf_mirror: str | None = None

    def models_path(self, model_type: str = "llm") -> Path:
        """获取指定类型的模型存储路径"""
        path = self.model_dir / model_type
        path.mkdir(parents=True, exist_ok=True)
        return path


def _default_model_dir() -> Path:
    """默认模型存储目录: ~/.bit/models/"""
    env_dir = os.environ.get("BIT_MODEL_DIR")
    if env_dir:
        return Path(env_dir)
    return Path.home() / ".bit" / "models"


def load_config() -> BitConfig:
    """加载配置"""
    return BitConfig()
