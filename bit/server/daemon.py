"""后台进程管理 — daemon 模式支持"""

from __future__ import annotations

import os
import signal
import sys
import time
from pathlib import Path

from rich.console import Console

console = Console()


def daemonize() -> None:
    """将当前进程转为后台守护进程"""
    # 第一次 fork
    pid = os.fork()
    if pid > 0:
        # 父进程退出
        sys.exit(0)

    # 创建新会话
    os.setsid()

    # 第二次 fork
    pid = os.fork()
    if pid > 0:
        sys.exit(0)

    # 重定向标准输入输出
    devnull = open(os.devnull, "r")
    os.dup2(devnull.fileno(), sys.stdin.fileno())

    log_dir = Path.home() / ".bit" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    stdout_log = open(log_dir / "bit.log", "a")
    stderr_log = open(log_dir / "bit.log", "a")
    os.dup2(stdout_log.fileno(), sys.stdout.fileno())
    os.dup2(stderr_log.fileno(), sys.stderr.fileno())

    # 写入 PID 文件
    pid_file = _get_pid_file()
    pid_file.write_text(str(os.getpid()))


def _get_pid_file() -> Path:
    """PID 文件路径"""
    return Path.home() / ".bit" / "bit.pid"


def is_daemon_running() -> bool:
    """检查守护进程是否在运行"""
    pid_file = _get_pid_file()
    if not pid_file.exists():
        return False

    try:
        pid = int(pid_file.read_text().strip())
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, ValueError):
        pid_file.unlink(missing_ok=True)
        return False


def get_daemon_pid() -> int | None:
    """获取守护进程 PID"""
    pid_file = _get_pid_file()
    if not pid_file.exists():
        return None

    try:
        return int(pid_file.read_text().strip())
    except ValueError:
        return None


def stop_daemon() -> bool:
    """停止守护进程"""
    pid = get_daemon_pid()
    if pid is None:
        console.print("[yellow]守护进程未运行[/yellow]")
        return False

    try:
        os.kill(pid, signal.SIGTERM)
        # 等待退出
        for _ in range(10):
            try:
                os.kill(pid, 0)
                time.sleep(0.5)
            except ProcessLookupError:
                break
        # 清理 PID 文件
        _get_pid_file().unlink(missing_ok=True)
        console.print("[green]守护进程已停止[/green]")
        return True
    except ProcessLookupError:
        _get_pid_file().unlink(missing_ok=True)
        console.print("[yellow]守护进程已不存在[/yellow]")
        return False
    except PermissionError:
        console.print("[red]权限不足，无法停止守护进程[/red]")
        return False
