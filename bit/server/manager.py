"""模型运行管理器 — 多模型服务管理"""

from __future__ import annotations

import json
import os
import signal
import socket
import time
from pathlib import Path

from rich.console import Console

console = Console()

# 运行中的模型 {model_name: {engine, port, pid, start_time, ...}}
_running: dict[str, dict] = {}


def _get_state_file() -> Path:
    """状态文件路径"""
    return Path.home() / ".bit" / "running.json"


def _save_state() -> None:
    """持久化运行状态"""
    state_file = _get_state_file()
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(_running, indent=2, default=str))


def _load_state() -> None:
    """加载运行状态"""
    global _running
    state_file = _get_state_file()
    if state_file.exists():
        try:
            _running = json.loads(state_file.read_text())
        except Exception:
            _running = {}


def _find_free_port() -> int:
    """查找可用端口"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def is_port_available(port: int) -> bool:
    """检查端口是否可用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("", port))
            return True
        except OSError:
            return False


def register_model(name: str, engine: str, port: int, pid: int) -> None:
    """注册运行中的模型"""
    _load_state()
    _running[name] = {
        "engine": engine,
        "port": port,
        "pid": pid,
        "start_time": time.time(),
        "status": "running",
    }
    _save_state()


def unregister_model(name: str) -> None:
    """注销模型"""
    _load_state()
    if name in _running:
        del _running[name]
        _save_state()


def list_running() -> list[dict]:
    """列出运行中的模型"""
    _load_state()
    result = []
    for name, info in _running.items():
        # 检查进程是否存活
        pid = info.get("pid", 0)
        alive = _is_process_alive(pid)

        uptime = time.time() - info.get("start_time", time.time())
        result.append({
            "name": name,
            "engine": info.get("engine", "unknown"),
            "port": info.get("port", 0),
            "pid": pid,
            "status": "running" if alive else "stopped",
            "uptime": _format_uptime(uptime),
        })

    return result


def get_stats(model_name: str | None = None) -> list[dict]:
    """获取模型运行指标"""
    _load_state()
    result = []

    for name, info in _running.items():
        if model_name and name != model_name:
            continue

        pid = info.get("pid", 0)
        alive = _is_process_alive(pid)
        uptime = time.time() - info.get("start_time", time.time())

        # 尝试从引擎获取详细指标
        stats = _get_engine_stats(name, info)

        result.append({
            "name": name,
            "port": info.get("port", 0),
            "engine": info.get("engine", "unknown"),
            "status": "running" if alive else "stopped",
            "uptime": _format_uptime(uptime),
            "pid": pid,
            "tokens_per_sec": stats.get("tokens_per_sec", "N/A"),
            "first_token_ms": stats.get("first_token_ms", "N/A"),
            "vram": stats.get("vram", "N/A"),
        })

    return result


def _get_engine_stats(name: str, info: dict) -> dict:
    """从引擎获取详细指标"""
    port = info.get("port", 0)
    if not port:
        return {}

    try:
        import httpx
        resp = httpx.get(f"http://localhost:{port}/metrics", timeout=2)
        if resp.status_code == 200:
            # 解析 Prometheus 格式指标
            return _parse_metrics(resp.text)
    except Exception:
        pass

    return {}


def _parse_metrics(text: str) -> dict:
    """解析 Prometheus 格式指标"""
    stats = {}
    for line in text.split("\n"):
        if line.startswith("#"):
            continue
        if "tokens_per_second" in line:
            try:
                stats["tokens_per_sec"] = float(line.split()[-1])
            except (ValueError, IndexError):
                pass
        elif "first_token_latency" in line:
            try:
                stats["first_token_ms"] = float(line.split()[-1]) * 1000
            except (ValueError, IndexError):
                pass
    return stats


def stop_model(model_name: str) -> bool:
    """停止指定模型"""
    _load_state()
    if model_name not in _running:
        console.print(f"[red]未找到运行中的模型: {model_name}[/red]")
        return False

    info = _running[model_name]
    pid = info.get("pid")

    if pid and _is_process_alive(pid):
        try:
            os.kill(pid, signal.SIGTERM)
            # 等待进程退出
            for _ in range(10):
                if not _is_process_alive(pid):
                    break
                time.sleep(0.5)
            # 如果还没退出，强制杀死
            if _is_process_alive(pid):
                os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    del _running[model_name]
    _save_state()
    console.print(f"[green]✓ 已停止: {model_name}[/green]")
    return True


def stop_all() -> None:
    """停止所有模型"""
    _load_state()
    for name in list(_running.keys()):
        stop_model(name)


def _is_process_alive(pid: int) -> bool:
    """检查进程是否存活"""
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def _format_uptime(seconds: float) -> str:
    """格式化运行时间"""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds / 60:.1f}m"
    else:
        return f"{seconds / 3600:.1f}h"
