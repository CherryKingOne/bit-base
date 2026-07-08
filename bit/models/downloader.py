"""模型下载 — 使用 huggingface_hub 官方工具拉取模型

使用 HuggingFace 官方 huggingface_hub 库进行下载，自带：
- 断点续传（自动跳过已下载的完整文件）
- 自动重试（网络中断后自动恢复）
- 镜像源支持（通过 HF_ENDPOINT 环境变量或 endpoint 参数）
- 多线程并发下载
- 原生进度条
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from huggingface_hub import HfApi, snapshot_download
from rich.console import Console

from bit.config import BitConfig
from bit.models.types import get_model_type_info

console = Console()


def pull_model(
    config: BitConfig,
    model_name: str,
    model_type: str = "llm",
    engine: str | None = None,
    precision: str | None = None,
    custom_dir: str | None = None,
) -> Path | None:
    """从 HuggingFace 拉取模型

    使用 huggingface_hub 官方下载工具，自带断点续传、自动重试、镜像源支持。

    Args:
        config: 全局配置
        model_name: 模型名称（如 Qwen/Qwen3-8B）
        model_type: 模型类型（llm/video/tts/asr/ocr/embedding/reranker）
        engine: 推理引擎，None 则按类型自动选择
        precision: 模型精度，仅 LLM 类型有效
        custom_dir: 自定义存储路径
    """
    type_info = get_model_type_info(model_type)

    # 按类型自动选择引擎和精度
    if engine is None:
        engine = type_info["default_engine"]
    if precision is None:
        precision = "q4_k_m" if type_info["has_precision"] else "none"

    # 确定存储路径
    if custom_dir:
        model_dir = Path(custom_dir) / _safe_name(model_name)
    else:
        model_dir = config.models_path(model_type) / _safe_name(model_name)

    # 检查是否已下载
    meta_file = model_dir / ".bit_meta.json"
    if meta_file.exists():
        console.print(f"[yellow]模型已存在: {model_dir}[/yellow]")
        if not _confirm("是否重新下载?"):
            return model_dir

    model_dir.mkdir(parents=True, exist_ok=True)

    hf_endpoint = config.hf_base
    if config.hf_mirror:
        console.print(f"[cyan]使用镜像源: {config.hf_mirror}[/cyan]")
    console.print(f"[cyan]正在查询模型信息: {model_name} (type={model_type})[/cyan]")

    # 使用 HfApi 获取模型文件列表
    api = HfApi(endpoint=hf_endpoint)
    try:
        model_info = api.model_info(model_name, files_metadata=True)
    except Exception as e:
        console.print(f"[red]获取模型信息失败: {e}[/red]")
        return None

    siblings = model_info.siblings or []
    type_info = get_model_type_info(model_type)

    # 确定要下载的文件列表及 allow_patterns
    allow_patterns, file_count, total_size = _build_download_patterns(
        siblings, precision, model_type
    )

    if file_count == 0:
        console.print(f"[red]未找到匹配的模型文件 (type={model_type}, precision={precision})[/red]")
        console.print("[yellow]提示: 检查模型名称或尝试其他类型[/yellow]")
        return None

    console.print(f"[green]找到 {file_count} 个文件，总大小: {_format_size(total_size)}[/green]")

    # 使用官方 snapshot_download 下载（自带断点续传、重试、进度条）
    console.print(f"[cyan]开始下载到: {model_dir}[/cyan]")
    try:
        snapshot_download(
            repo_id=model_name,
            local_dir=str(model_dir),
            allow_patterns=allow_patterns,
            endpoint=hf_endpoint,
        )
    except Exception as e:
        console.print(f"[red]下载失败: {e}[/red]")
        console.print("[yellow]提示: 重新运行 bit pull 可断点续传，已下载的文件会自动跳过[/yellow]")
        return None

    # 保存元数据
    _save_metadata(model_dir, model_name, engine, precision, model_type)

    console.print(f"[green]✓ 模型已保存到: {model_dir}[/green]")
    return model_dir


def _build_download_patterns(
    siblings: list, precision: str, model_type: str
) -> tuple[list[str], int, int]:
    """根据模型类型和精度构建下载文件模式

    Returns:
        (allow_patterns, file_count, total_size)
    """
    type_info = get_model_type_info(model_type)
    patterns: list[str] = []
    total_size = 0

    # LLM 类型：优先筛选匹配精度的 GGUF 文件
    if type_info["has_precision"]:
        for s in siblings:
            filename = s.rfilename
            if filename.endswith(".gguf") and _match_precision(filename, precision):
                patterns.append(filename)
                total_size += s.size or 0

    # 如果没有匹配的 GGUF（或非 LLM 类型），下载全部文件
    if not patterns:
        for s in siblings:
            filename = s.rfilename
            if filename and not filename.startswith(".") and not filename.endswith(".gitignore"):
                patterns.append(filename)
                total_size += s.size or 0

    return patterns, len(patterns), total_size


def _match_precision(filename: str, precision: str) -> bool:
    """检查文件名是否匹配精度"""
    filename_lower = filename.lower()
    precision_lower = precision.lower()

    # 直接匹配
    if precision_lower in filename_lower:
        return True

    # 常见别名
    aliases = {
        "q4_k_m": ["q4_k_m", "q4km", "iq4_xs"],
        "q4_k_s": ["q4_k_s", "q4ks"],
        "q5_k_m": ["q5_k_m", "q5km"],
        "q8_0": ["q8_0", "q80"],
        "fp16": ["f16", "fp16"],
        "fp32": ["f32", "fp32", "no_quant"],
    }

    for key, values in aliases.items():
        if precision_lower == key:
            return any(v in filename_lower for v in values)

    return False


def _save_metadata(
    model_dir: Path, name: str, engine: str, precision: str, model_type: str = "llm"
) -> None:
    """保存模型元数据"""
    meta = {
        "name": name,
        "engine": engine,
        "precision": precision,
        "model_type": model_type,
        "downloaded_at": time.time(),
    }
    (model_dir / ".bit_meta.json").write_text(json.dumps(meta, indent=2))


def _safe_name(name: str) -> str:
    """将模型名转为安全的目录名"""
    return name.replace("/", "_").replace("\\", "_")


def _format_size(size: int) -> str:
    """格式化文件大小"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}PB"


def _confirm(message: str) -> bool:
    """确认提示"""
    try:
        resp = console.input(f"[yellow]{message} (y/N): [/yellow]")
        return resp.lower() == "y"
    except (EOFError, KeyboardInterrupt):
        return False
