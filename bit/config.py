"""配置管理"""

from __future__ import annotations

import os
import json
from pathlib import Path
from dataclasses import dataclass, field

# HuggingFace 默认地址
HF_DEFAULT_BASE = "https://huggingface.co"

# 国内常用镜像
HF_MIRRORS = {
    "hf-mirror": "https://hf-mirror.com",
}


@dataclass
class BitConfig:
    """全局配置"""

    # 模型存储根目录
    model_dir: Path = field(default_factory=lambda: _default_model_dir())

    # API 服务默认端口范围
    port_range: tuple[int, int] = (10000, 60000)

    # HF 镜像源（可选），如 https://hf-mirror.com
    hf_mirror: str | None = None

    @property
    def hf_base(self) -> str:
        """当前 HF 基础 URL（含镜像）"""
        return self.hf_mirror or HF_DEFAULT_BASE

    def models_path(self, model_type: str = "llm") -> Path:
        """获取指定类型的模型存储路径"""
        path = self.model_dir / model_type
        path.mkdir(parents=True, exist_ok=True)
        return path


def _default_model_dir() -> Path:
    """默认模型存储目录: 项目根目录下的 model_cache/"""
    env_dir = os.environ.get("BIT_MODEL_DIR")
    if env_dir:
        return Path(env_dir)
    # 项目根目录: 从当前工作目录向上查找包含 pyproject.toml 的目录
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if (parent / "pyproject.toml").exists():
            return parent / "model_cache"
    # 回退: 当前工作目录下的 model_cache/
    return cwd / "model_cache"


def load_config() -> BitConfig:
    """加载配置

    优先级: 环境变量 > ~/.bit/config.json > 默认值

    支持的环境变量:
      - BIT_MODEL_DIR: 模型存储目录
      - HF_ENDPOINT:   HF 镜像地址（与 huggingface-cli 一致）
      - BIT_HF_MIRROR: HF 镜像地址（同 HF_ENDPOINT，bit 专用）

    配置镜像源后，会自动同步设置 HF_ENDPOINT 环境变量，
    使 huggingface_hub 库的所有操作（下载、搜索）自动使用镜像。
    """
    config = BitConfig()

    # 环境变量
    env_dir = os.environ.get("BIT_MODEL_DIR")
    if env_dir:
        config.model_dir = Path(env_dir)

    env_mirror = os.environ.get("HF_ENDPOINT") or os.environ.get("BIT_HF_MIRROR")
    if env_mirror:
        config.hf_mirror = env_mirror.rstrip("/")

    # 配置文件 ~/.bit/config.json
    config_file = Path.home() / ".bit" / "config.json"
    if config_file.exists():
        try:
            data = json.loads(config_file.read_text())
            if "model_dir" in data and not env_dir:
                config.model_dir = Path(data["model_dir"])
            if "hf_mirror" in data and not env_mirror:
                config.hf_mirror = data["hf_mirror"]
        except Exception:
            pass

    # 将镜像源同步到 HF_ENDPOINT 环境变量，让 huggingface_hub 自动识别
    if config.hf_mirror:
        os.environ["HF_ENDPOINT"] = config.hf_mirror

    return config
