"""Model commands: pull, list, info, remove"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from bit.config import load_config
from bit.i18n.translator import t

console = Console()


def pull_cmd(
    model: str = typer.Argument(help="Model name"),
    engine: str = typer.Option("llama.cpp", "--engine", "-e", help="Inference engine"),
    precision: str = typer.Option("q4_k_m", "--precision", "-p", help="Model precision"),
    dir: str | None = typer.Option(None, "--dir", "-d", help="Custom storage path"),
):
    """Pull model from HuggingFace"""
    from bit.models.downloader import pull_model
    config = load_config()
    pull_model(config, model, engine, precision, dir)


def list_cmd():
    """List downloaded models"""
    from bit.models.registry import list_models
    config = load_config()
    models = list_models(config)

    if not models:
        console.print(f"[yellow]{t('list_empty')}[/yellow]")
        return

    table = Table(title=t("list_title"))
    table.add_column(t("list_name"), style="cyan")
    table.add_column(t("list_engine"), style="green")
    table.add_column(t("list_precision"), style="magenta")
    table.add_column(t("list_size"), style="white")

    for m in models:
        table.add_row(m["name"], m["engine"], m["precision"], m["size"])

    console.print(table)


def info_cmd(model: str = typer.Argument(help="Model name")):
    """Show model details"""
    from bit.market.search import get_model_info
    detail = get_model_info(model)
    if not detail:
        console.print(f"[red]{t('info_not_found', model)}[/red]")
        return

    console.print(Panel(
        f"[cyan]{detail['name']}[/cyan]\n"
        f"{t('info_downloads')}: {detail['downloads']:,}  {t('info_likes')}: {detail['likes']}\n"
        f"{t('info_engines')}: {', '.join(detail['engines'])}\n"
        f"{t('info_total_size')}: {detail['total_size']}\n\n"
        f"[dim]{detail['desc']}[/dim]",
        title=t("info_title"),
    ))

    if detail["files"]:
        console.print(f"\n[bold]{t('info_files')}:[/bold]")
        table = Table(show_header=False, show_lines=False)
        table.add_column("Name", style="cyan")
        table.add_column("Size", style="white")
        for f in detail["files"][:10]:
            table.add_row(f["name"], f["size"])
        if len(detail["files"]) > 10:
            table.add_row(f"... {len(detail['files']) - 10} more files", "")
        console.print(table)


def remove_cmd(
    model: str = typer.Argument(help="Model name"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Remove downloaded model"""
    from bit.models.registry import remove_model
    config = load_config()
    remove_model(config, model, force)
