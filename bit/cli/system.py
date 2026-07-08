"""System commands: daemon, apikey"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from bit.i18n.translator import t

console = Console()


def daemon_cmd(
    action: str = typer.Argument(help="Action: status, stop"),
):
    """Daemon process management"""
    from bit.server.daemon import is_daemon_running, get_daemon_pid, stop_daemon

    if action == "status":
        if is_daemon_running():
            pid = get_daemon_pid()
            console.print(f"[green]{t('daemon_running', pid)}[/green]")
        else:
            console.print(f"[yellow]{t('daemon_not_running')}[/yellow]")
    elif action == "stop":
        stop_daemon()
    else:
        console.print(f"[red]{t('daemon_invalid_action')}[/red]")


def apikey_cmd(
    action: str = typer.Argument(help="Action: create, list, delete"),
    name: str | None = typer.Option(None, "--name", "-n", help="Key name"),
    description: str | None = typer.Option(None, "--desc", help="Key description"),
):
    """API key management"""
    from bit.server.auth import api_key_manager

    if action == "create":
        if not name:
            console.print(f"[red]{t('apikey_hint_name')}[/red]")
            return
        key = api_key_manager.create_key(name, description or "")
        console.print(f"[green]{t('apikey_create')}[/green]")
        console.print(f"\n[bold]{t('apikey_key')}:[/bold] {key}")
        console.print(f"[yellow]{t('apikey_save_hint')}[/yellow]")

    elif action == "list":
        keys = api_key_manager.list_keys()
        if not keys:
            console.print(f"[yellow]{t('apikey_list_empty')}[/yellow]")
            return

        table = Table(title=t("apikey_list_title"))
        table.add_column(t("apikey_name"), style="cyan")
        table.add_column(t("apikey_desc"), style="white")
        table.add_column(t("apikey_created"), style="green")
        table.add_column(t("apikey_status"), style="magenta")

        for k in keys:
            from datetime import datetime
            created = datetime.fromtimestamp(k["created_at"]).strftime("%Y-%m-%d %H:%M")
            status_key = "apikey_active" if k["active"] else "apikey_revoked"
            table.add_row(k["name"], k["description"], created, t(status_key))

        console.print(table)

    elif action == "delete":
        if not name:
            console.print(f"[red]{t('apikey_hint_name')}[/red]")
            return
        if api_key_manager.delete_key(name):
            console.print(f"[green]{t('apikey_deleted', name)}[/green]")
        else:
            console.print(f"[red]{t('apikey_not_found', name)}[/red]")

    else:
        console.print(f"[red]{t('apikey_invalid_action')}[/red]")
