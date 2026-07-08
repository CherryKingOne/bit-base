"""模型下载 — 从 HuggingFace 拉取模型（支持断点续传、自动重试、镜像源）"""

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
from bit.models.types import get_model_type_info

console = Console()

# 最大重试次数
MAX_RETRIES = 3

# 重试之间的等待秒数（指数退避基数）
RETRY_BACKOFF_BASE = 2


def pull_model(
    config: BitConfig,
    model_name: str,
    model_type: str = "llm",
    engine: str | None = None,
    precision: str | None = None,
    custom_dir: str | None = None,
) -> Path | None:
    """从 HuggingFace 拉取模型

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

    hf_base = config.hf_base
    if config.hf_mirror:
        console.print(f"[cyan]使用镜像源: {config.hf_mirror}[/cyan]")
    console.print(f"[cyan]正在查询模型信息: {model_name} (type={model_type})[/cyan]")

    # 获取模型文件列表
    files = _get_model_files(hf_base, model_name, precision, model_type)
    if not files:
        console.print(f"[red]未找到匹配的模型文件 (type={model_type}, precision={precision})[/red]")
        console.print("[yellow]提示: 检查模型名称或尝试其他类型[/yellow]")
        return None

    total_size = sum(f.get("size", 0) for f in files)
    console.print(f"[green]找到 {len(files)} 个文件，总大小: {_format_size(total_size)}[/green]")

    # 下载文件
    try:
        _download_files(files, model_dir, hf_base)
    except Exception as e:
        console.print(f"[red]下载失败: {e}[/red]")
        return None

    # 保存元数据
    _save_metadata(model_dir, model_name, engine, precision, model_type)

    console.print(f"[green]✓ 模型已保存到: {model_dir}[/green]")
    return model_dir


def _get_model_files(
    hf_base: str, model_name: str, precision: str, model_type: str = "llm"
) -> list[dict]:
    """获取模型文件列表

    LLM 类型：优先筛选匹配精度的 GGUF 文件
    其他类型：下载全部文件（跳过精度筛选）
    """
    api_url = f"{hf_base}/api/models/{model_name}"
    try:
        resp = httpx.get(api_url, timeout=httpx.Timeout(connect=15, read=30, write=10, pool=30), follow_redirects=True)
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
    type_info = get_model_type_info(model_type)

    # LLM 类型：优先筛选匹配精度的 GGUF 文件
    if type_info["has_precision"]:
        for s in siblings:
            filename = s.get("rfilename", "")
            if filename.endswith(".gguf") and _match_precision(filename, precision):
                files.append({
                    "filename": filename,
                    "url": f"{hf_base}/{model_name}/resolve/main/{filename}",
                    "size": s.get("size", 0),
                })

    # 如果没有匹配的 GGUF（或非 LLM 类型），下载全部文件
    if not files:
        for s in siblings:
            filename = s.get("rfilename", "")
            if filename and not filename.startswith(".") and not filename.endswith(".gitignore"):
                files.append({
                    "filename": filename,
                    "url": f"{hf_base}/{model_name}/resolve/main/{filename}",
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


def _download_files(files: list[dict], model_dir: Path, hf_base: str) -> None:
    """下载文件列表（支持断点续传和自动重试）"""
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
            # 确保文件的父目录存在（处理带子目录的文件如 assets/xxx.png）
            dest.parent.mkdir(parents=True, exist_ok=True)

            # 已完整下载则跳过
            if dest.exists() and size > 0 and dest.stat().st_size == size:
                console.print(f"  [dim]跳过已存在: {filename}[/dim]")
                continue

            _download_with_retry(url, dest, filename, size, progress)


def _download_with_retry(
    url: str,
    dest: Path,
    filename: str,
    expected_size: int,
    progress: Progress,
) -> None:
    """带断点续传和自动重试的下载

    - 使用 .part 临时文件，完成后原子重命名
    - 通过 HTTP Range 头实现断点续传
    - 连接断开时自动重试（指数退避）
    """
    part_file = dest.with_suffix(dest.suffix + ".part")
    max_retries = MAX_RETRIES

    for attempt in range(1, max_retries + 1):
        # 获取已下载的字节数（用于断点续传）
        existing_bytes = part_file.stat().st_size if part_file.exists() else 0

        # 如果已有完整文件大小的数据但 expected_size 为 0（未知大小），尝试完成
        if expected_size > 0 and existing_bytes >= expected_size:
            part_file.rename(dest)
            return

        task = progress.add_task(
            f"下载 {filename}" + (f" (续传 {existing_bytes}B)" if existing_bytes else ""),
            total=expected_size or None,
            completed=existing_bytes if expected_size else 0,
        )

        try:
            _do_download(url, part_file, existing_bytes, task, progress)

            # 下载完成，原子重命名
            if part_file.exists():
                if expected_size > 0 and part_file.stat().st_size != expected_size:
                    raise IOError(
                        f"文件大小不匹配: 预期 {expected_size}, 实际 {part_file.stat().st_size}"
                    )
                part_file.rename(dest)

            progress.update(task, completed=dest.stat().st_size if dest.exists() else (expected_size or 0))
            return

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 416 and part_file.exists():
                # Range Not Satisfiable — 文件可能已完整下载
                progress.update(task, completed=expected_size)
                part_file.rename(dest)
                return
            progress.remove_task(task)
            if attempt < max_retries:
                _retry_wait(attempt, filename, e)
            else:
                raise

        except (httpx.TransportError, httpx.RemoteProtocolError, ConnectionError, IOError) as e:
            progress.remove_task(task)
            if attempt < max_retries:
                _retry_wait(attempt, filename, e)
            else:
                raise

        except Exception as e:
            progress.remove_task(task)
            console.print(f"  [red]下载 {filename} 失败: {e}[/red]")
            raise

    # 不应到达此处
    raise RuntimeError(f"下载 {filename} 失败: 已达最大重试次数")


def _do_download(
    url: str,
    part_file: Path,
    existing_bytes: int,
    task,
    progress: Progress,
) -> None:
    """执行单次下载（带断点续传）

    使用 Range 头从 existing_bytes 位置继续下载。
    超时设置: 连接 15s，读取 60s（大文件需较长读取超时）。
    """
    headers = {}
    mode = "wb"

    if existing_bytes > 0:
        headers["Range"] = f"bytes={existing_bytes}-"
        mode = "ab"  # 追加模式

    timeout = httpx.Timeout(connect=15, read=60, write=30, pool=30)

    with httpx.stream("GET", url, headers=headers, timeout=timeout, follow_redirects=True) as resp:
        resp.raise_for_status()

        # 如果服务端返回 200（不支持 Range），从头开始
        if resp.status_code == 200 and existing_bytes > 0:
            mode = "wb"

        with open(part_file, mode) as f:
            for chunk in resp.iter_bytes(chunk_size=65536):
                f.write(chunk)
                progress.update(task, advance=len(chunk))


def _retry_wait(attempt: int, filename: str, error: Exception) -> None:
    """指数退避等待"""
    wait = RETRY_BACKOFF_BASE ** attempt
    console.print(
        f"  [yellow]下载 {filename} 中断 ({type(error).__name__}), "
        f"第 {attempt} 次重试（等待 {wait}s）...[/yellow]"
    )
    time.sleep(wait)


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
