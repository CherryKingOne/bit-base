"""Market commands: search, engines, categories"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from bit.i18n.translator import t

console = Console()


def search_cmd(
    keyword: str = typer.Argument(help="Search keyword"),
    category: str | None = typer.Option(None, "--category", "-c", help="Category"),
):
    """Search model marketplace"""
    from bit.market.search import search_models
    results = search_models(keyword, category=category)
    if not results:
        console.print(f"[yellow]{t('search_empty')}[/yellow]")
        return

    table = Table(title=t("search_title", keyword))
    table.add_column(t("search_name"), style="cyan")
    table.add_column(t("search_desc"), style="white")
    table.add_column(t("search_engine"), style="green")
    table.add_column(t("search_size"), style="magenta")

    for r in results:
        table.add_row(r["name"], r.get("desc", ""), r["engine"], r["size"])

    console.print(table)
    console.print(f"\n[dim]{t('search_hint')}[/dim]")


def engines_cmd():
    """List available engines"""
    from bit.engines import list_engines
    table = Table(title=t("engines_title"))
    table.add_column(t("list_engine"), style="cyan")
    table.add_column(t("search_desc"), style="white")

    engine_info = {
        "llama.cpp": t("engines_llamacpp"),
        "vllm": t("engines_vllm"),
        "sglang": t("engines_sglang"),
    }

    for e in list_engines():
        table.add_row(e, engine_info.get(e, ""))

    console.print(table)


def categories_cmd():
    """List model categories"""
    from bit.market.search import list_categories
    table = Table(title=t("categories_title"))
    table.add_column(t("categories_name"), style="cyan")
    table.add_column(t("categories_desc"), style="white")
    table.add_column(t("categories_count"), style="green")

    for c in list_categories():
        console.print(f"[cyan]{c['name']}[/cyan]")
        table.add_row(c["name"], c["desc"], str(c["count"]))

    console.print(table)
