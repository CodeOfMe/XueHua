"""Language registry for Xuehua.

Centralizes metadata for every supported study language and every supported
UI language. Decouples the rest of the codebase from Japanese-specific
assumptions (JLPT levels, furigana, etc.) so the same pipeline works for
English, French, German, Spanish, Portuguese, Italian, Russian, Korean,
Chinese and Japanese.

A "study language" is the language the user is learning. A "UI language" is
the language the interface is rendered in. They are independent: a Chinese
speaker can learn French with a Chinese UI, or an English speaker can learn
Japanese with an English UI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class LanguageInfo:
    """Metadata for a studyable language."""

    code: str
    """ISO 639-1 code, e.g. 'ja', 'en', 'fr'."""

    name_zh: str
    """Chinese display name, e.g. '日语'."""

    name_en: str
    """English display name, e.g. 'Japanese'."""

    endonym: str
    """Native name, e.g. '日本語', 'English', 'Français'."""

    levels: List[str]
    """Proficiency level IDs, ordered beginner → advanced. Empty = single track."""

    level_labels: Dict[str, str]
    """Display label per level id (Chinese). Falls back to the id itself."""

    script: str
    """Primary script hint: 'kanji_kana', 'latin', 'cyrillic', 'hangul', 'hanzi'."""

    annotator: str
    """Which annotator backend to use: 'japanese', 'chinese', 'korean', 'latin', 'cyrillic'."""

    has_furigana: bool
    """Whether furigana-style reading aids apply."""

    has_romaji: bool
    """Whether a romanization layer applies (romaji/pinyin/romaja/romanization)."""

    default_level: str = ""
    """Initial level; empty means levels[0] or ''."""

    extra: Dict[str, str] = field(default_factory=dict)
    """Free-form per-language metadata (e.g. transliteration system)."""


LANGUAGES: Dict[str, LanguageInfo] = {}


def _register(info: LanguageInfo) -> LanguageInfo:
    LANGUAGES[info.code] = info
    return info


_register(LanguageInfo(
    code="ja",
    name_zh="日语", name_en="Japanese", endonym="日本語",
    levels=["N5", "N4", "N3", "N2", "N1"],
    level_labels={
        "N5": "N5 入门", "N4": "N4 初级", "N3": "N3 中级",
        "N2": "N2 中高级", "N1": "N1 高级",
    },
    script="kanji_kana",
    annotator="japanese",
    has_furigana=True,
    has_romaji=True,
    default_level="N5",
    extra={"romaji_systems": "hepburn,nippon,passport"},
))

_register(LanguageInfo(
    code="zh",
    name_zh="中文", name_en="Chinese", endonym="中文",
    levels=["HSK1", "HSK2", "HSK3", "HSK4", "HSK5", "HSK6"],
    level_labels={
        "HSK1": "HSK 1 入门", "HSK2": "HSK 2 基础", "HSK3": "HSK 3 初级",
        "HSK4": "HSK 4 中级", "HSK5": "HSK 5 中高级", "HSK6": "HSK 6 高级",
    },
    script="hanzi",
    annotator="chinese",
    has_furigana=False,
    has_romaji=True,
    default_level="HSK1",
    extra={"romaji_label": "拼音", "romaji_systems": "pinyin"},
))

_register(LanguageInfo(
    code="en",
    name_zh="英语", name_en="English", endonym="English",
    levels=["A1", "A2", "B1", "B2", "C1", "C2"],
    level_labels={
        "A1": "A1 入门", "A2": "A2 基础", "B1": "B1 中级",
        "B2": "B2 中高级", "C1": "C1 高级", "C2": "C2 精通",
    },
    script="latin",
    annotator="latin",
    has_furigana=False,
    has_romaji=False,
    default_level="A1",
))

_register(LanguageInfo(
    code="ko",
    name_zh="韩语", name_en="Korean", endonym="한국어",
    levels=["TOPIK1", "TOPIK2", "TOPIK3", "TOPIK4", "TOPIK5", "TOPIK6"],
    level_labels={
        "TOPIK1": "TOPIK 1 入门", "TOPIK2": "TOPIK 2 基础",
        "TOPIK3": "TOPIK 3 初级", "TOPIK4": "TOPIK 4 中级",
        "TOPIK5": "TOPIK 5 高级", "TOPIK6": "TOPIK 6 精通",
    },
    script="hangul",
    annotator="korean",
    has_furigana=False,
    has_romaji=True,
    default_level="TOPIK1",
    extra={"romaji_label": "罗马音", "romaji_systems": "rr"},
))

_register(LanguageInfo(
    code="fr",
    name_zh="法语", name_en="French", endonym="Français",
    levels=["A1", "A2", "B1", "B2", "C1", "C2"],
    level_labels={
        "A1": "A1 入门", "A2": "A2 基础", "B1": "B1 中级",
        "B2": "B2 中高级", "C1": "C1 高级", "C2": "C2 精通",
    },
    script="latin",
    annotator="latin",
    has_furigana=False,
    has_romaji=False,
    default_level="A1",
))

_register(LanguageInfo(
    code="de",
    name_zh="德语", name_en="German", endonym="Deutsch",
    levels=["A1", "A2", "B1", "B2", "C1", "C2"],
    level_labels={
        "A1": "A1 入门", "A2": "A2 基础", "B1": "B1 中级",
        "B2": "B2 中高级", "C1": "C1 高级", "C2": "C2 精通",
    },
    script="latin",
    annotator="latin",
    has_furigana=False,
    has_romaji=False,
    default_level="A1",
))

_register(LanguageInfo(
    code="es",
    name_zh="西班牙语", name_en="Spanish", endonym="Español",
    levels=["A1", "A2", "B1", "B2", "C1", "C2"],
    level_labels={
        "A1": "A1 入门", "A2": "A2 基础", "B1": "B1 中级",
        "B2": "B2 中高级", "C1": "C1 高级", "C2": "C2 精通",
    },
    script="latin",
    annotator="latin",
    has_furigana=False,
    has_romaji=False,
    default_level="A1",
))

_register(LanguageInfo(
    code="pt",
    name_zh="葡萄牙语", name_en="Portuguese", endonym="Português",
    levels=["A1", "A2", "B1", "B2", "C1", "C2"],
    level_labels={
        "A1": "A1 入门", "A2": "A2 基础", "B1": "B1 中级",
        "B2": "B2 中高级", "C1": "C1 高级", "C2": "C2 精通",
    },
    script="latin",
    annotator="latin",
    has_furigana=False,
    has_romaji=False,
    default_level="A1",
))

_register(LanguageInfo(
    code="it",
    name_zh="意大利语", name_en="Italian", endonym="Italiano",
    levels=["A1", "A2", "B1", "B2", "C1", "C2"],
    level_labels={
        "A1": "A1 入门", "A2": "A2 基础", "B1": "B1 中级",
        "B2": "B2 中高级", "C1": "C1 高级", "C2": "C2 精通",
    },
    script="latin",
    annotator="latin",
    has_furigana=False,
    has_romaji=False,
    default_level="A1",
))

_register(LanguageInfo(
    code="ru",
    name_zh="俄语", name_en="Russian", endonym="Русский",
    levels=["A1", "A2", "B1", "B2", "C1", "C2"],
    level_labels={
        "A1": "A1 入门", "A2": "A2 基础", "B1": "B1 中级",
        "B2": "B2 中高级", "C1": "C1 高级", "C2": "C2 精通",
    },
    script="cyrillic",
    annotator="cyrillic",
    has_furigana=False,
    has_romaji=True,
    default_level="A1",
    extra={"romaji_label": "拉丁转写", "romaji_systems": "ala"},
))


def get_language(code: str) -> Optional[LanguageInfo]:
    """Return LanguageInfo for a code, or None."""
    return LANGUAGES.get(code)


def list_languages() -> List[LanguageInfo]:
    """Return all registered study languages, ordered by Chinese name."""
    return sorted(LANGUAGES.values(), key=lambda i: i.name_zh)


def get_levels(code: str) -> List[str]:
    info = get_language(code)
    return list(info.levels) if info else []


def get_level_labels(code: str) -> Dict[str, str]:
    info = get_language(code)
    return dict(info.level_labels) if info else {}


def default_level(code: str) -> str:
    info = get_language(code)
    if not info:
        return ""
    return info.default_level or (info.levels[0] if info.levels else "")


def is_supported(code: str) -> bool:
    return code in LANGUAGES


UI_LANGUAGES: Dict[str, Dict[str, str]] = {
    "zh": {"name": "中文", "name_en": "Chinese", "endonym": "中文"},
    "en": {"name": "英文", "name_en": "English", "endonym": "English"},
    "ja": {"name": "日语", "name_en": "Japanese", "endonym": "日本語"},
    "ko": {"name": "韩语", "name_en": "Korean", "endonym": "한국어"},
    "fr": {"name": "法语", "name_en": "French", "endonym": "Français"},
    "de": {"name": "德语", "name_en": "German", "endonym": "Deutsch"},
    "es": {"name": "西班牙语", "name_en": "Spanish", "endonym": "Español"},
    "pt": {"name": "葡萄牙语", "name_en": "Portuguese", "endonym": "Português"},
    "it": {"name": "意大利语", "name_en": "Italian", "endonym": "Italiano"},
    "ru": {"name": "俄语", "name_en": "Russian", "endonym": "Русский"},
}


def list_ui_languages() -> List[Dict[str, str]]:
    return [
        {"code": code, **meta}
        for code, meta in UI_LANGUAGES.items()
    ]


def is_ui_supported(code: str) -> bool:
    return code in UI_LANGUAGES