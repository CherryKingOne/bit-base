"""CLI 入口"""

from __future__ import annotations

import os
import sys
import json


def _load_language() -> str:
    """在 typer 处理前加载语言"""
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg in ("--lang", "-l") and i + 1 < len(args):
            return _resolve(args[i + 1])
        if arg.startswith("--lang="):
            return _resolve(arg.split("=", 1)[1])
        if arg == "--init" and i + 1 < len(args):
            return _resolve(args[i + 1])
        if arg.startswith("--init="):
            return _resolve(arg.split("=", 1)[1])

    config_file = os.path.expanduser("~/.bit/config.json")
    if os.path.exists(config_file):
        try:
            config = json.loads(open(config_file).read())
            return config.get("language", "en")
        except Exception:
            pass
    return "en"


def _resolve(lang: str) -> str:
    aliases = {"chinese": "zh", "cn": "zh", "english": "en", "japanese": "ja",
               "jp": "ja", "korean": "ko", "kr": "ko", "french": "fr",
               "france": "fr", "german": "de", "deutsch": "de", "russian": "ru"}
    return aliases.get(lang.lower().strip(), lang.lower().strip())


_lang = _load_language()


# ─── 全语言翻译表 ───

_TR = {
    "zh": {
        "Switch language": "切换语言",
        "Show version": "显示版本",
        "Pull model from HuggingFace": "从 HuggingFace 拉取模型",
        "List downloaded models": "查看已下载模型",
        "Show model details": "查看模型详情",
        "Remove downloaded model": "删除已下载模型",
        "Start model inference service": "启动模型推理服务",
        "List running models": "查看运行中的模型",
        "Show model metrics": "查看模型运行指标",
        "Stop model service": "停止模型服务",
        "Search model marketplace": "搜索模型市场",
        "List available engines": "列出可用引擎",
        "List model categories": "查看模型分类",
        "Daemon process management": "守护进程管理",
        "API key management": "API 密钥管理",
        "Action: status, set, list": "操作: status, set, list",
        "Action: status, stop": "操作: status, stop",
        "Action: create, list, delete": "操作: create, list, delete",
        "Language code": "语言代码",
        "Model name": "模型名称",
        "Search keyword": "搜索关键词",
        "Inference engine": "推理引擎",
        "Model precision": "模型精度",
        "Custom storage path": "自定义存储路径",
        "API port": "API 端口",
        "Run in background": "后台运行",
        "Model name (omit for all)": "模型名称（不指定则显示全部）",
        "Skip confirmation": "跳过确认",
        "Stop all models": "停止所有模型",
        "Category": "分类",
        "Key name": "密钥名称",
        "Key description": "密钥描述",
        "Language (zh/en/ja/ko/fr/de/ru)": "语言 (zh/en/ja/ko/fr/de/ru)",
        "Set default language": "设置默认语言",
        "Multi-Engine Model Inference Platform": "多引擎模型推理平台",
    },
    "ja": {
        "Switch language": "言語を切り替え",
        "Show version": "バージョン表示",
        "Pull model from HuggingFace": "HuggingFaceからモデルを取得",
        "List downloaded models": "ダウンロード済みモデル一覧",
        "Show model details": "モデル詳細表示",
        "Remove downloaded model": "ダウンロード済みモデルを削除",
        "Start model inference service": "モデル推論サービスを開始",
        "List running models": "実行中のモデル一覧",
        "Show model metrics": "モデルメトリクス表示",
        "Stop model service": "モデルサービスを停止",
        "Search model marketplace": "モデルマーケットを検索",
        "List available engines": "利用可能なエンジン一覧",
        "List model categories": "モデルカテゴリ一覧",
        "Daemon process management": "デーモンプロセス管理",
        "API key management": "APIキー管理",
        "Action: status, set, list": "アクション: status, set, list",
        "Action: status, stop": "アクション: status, stop",
        "Action: create, list, delete": "アクション: create, list, delete",
        "Language code": "言語コード",
        "Model name": "モデル名",
        "Search keyword": "検索キーワード",
        "Inference engine": "推論エンジン",
        "Model precision": "モデル精度",
        "Custom storage path": "カスタムストレージパス",
        "API port": "APIポート",
        "Run in background": "バックグラウンドで実行",
        "Model name (omit for all)": "モデル名（省略時は全て表示）",
        "Skip confirmation": "確認をスキップ",
        "Stop all models": "全てのモデルを停止",
        "Category": "カテゴリ",
        "Key name": "キー名",
        "Key description": "キーの説明",
        "Language (zh/en/ja/ko/fr/de/ru)": "言語 (zh/en/ja/ko/fr/de/ru)",
        "Set default language": "デフォルト言語を設定",
        "Multi-Engine Model Inference Platform": "マルチエンジンモデル推論プラットフォーム",
    },
    "ko": {
        "Switch language": "언어 전환",
        "Show version": "버전 표시",
        "Pull model from HuggingFace": "HuggingFace에서 모델 가져오기",
        "List downloaded models": "다운로드한 모델 목록",
        "Show model details": "모델 상세 정보",
        "Remove downloaded model": "다운로드한 모델 삭제",
        "Start model inference service": "모델 추론 서비스 시작",
        "List running models": "실행 중인 모델 목록",
        "Show model metrics": "모델 메트릭 표시",
        "Stop model service": "모델 서비스 중지",
        "Search model marketplace": "모델 마켓플레이스 검색",
        "List available engines": "사용 가능한 엔진 목록",
        "List model categories": "모델 카테고리 목록",
        "Daemon process management": "데몬 프로세스 관리",
        "API key management": "API 키 관리",
        "Action: status, set, list": "작업: status, set, list",
        "Action: status, stop": "작업: status, stop",
        "Action: create, list, delete": "작업: create, list, delete",
        "Language code": "언어 코드",
        "Model name": "모델 이름",
        "Search keyword": "검색 키워드",
        "Inference engine": "추론 엔진",
        "Model precision": "모델 정밀도",
        "Custom storage path": "사용자 지정 저장 경로",
        "API port": "API 포트",
        "Run in background": "백그라운드에서 실행",
        "Model name (omit for all)": "모델 이름 (생략 시 전체 표시)",
        "Skip confirmation": "확인 건너뛰기",
        "Stop all models": "모든 모델 중지",
        "Category": "카테고리",
        "Key name": "키 이름",
        "Key description": "키 설명",
        "Language (zh/en/ja/ko/fr/de/ru)": "언어 (zh/en/ja/ko/fr/de/ru)",
        "Set default language": "기본 언어 설정",
        "Multi-Engine Model Inference Platform": "멀티 엔진 모델 추론 플랫폼",
    },
    "fr": {
        "Switch language": "Changer de langue",
        "Show version": "Afficher la version",
        "Pull model from HuggingFace": "Télécharger le modèle depuis HuggingFace",
        "List downloaded models": "Lister les modèles téléchargés",
        "Show model details": "Afficher les détails du modèle",
        "Remove downloaded model": "Supprimer le modèle téléchargé",
        "Start model inference service": "Démarrer le service d'inférence",
        "List running models": "Lister les modèles en cours d'exécution",
        "Show model metrics": "Afficher les métriques du modèle",
        "Stop model service": "Arrêter le service modèle",
        "Search model marketplace": "Rechercher sur le marketplace de modèles",
        "List available engines": "Lister les moteurs disponibles",
        "List model categories": "Lister les catégories de modèles",
        "Daemon process management": "Gestion du processus démon",
        "API key management": "Gestion des clés API",
        "Action: status, set, list": "Action: status, set, list",
        "Action: status, stop": "Action: status, stop",
        "Action: create, list, delete": "Action: create, list, delete",
        "Language code": "Code de langue",
        "Model name": "Nom du modèle",
        "Search keyword": "Mot-clé de recherche",
        "Inference engine": "Moteur d'inférence",
        "Model precision": "Précision du modèle",
        "Custom storage path": "Chemin de stockage personnalisé",
        "API port": "Port API",
        "Run in background": "Exécuter en arrière-plan",
        "Model name (omit for all)": "Nom du modèle (omettre pour tous)",
        "Skip confirmation": "Ignorer la confirmation",
        "Stop all models": "Arrêter tous les modèles",
        "Category": "Catégorie",
        "Key name": "Nom de la clé",
        "Key description": "Description de la clé",
        "Language (zh/en/ja/ko/fr/de/ru)": "Langue (zh/en/ja/ko/fr/de/ru)",
        "Set default language": "Définir la langue par défaut",
        "Multi-Engine Model Inference Platform": "Plateforme d'inférence multi-moteur",
    },
    "de": {
        "Switch language": "Sprache wechseln",
        "Show version": "Version anzeigen",
        "Pull model from HuggingFace": "Modell von HuggingFace herunterladen",
        "List downloaded models": "Heruntergeladene Modelle auflisten",
        "Show model details": "Modell-Details anzeigen",
        "Remove downloaded model": "Heruntergeladenes Modell entfernen",
        "Start model inference service": "Modell-Inferenzdienst starten",
        "List running models": "Laufende Modelle auflisten",
        "Show model metrics": "Modellmetriken anzeigen",
        "Stop model service": "Modell-Dienst stoppen",
        "Search model marketplace": "Modell-Marktplatz durchsuchen",
        "List available engines": "Verfügbare Engines auflisten",
        "List model categories": "Modellkategorien auflisten",
        "Daemon process management": "Daemon-Prozessverwaltung",
        "API key management": "API-Schlüsselverwaltung",
        "Action: status, set, list": "Aktion: status, set, list",
        "Action: status, stop": "Aktion: status, stop",
        "Action: create, list, delete": "Aktion: create, list, delete",
        "Language code": "Sprachcode",
        "Model name": "Modellname",
        "Search keyword": "Suchbegriff",
        "Inference engine": "Inferenz-Engine",
        "Model precision": "Modellpräzision",
        "Custom storage path": "Benutzerdefinierter Speicherpfad",
        "API port": "API-Port",
        "Run in background": "Im Hintergrund ausführen",
        "Model name (omit for all)": "Modellname (weglassen für alle)",
        "Skip confirmation": "Bestätigung überspringen",
        "Stop all models": "Alle Modelle stoppen",
        "Category": "Kategorie",
        "Key name": "Schlüsselname",
        "Key description": "Schlüsselbeschreibung",
        "Language (zh/en/ja/ko/fr/de/ru)": "Sprache (zh/en/ja/ko/fr/de/ru)",
        "Set default language": "Standardsprache festlegen",
        "Multi-Engine Model Inference Platform": "Multi-Engine-Modell-Inferenz-Plattform",
    },
    "ru": {
        "Switch language": "Переключить язык",
        "Show version": "Показать версию",
        "Pull model from HuggingFace": "Загрузить модель из HuggingFace",
        "List downloaded models": "Список загруженных моделей",
        "Show model details": "Показать детали модели",
        "Remove downloaded model": "Удалить загруженную модель",
        "Start model inference service": "Запустить сервис инференса",
        "List running models": "Список запущенных моделей",
        "Show model metrics": "Показать метрики модели",
        "Stop model service": "Остановить сервис модели",
        "Search model marketplace": "Поиск на маркетплейсе моделей",
        "List available engines": "Список доступных движков",
        "List model categories": "Список категорий моделей",
        "Daemon process management": "Управление демон-процессом",
        "API key management": "Управление API-ключами",
        "Action: status, set, list": "Действие: status, set, list",
        "Action: status, stop": "Действие: status, stop",
        "Action: create, list, delete": "Действие: create, list, delete",
        "Language code": "Код языка",
        "Model name": "Имя модели",
        "Search keyword": "Ключевое слово",
        "Inference engine": "Движок инференса",
        "Model precision": "Точность модели",
        "Custom storage path": "Пользовательский путь",
        "API port": "Порт API",
        "Run in background": "Запустить в фоне",
        "Model name (omit for all)": "Имя модели (пусто = все)",
        "Skip confirmation": "Пропустить подтверждение",
        "Stop all models": "Остановить все модели",
        "Category": "Категория",
        "Key name": "Имя ключа",
        "Key description": "Описание ключа",
        "Language (zh/en/ja/ko/fr/de/ru)": "Язык (zh/en/ja/ko/fr/de/ru)",
        "Set default language": "Установить язык по умолчанию",
        "Multi-Engine Model Inference Platform": "Платформа инференса моделей с многоязыковыми движками",
    },
}


def t(key: str, *args) -> str:
    """获取翻译

    先查 CLI 帮助文本翻译表（_TR，支持 6 种语言），
    未找到则回退到运行时消息翻译（bit.i18n.translator，支持 zh/en）。
    """
    msg = _TR.get(_lang, {}).get(key)
    if msg is not None:
        if args:
            try:
                msg = msg.format(*args)
            except (IndexError, KeyError):
                pass
        return msg
    # 回退到运行时消息翻译
    from bit.i18n.translator import t as _tr_t
    return _tr_t(key, *args)


# ─── typer 部分 ───

import typer
from bit import __version__
from bit.i18n import SUPPORTED_LANGUAGES, set_language, get_language

app = typer.Typer(
    name="bit",
    help=f"bit — {t('Multi-Engine Model Inference Platform')}",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


@app.callback(invoke_without_command=True)
def main(
    lang: str | None = typer.Option(None, "--lang", "-l", help=t("Language (zh/en/ja/ko/fr/de/ru)")),
    init: str | None = typer.Option(None, "--init", help=t("Set default language")),
):
    """bit — Multi-Engine Model Inference Platform"""
    from bit.logging import setup_logging
    setup_logging()

    if init:
        set_language(init, permanent=True)
        lang_code = get_language()
        from rich.console import Console
        Console().print(f"[green]✓ Default language set: {SUPPORTED_LANGUAGES.get(lang_code, lang_code)}[/green]")
        return

    if lang:
        set_language(lang, permanent=False)


@app.command(name="lang", help=t("Switch language"))
def lang_cmd(
    action: str = typer.Argument("status", help=t("Action: status, set, list")),
    language: str | None = typer.Argument(None, help=t("Language code")),
):
    """Switch language"""
    from rich.console import Console
    from rich.table import Table
    console = Console()

    if action == "status":
        current = get_language()
        console.print(t("lang_current", SUPPORTED_LANGUAGES.get(current, current), current))

    elif action == "set":
        if not language:
            console.print("[red]Please specify language[/red]")
            return
        set_language(language, permanent=True)
        current = get_language()
        console.print(f"[green]{t('lang_switched', SUPPORTED_LANGUAGES.get(current, current), current)}[/green]")

    elif action == "list":
        table = Table(title=t("lang_supported"))
        table.add_column("Code", style="cyan")
        table.add_column("Language", style="white")
        for code, name in SUPPORTED_LANGUAGES.items():
            current = get_language()
            style = "green" if code == current else "white"
            table.add_row(code, f"[{style}]{name}[/{style}]")
        console.print(table)
        console.print(f"\n[dim]{t('lang_hint_init')}[/dim]")

    else:
        console.print(f"[red]{t('daemon_invalid_action')}[/red]")


@app.command(help=t("Show version"))
def version():
    """Show version"""
    from rich.console import Console
    Console().print(f"bit v{__version__}")


@app.command(help=t("Pull model from HuggingFace"))
def pull(
    model: str = typer.Argument(help=t("Model name")),
    engine: str = typer.Option("llama.cpp", "--engine", "-e", help=t("Inference engine")),
    precision: str = typer.Option("q4_k_m", "--precision", "-p", help=t("Model precision")),
    dir: str | None = typer.Option(None, "--dir", "-d", help=t("Custom storage path")),
):
    """Pull model from HuggingFace"""
    from bit.models.downloader import pull_model
    from bit.config import load_config
    pull_model(load_config(), model, engine, precision, dir)


@app.command(name="list", help=t("List downloaded models"))
def list_models():
    """List downloaded models"""
    from bit.models.registry import list_models
    from bit.config import load_config
    from rich.console import Console
    from rich.table import Table
    console = Console()
    models = list_models(load_config())
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


@app.command(help=t("Show model details"))
def info(model: str = typer.Argument(help=t("Model name"))):
    """Show model details"""
    from bit.market.search import get_model_info
    from rich.console import Console
    from rich.panel import Panel
    console = Console()
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


@app.command(help=t("Remove downloaded model"))
def remove(
    model: str = typer.Argument(help=t("Model name")),
    force: bool = typer.Option(False, "--force", "-f", help=t("Skip confirmation")),
):
    """Remove downloaded model"""
    from bit.models.registry import remove_model
    from bit.config import load_config
    remove_model(load_config(), model, force)


@app.command(help=t("Start model inference service"))
def run(
    model: str = typer.Argument(help=t("Model name")),
    engine: str = typer.Option("llama.cpp", "--engine", "-e", help=t("Inference engine")),
    precision: str = typer.Option("q4_k_m", "--precision", "-p", help=t("Model precision")),
    port: int | None = typer.Option(None, "--port", help=t("API port")),
    daemon: bool = typer.Option(False, "--daemon", "-D", help=t("Run in background")),
):
    """Start model inference service"""
    from bit.server.runner import run_model
    from bit.config import load_config
    run_model(load_config(), model, engine, precision, port, daemon)


@app.command(help=t("List running models"))
def ps():
    """List running models"""
    from bit.server.manager import list_running
    from rich.console import Console
    from rich.table import Table
    console = Console()
    models = list_running()
    if not models:
        console.print(f"[yellow]{t('ps_empty')}[/yellow]")
        return
    table = Table(title=t("ps_title"))
    table.add_column(t("ps_model"), style="cyan")
    table.add_column(t("list_engine"), style="green")
    table.add_column(t("run_port"), style="yellow")
    table.add_column(t("ps_pid"), style="white")
    table.add_column(t("ps_uptime"), style="magenta")
    table.add_column(t("ps_status"), style="green")
    for m in models:
        status_style = "green" if m["status"] == "running" else "red"
        status_key = "ps_running" if m["status"] == "running" else "ps_stopped"
        table.add_row(m["name"], m["engine"], str(m["port"]), str(m["pid"]), m["uptime"],
                      f"[{status_style}]{t(status_key)}[/{status_style}]")
    console.print(table)


@app.command(help=t("Show model metrics"))
def stats(
    model: str | None = typer.Argument(None, help=t("Model name (omit for all)")),
):
    """Show model metrics"""
    from bit.server.manager import get_stats
    from rich.console import Console
    from rich.panel import Panel
    console = Console()
    stats_data = get_stats(model)
    if not stats_data:
        console.print(f"[yellow]{t('stats_empty')}[/yellow]")
        return
    for s in stats_data:
        console.print(Panel(
            f"[bold]{t('list_engine')}:[/bold] {s['engine']}\n"
            f"[bold]{t('run_port')}:[/bold] {s['port']}\n"
            f"[bold]{t('ps_pid')}:[/bold] {s['pid']}\n"
            f"[bold]{t('ps_status')}:[/bold] {s['status']}\n"
            f"[bold]{t('ps_uptime')}:[/bold] {s['uptime']}\n"
            f"[bold]{t('stats_tokens_per_sec')}:[/bold] {s['tokens_per_sec']}\n"
            f"[bold]{t('stats_first_token')}:[/bold] {s['first_token_ms']}ms\n"
            f"[bold]{t('stats_vram')}:[/bold] {s['vram']}",
            title=t("stats_title", s['name']),
        ))


@app.command(help=t("Stop model service"))
def stop(
    model: str | None = typer.Argument(None, help=t("Model name")),
    all: bool = typer.Option(False, "--all", help=t("Stop all models")),
):
    """Stop model service"""
    from bit.server.manager import stop_model, stop_all
    from rich.console import Console
    console = Console()
    if all:
        stop_all()
        console.print(f"[green]{t('stop_all')}[/green]")
    elif model:
        stop_model(model)
    else:
        console.print(f"[red]{t('stop_hint')}[/red]")


@app.command(help=t("Search model marketplace"))
def search(
    keyword: str = typer.Argument(help=t("Search keyword")),
    category: str | None = typer.Option(None, "--category", "-c", help=t("Category")),
):
    """Search model marketplace"""
    from bit.market.search import search_models
    from rich.console import Console
    from rich.table import Table
    console = Console()
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


@app.command(help=t("List available engines"))
def engines():
    """List available engines"""
    from bit.engines import list_engines
    from rich.console import Console
    from rich.table import Table
    console = Console()
    table = Table(title=t("engines_title"))
    table.add_column(t("list_engine"), style="cyan")
    table.add_column(t("search_desc"), style="white")
    engine_info = {"llama.cpp": t("engines_llamacpp"), "vllm": t("engines_vllm"), "sglang": t("engines_sglang")}
    for e in list_engines():
        table.add_row(e, engine_info.get(e, ""))
    console.print(table)


@app.command(help=t("List model categories"))
def categories():
    """List model categories"""
    from bit.market.search import list_categories
    from rich.console import Console
    from rich.table import Table
    console = Console()
    table = Table(title=t("categories_title"))
    table.add_column(t("categories_name"), style="cyan")
    table.add_column(t("categories_desc"), style="white")
    table.add_column(t("categories_count"), style="green")
    for c in list_categories():
        table.add_row(c["name"], c["desc"], str(c["count"]))
    console.print(table)


@app.command(help=t("Daemon process management"))
def daemon(
    action: str = typer.Argument("status", help=t("Action: status, stop")),
):
    """Daemon process management"""
    from bit.server.daemon import is_daemon_running, get_daemon_pid, stop_daemon
    from rich.console import Console
    console = Console()
    if action == "status":
        if is_daemon_running():
            console.print(f"[green]{t('daemon_running', get_daemon_pid())}[/green]")
        else:
            console.print(f"[yellow]{t('daemon_not_running')}[/yellow]")
    elif action == "stop":
        stop_daemon()
    else:
        console.print(f"[red]{t('daemon_invalid_action')}[/red]")


@app.command(help=t("API key management"))
def apikey(
    action: str = typer.Argument("list", help=t("Action: create, list, delete")),
    name: str | None = typer.Option(None, "--name", "-n", help=t("Key name")),
    description: str | None = typer.Option(None, "--desc", help=t("Key description")),
):
    """API key management"""
    from bit.server.auth import api_key_manager
    from rich.console import Console
    from rich.table import Table
    console = Console()
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


if __name__ == "__main__":
    app()
