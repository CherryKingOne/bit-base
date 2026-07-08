"""模型注册表 — 管理已下载模型"""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

from rich.console import Console

from bit.config import BitConfig

console = Console()


def list_models(config: BitConfig) -> list[dict]:
    """列出所有已下载模型"""
    models = []
    model_root = config.model_dir

    if not model_root.exists():
        return models

    for meta_file in model_root.rglob(".bit_meta.json"):
        try:
            meta = json.loads(meta_file.read_text())
            parent = meta_file.parent
            size = _dir_size(parent)
            models.append({
                "name": meta.get("name", parent.name),
                "engine": meta.get("engine", "unknown"),
                "precision": meta.get("precision", "unknown"),
                "model_type": meta.get("model_type", "llm"),
                "size": _format_size(size),
                "path": str(parent),
                "downloaded_at": meta.get("downloaded_at"),
            })
        except Exception:
            continue

    # 按下载时间排序
    models.sort(key=lambda x: x.get("downloaded_at", 0), reverse=True)
    return models


def get_model_info(config: BitConfig, model_name: str) -> dict | None:
    """获取模型详细信息"""
    model_dir = _find_model(config, model_name)
    if not model_dir:
        return None

    meta_file = model_dir / ".bit_meta.json"
    if not meta_file.exists():
        return None

    meta = json.loads(meta_file.read_text())
    size = _dir_size(model_dir)

    # 列出模型文件
    files = []
    for f in model_dir.iterdir():
        if f.is_file() and not f.name.startswith("."):
            files.append({
                "name": f.name,
                "size": _format_size(f.stat().st_size),
            })

    return {
        **meta,
        "total_size": _format_size(size),
        "path": str(model_dir),
        "files": files,
    }


def remove_model(config: BitConfig, model_name: str, force: bool = False) -> bool:
    """删除指定模型"""
    model_dir = _find_model(config, model_name)
    if not model_dir:
        console.print(f"[red]未找到模型: {model_name}[/red]")
        return False

    if not force:
        size = _format_size(_dir_size(model_dir))
        confirm = console.input(
            f"[yellow]确认删除 {model_name} ({size})? (y/N): [/yellow]"
        )
        if confirm.lower() != "y":
            console.print("[yellow]已取消[/yellow]")
            return False

    shutil.rmtree(model_dir)
    console.print(f"[green]✓ 已删除: {model_name}[/green]")
    return True


def _find_model(config: BitConfig, model_name: str) -> Path | None:
    """查找模型目录"""
    model_root = config.model_dir
    if not model_root.exists():
        return None

    # 精确匹配
    for meta_file in model_root.rglob(".bit_meta.json"):
        try:
            meta = json.loads(meta_file.read_text())
            if meta.get("name") == model_name:
                return meta_file.parent
        except Exception:
            continue

    # 模糊匹配（包含关键字）
    for meta_file in model_root.rglob(".bit_meta.json"):
        try:
            meta = json.loads(meta_file.read_text())
            if model_name.lower() in meta.get("name", "").lower():
                return meta_file.parent
        except Exception:
            continue

    # 目录名匹配
    for d in model_root.rglob("*"):
        if d.is_dir() and model_name.lower() in d.name.lower():
            if (d / ".bit_meta.json").exists():
                return d

    return None


def _dir_size(path: Path) -> int:
    """计算目录大小"""
    total = 0
    for f in path.rglob("*"):
        if f.is_file():
            try:
                total += f.stat().st_size
            except OSError:
                pass
    return total


def _format_size(size: int) -> str:
    """格式化文件大小"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}PB"
