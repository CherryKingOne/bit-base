"""多语言支持"""

from __future__ import annotations

import json
from pathlib import Path

# 支持的语言
SUPPORTED_LANGUAGES = {
    "zh": "中文",
    "en": "English",
    "ja": "日本語",
    "ko": "한국어",
    "fr": "Français",
    "de": "Deutsch",
    "ru": "Русский",
}

# 语言简写映射
LANG_ALIASES = {
    "chinese": "zh",
    "cn": "zh",
    "english": "en",
    "japanese": "ja",
    "jp": "ja",
    "korean": "ko",
    "kr": "ko",
    "french": "fr",
    "france": "fr",
    "german": "de",
    "deutsch": "de",
    "russian": "ru",
    "ru": "ru",
}

# 默认语言
DEFAULT_LANGUAGE = "en"

# 当前语言（临时）
_current_language: str | None = None

# 配置文件路径
_config_file = Path.home() / ".bit" / "config.json"


def get_language() -> str:
    """获取当前语言"""
    global _current_language

    # 临时语言优先
    if _current_language:
        return _current_language

    # 读取配置
    config = _load_config()
    return config.get("language", DEFAULT_LANGUAGE)


def set_language(lang: str, permanent: bool = False) -> None:
    """设置语言"""
    global _current_language

    # 解析语言代码
    lang_code = _resolve_lang(lang)

    if permanent:
        # 永久设置
        config = _load_config()
        config["language"] = lang_code
        _save_config(config)
        _current_language = None  # 清除临时设置
    else:
        # 临时设置
        _current_language = lang_code


def _resolve_lang(lang: str) -> str:
    """解析语言代码"""
    lang = lang.lower().strip()

    # 直接匹配
    if lang in SUPPORTED_LANGUAGES:
        return lang

    # 别名匹配
    if lang in LANG_ALIASES:
        return LANG_ALIASES[lang]

    raise ValueError(f"不支持的语言: {lang}\n支持: {', '.join(SUPPORTED_LANGUAGES.keys())}")


def _load_config() -> dict:
    """加载配置"""
    if _config_file.exists():
        try:
            return json.loads(_config_file.read_text())
        except Exception:
            pass
    return {}


def _save_config(config: dict) -> None:
    """保存配置"""
    _config_file.parent.mkdir(parents=True, exist_ok=True)
    _config_file.write_text(json.dumps(config, indent=2, ensure_ascii=False))
