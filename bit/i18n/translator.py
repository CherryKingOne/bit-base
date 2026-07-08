"""语言消息访问器"""

from __future__ import annotations

from bit.i18n import get_language
from bit.i18n.zh import MESSAGES as ZH_MESSAGES
from bit.i18n.en import MESSAGES as EN_MESSAGES

# 语言包注册
_LANG_PACKS = {
    "zh": ZH_MESSAGES,
    "en": EN_MESSAGES,
}


def t(key: str, *args) -> str:
    """获取翻译文本

    Args:
        key: 消息键名
        *args: 格式化参数

    Returns:
        翻译后的文本
    """
    lang = get_language()
    messages = _LANG_PACKS.get(lang, EN_MESSAGES)

    msg = messages.get(key, key)

    if args:
        try:
            msg = msg.format(*args)
        except (IndexError, KeyError):
            pass

    return msg


def register_lang(lang_code: str, messages: dict) -> None:
    """注册语言包"""
    _LANG_PACKS[lang_code] = messages
