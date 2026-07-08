"""支持多语言的 Typer"""

from __future__ import annotations

import os
import typer
from typer.models import TyperInfo
from click import Group


def _get_lang_from_args() -> str:
    """从命令行参数或配置文件获取语言（在 typer 处理前）"""
    # 先检查命令行参数
    args = sys.argv[1:] if 'sys' in dir() else []

    # 检查 --lang 参数
    for i, arg in enumerate(args):
        if arg in ("--lang", "-l") and i + 1 < len(args):
            return _resolve_lang(args[i + 1])
        if arg.startswith("--lang="):
            return _resolve_lang(arg.split("=", 1)[1])
        if arg.startswith("-l="):
            return _resolve_lang(arg.split("=", 1)[1])

    # 检查 --init 参数（设置默认语言）
    for i, arg in enumerate(args):
        if arg == "--init" and i + 1 < len(args):
            return _resolve_lang(args[i + 1])
        if arg.startswith("--init="):
            return _resolve_lang(arg.split("=", 1)[1])

    # 从配置文件读取
    config_file = os.path.expanduser("~/.bit/config.json")
    if os.path.exists(config_file):
        try:
            import json
            config = json.loads(open(config_file).read())
            return config.get("language", "en")
        except Exception:
            pass

    return "en"


def _resolve_lang(lang: str) -> str:
    """解析语言代码"""
    aliases = {
        "chinese": "zh", "cn": "zh",
        "english": "en",
        "japanese": "ja", "jp": "ja",
        "korean": "ko", "kr": "ko",
        "french": "fr", "france": "fr",
        "german": "de", "deutsch": "de",
        "russian": "ru",
    }
    return aliases.get(lang.lower().strip(), lang.lower().strip())


import sys

# 在模块加载时就确定语言
_current_lang = _get_lang_from_args()


def _translate(text: str) -> str:
    """翻译文本"""
    if not text:
        return text

    lang = _current_lang
    if lang == "en":
        return text

    translations = {
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
    }

    return translations.get(lang, {}).get(text, text)


class I18nGroup(Group):
    """支持多语言的 Group"""

    def format_help(self, ctx, formatter):
        """Format help with translation"""
        self.help = _translate(self.help or "")
        self.short_help = _translate(self.short_help or "")

        for cmd in self.commands.values():
            cmd.help = _translate(cmd.help or "")
            cmd.short_help = _translate(cmd.short_help or "")

        super().format_help(ctx, formatter)
