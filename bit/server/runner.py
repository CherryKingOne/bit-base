"""模型运行器 — 启动推理服务"""

from __future__ import annotations

import uvicorn
from rich.console import Console

from bit.config import BitConfig
from bit.engines import get_engine
from bit.server.manager import (
    register_model,
    unregister_model,
    _find_free_port,
    is_port_available,
)

console = Console()


def run_model(
    config: BitConfig,
    model_name: str,
    engine_name: str,
    precision: str,
    port: int | None = None,
    daemon: bool = False,
) -> None:
    """启动模型推理服务"""
    from bit.models.registry import _find_model

    # 查找模型
    model_dir = _find_model(config, model_name)
    if not model_dir:
        console.print(f"[red]未找到模型: {model_name}[/red]")
        console.print("[yellow]请先使用 bit pull 下载模型[/yellow]")
        return

    # 分配端口
    if port is None:
        port = _find_free_port()
    else:
        if not is_port_available(port):
            console.print(f"[red]端口 {port} 已被占用[/red]")
            console.print("[yellow]请指定其他端口或不指定以自动分配[/yellow]")
            return

    console.print(f"[cyan]正在启动 {model_name}...[/cyan]")
    console.print(f"  引擎: {engine_name}")
    console.print(f"  精度: {precision}")
    console.print(f"  端口: {port}")

    # 初始化引擎
    try:
        engine = get_engine(engine_name)
        engine.load_model(model_dir, precision, port=port)
    except FileNotFoundError as e:
        console.print(f"[red]模型文件错误: {e}[/red]")
        return
    except ValueError as e:
        console.print(f"[red]引擎错误: {e}[/red]")
        return
    except Exception as e:
        console.print(f"[red]启动失败: {e}[/red]")
        return

    # 设置全局引擎和模型名
    import bit.server.app as app_module
    app_module._engine = engine
    app_module._model_name = model_name

    # 记录运行状态
    import os
    register_model(model_name, engine_name, port, os.getpid())

    console.print(f"[green]✓ {model_name} 已启动[/green]")
    console.print()
    console.print("[bold]可用 API 端点:[/bold]")
    console.print(f"  OpenAI:     http://localhost:{port}/v1/chat/completions")
    console.print(f"  Anthropic:  http://localhost:{port}/v1/messages")
    console.print(f"  Bedrock:    http://localhost:{port}/bedrock/converse")
    console.print(f"  Codex:      http://localhost:{port}/v1/responses")
    console.print()

    if daemon:
        # 后台模式
        from bit.server.daemon import daemonize
        daemonize()
        console.print("[dim]已切换到后台运行[/dim]")
        console.print(f"[dim]日志: ~/.bit/logs/bit.log[/dim]")

    console.print("[dim]按 Ctrl+C 停止[/dim]")

    # 启动 API 服务
    try:
        uvicorn.run(app_module.app, host="0.0.0.0", port=port, log_level="info")
    except KeyboardInterrupt:
        engine.unload()
        unregister_model(model_name)
        console.print(f"\n[yellow]{model_name} 已停止[/yellow]")
