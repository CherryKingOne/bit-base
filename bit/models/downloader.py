"""模型下载 — 从 HuggingFace 拉取模型"""

from __future__ import annotations

import json
import time
from pathlib import Path

import httpx
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
)

from bit.config import BitConfig

console = Console()

HF_API = "https://huggingface.co/api/models"
HF_DOWNLOAD = "https://huggingface.co"


def pull_model(
    config: BitConfig,
    model_name: str,
    engine: str = "llama.cpp",
    precision: str = "q4_k_m",
    custom_dir: str | None = None,
) -> Path | None:
    """从 HuggingFace 拉取模型"""
    # 确定存储路径
    if custom_dir:
        model_dir = Path(custom_dir) / _safe_name(model_name)
    else:
        model_dir = config.models_path("llm") / _safe_name(model_name)

    # 检查是否已下载
    meta_file = model_dir / ".bit_meta.json"
    if meta_file.exists():
        console.print(f"[yellow]模型已存在: {model_dir}[/yellow]")
        if not _confirm("是否重新下载?"):
            return model_dir

    model_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"[cyan]正在查询模型信息: {model_name}[/cyan]")

    # 获取模型文件列表
    files = _get_model_files(model_name, precision)
    if not files:
        console.print(f"[red]未找到匹配的模型文件 (precision={precision})[/red]")
        console.print("[yellow]提示: 尝试其他精度或检查模型名称[/yellow]")
        return None

    total_size = sum(f.get("size", 0) for f in files)
    console.print(f"[green]找到 {len(files)} 个文件，总大小: {_format_size(total_size)}[/green]")

    # 下载文件
    try:
        _download_files(files, model_dir)
    except Exception as e:
        console.print(f"[red]下载失败: {e}[/red]")
        return None

    # 保存元数据
    _save_metadata(model_dir, model_name, engine, precision)

    console.print(f"[green]✓ 模型已保存到: {model_dir}[/green]")
    return model_dir


def _get_model_files(model_name: str, precision: str) -> list[dict]:
    """获取模型文件列表"""
    try:
        resp = httpx.get(f"{HF_API}/{model_name}", timeout=30, follow_redirects=True)
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            console.print(f"[red]模型不存在: {model_name}[/red]")
        else:
            console.print(f"[red]API 错误: {e.response.status_code}[/red]")
        return []
    except Exception as e:
        console.print(f"[red]连接失败: {e}[/red]")
        return []

    files = []
    siblings = data.get("siblings", [])

    # 优先筛选 GGUF 文件
    for s in siblings:
        filename = s.get("rfilename", "")
        if filename.endswith(".gguf") and _match_precision(filename, precision):
            files.append({
                "filename": filename,
                "url": f"{HF_DOWNLOAD}/{model_name}/resolve/main/{filename}",
                "size": s.get("size", 0),
            })

    # 如果没有 GGUF，下载全部文件（用于 vLLM/SGLang）
    if not files:
        for s in siblings:
            filename = s.get("rfilename", "")
            if filename and not filename.startswith(".") and not filename.endswith(".gitignore"):
                files.append({
                    "filename": filename,
                    "url": f"{HF_DOWNLOAD}/{model_name}/resolve/main/{filename}",
                    "size": s.get("size", 0),
                })

    return files


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


def _download_files(files: list[dict], model_dir: Path) -> None:
    """下载文件列表"""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        for file_info in files:
            filename = file_info["filename"]
            url = file_info["url"]
            size = file_info.get("size", 0)

            dest = model_dir / filename
            if dest.exists() and dest.stat().st_size == size:
                console.print(f"  [dim]跳过已存在: {filename}[/dim]")
                continue

            task = progress.add_task(f"下载 {filename}", total=size or None)

            try:
                with httpx.stream("GET", url, timeout=300, follow_redirects=True) as resp:
                    resp.raise_for_status()
                    with open(dest, "wb") as f:
                        for chunk in resp.iter_bytes(chunk_size=65536):
                            f.write(chunk)
                            progress.update(task, advance=len(chunk))
            except Exception as e:
                console.print(f"  [red]下载 {filename} 失败: {e}[/red]")
                raise


def _save_metadata(model_dir: Path, name: str, engine: str, precision: str) -> None:
    """保存模型元数据"""
    meta = {
        "name": name,
        "engine": engine,
        "precision": precision,
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
