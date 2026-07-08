"""Server commands: run, ps, stats, stop"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from bit.config import load_config
from bit.i18n.translator import t

console = Console()


def run_cmd(
    model: str = typer.Argument(help="Model name"),
    engine: str = typer.Option("llama.cpp", "--engine", "-e", help="Inference engine"),
    precision: str = typer.Option("q4_k_m", "--precision", "-p", help="Model precision"),
    port: int | None = typer.Option(None, "--port", help="API port"),
    daemon: bool = typer.Option(False, "--daemon", "-D", help="Run in background"),
):
    """Start model inference service"""
    from bit.server.runner import run_model
    config = load_config()
    run_model(config, model, engine, precision, port, daemon)


def ps_cmd():
    """List running models"""
    from bit.server.manager import list_running
    models = list_running()
    if not models:
        console.print(f"[yellow]{t('ps_empty')}[/yellow]")
        return

    table = Table(title=t("ps_title"))
    table.add_column(t("ps_model"), style="cyan")
    table.add_column(t("run_engine"), style="green")
    table.add_column(t("run_port"), style="yellow")
    table.add_column(t("ps_pid"), style="white")
    table.add_column(t("ps_uptime"), style="magenta")
    table.add_column(t("ps_status"), style="green")

    for m in models:
        status_style = "green" if m["status"] == "running" else "red"
        status_key = "ps_running" if m["status"] == "running" else "ps_stopped"
        table.add_row(
            m["name"],
            m["engine"],
            str(m["port"]),
            str(m["pid"]),
            m["uptime"],
            f"[{status_style}]{t(status_key)}[/{status_style}]",
        )

    console.print(table)


def stats_cmd(
    model: str | None = typer.Argument(None, help="Model name (omit for all)"),
):
    """Show model metrics"""
    from bit.server.manager import get_stats
    stats_data = get_stats(model)
    if not stats_data:
        console.print(f"[yellow]{t('stats_empty')}[/yellow]")
        return

    for s in stats_data:
        console.print(Panel(
            f"[bold]{t('run_engine')}:[/bold] {s['engine']}\n"
            f"[bold]{t('run_port')}:[/bold] {s['port']}\n"
            f"[bold]{t('ps_pid')}:[/bold] {s['pid']}\n"
            f"[bold]{t('ps_status')}:[/bold] {s['status']}\n"
            f"[bold]{t('ps_uptime')}:[/bold] {s['uptime']}\n"
            f"[bold]{t('stats_tokens_per_sec')}:[/bold] {s['tokens_per_sec']}\n"
            f"[bold]{t('stats_first_token')}:[/bold] {s['first_token_ms']}ms\n"
            f"[bold]{t('stats_vram')}:[/bold] {s['vram']}",
            title=t("stats_title", s['name']),
        ))


def stop_cmd(
    model: str | None = typer.Argument(None, help="Model name"),
    all: bool = typer.Option(False, "--all", help="Stop all models"),
):
    """Stop model service"""
    from bit.server.manager import stop_model, stop_all
    if all:
        stop_all()
        console.print(f"[green]{t('stop_all')}[/green]")
    elif model:
        stop_model(model)
    else:
        console.print(f"[red]{t('stop_hint')}[/red]")
