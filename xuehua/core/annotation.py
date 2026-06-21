"""Multi-language annotation dispatcher.

Provides a single `annotate_text` entry point that delegates to the right
backend per study language. Japanese keeps its furigana/romaji pipeline;
Chinese adds pinyin; Korean adds romaja; Latin/Cyrillic pass through with
optional transliteration for Russian.

This decouples learning.py and app.py from the Japanese-only module.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .languages import LanguageInfo, get_language


@dataclass
class AnnotatedToken:
    """A single annotated token, language-agnostic."""
    surface: str
    lemma: str = ""
    pos: str = ""
    reading: str = ""
    is_kanji: bool = False
    is_kana: bool = False
    is_mixed: bool = False


@dataclass
class AnnotatedText:
    """Annotated text for any language."""
    original: str
    tokens: List[AnnotatedToken] = field(default_factory=list)
    html_ruby: str = ""
    html_romaji: str = ""
    plain_reading: str = ""

    def to_api_dict(self) -> dict:
        return {
            "original": self.original,
            "html_ruby": self.html_ruby,
            "html_romaji": self.html_romaji,
            "plain_reading": self.plain_reading,
            "tokens": [{
                "surface": t.surface,
                "reading": t.reading,
                "pos": t.pos,
                "is_kanji": t.is_kanji,
                "is_kana": t.is_kana,
                "is_mixed": t.is_mixed,
            } for t in self.tokens],
        }


_KANA_RANGE = re.compile(r"[\u3040-\u309f\u30a0-\u30ff\uFF65-\uFF9f]")
_HANZI_RANGE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]")
_HANGUL_RANGE = re.compile(r"[\uac00-\ud7af\u1100-\u11ff\u3130-\u318f]")
_CYRILLIC_RANGE = re.compile(r"[\u0400-\u04ff]")


def _annotate_japanese(text: str, show_furigana: bool, show_romaji: bool,
                       learned_chars: Optional[set]) -> AnnotatedText:
    from .japanese import annotate_text as _ja_annotate, tokenize as _ja_tokenize
    result = _ja_annotate(text, show_furigana=show_furigana, show_romaji=show_romaji,
                         learned_kanji=learned_chars)
    tokens = [
        AnnotatedToken(
            surface=t.surface, lemma=t.lemma, pos=t.pos, reading=t.reading,
            is_kanji=t.is_kanji, is_kana=t.is_kana, is_mixed=t.is_mixed,
        )
        for t in result.tokens
    ]
    return AnnotatedText(
        original=result.original, tokens=tokens,
        html_ruby=result.html_ruby, html_romaji=result.html_romaji,
        plain_reading=result.plain_reading,
    )


def _pinyin(text: str) -> str:
    try:
        from pypinyin import pinyin as _py, Style
        pieces = _py(text, style=Style.TONE)
        return " ".join(item[0] for item in pieces if item and item[0])
    except Exception:
        return ""


def _annotate_chinese(text: str, show_furigana: bool, show_romaji: bool,
                      learned_chars: Optional[set]) -> AnnotatedText:
    """Chinese annotation: pinyin over hanzi as ruby, plain pinyin as reading."""
    if learned_chars is None:
        learned_chars = set()

    tokens: List[AnnotatedToken] = []
    ruby_parts: List[str] = []
    reading_parts: List[str] = []
    pinyin_parts: List[str] = []

    for ch in text:
        if _HANZI_RANGE.match(ch):
            py = _pinyin(ch)
            tokens.append(AnnotatedToken(
                surface=ch, reading=py, pos="hanzi",
                is_kanji=True,
            ))
            if show_furigana and ch not in learned_chars and py:
                ruby_parts.append(f"<ruby>{ch}<rp>(</rp><rt>{py}</rt><rp>)</rp></ruby>")
            else:
                ruby_parts.append(ch)
            reading_parts.append(py or ch)
            if py:
                pinyin_parts.append(py)
        else:
            tokens.append(AnnotatedToken(surface=ch))
            ruby_parts.append(ch)
            reading_parts.append(ch)
            if ch.strip():
                pinyin_parts.append(ch)

    return AnnotatedText(
        original=text,
        tokens=tokens,
        html_ruby="".join(ruby_parts),
        html_romaji=" ".join(pinyin_parts) if show_romaji else "",
        plain_reading="".join(reading_parts),
    )


def _hangul_to_roman(text: str) -> str:
    """Best-effort Korean romanization; falls back to surface if no library."""
    try:
        from hangul_romanize import romanize
        return " ".join(romanize(word) for word in text.split() if word)
    except Exception:
        return ""


def _annotate_korean(text: str, show_furigana: bool, show_romaji: bool,
                    learned_chars: Optional[set]) -> AnnotatedText:
    tokens: List[AnnotatedToken] = []
    ruby_parts: List[str] = []
    reading_parts: List[str] = []
    romaja_parts: List[str] = []

    for ch in text:
        if _HANGUL_RANGE.match(ch):
            tokens.append(AnnotatedToken(surface=ch, reading=ch, pos="hangul", is_kana=True))
            ruby_parts.append(ch)
            reading_parts.append(ch)
        else:
            tokens.append(AnnotatedToken(surface=ch))
            ruby_parts.append(ch)
            reading_parts.append(ch)
            if ch.strip():
                romaja_parts.append(ch)

    if show_romaji:
        romaja = _hangul_to_roman(text)
        if romaja:
            return AnnotatedText(
                original=text, tokens=tokens,
                html_ruby="".join(ruby_parts),
                html_romaji=romaja,
                plain_reading="".join(reading_parts),
            )

    return AnnotatedText(
        original=text, tokens=tokens,
        html_ruby="".join(ruby_parts),
        html_romaji=" ".join(romaja_parts) if show_romaji else "",
        plain_reading="".join(reading_parts),
    )


def _cyrillic_to_latin(text: str) -> str:
    """Minimal Russian→Latin transliteration (ALA-LC-ish)."""
    table = {
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
        "ж": "zh", "з": "z", "и": "i", "й": "i", "к": "k", "л": "l", "м": "m",
        "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
        "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch",
        "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "iu", "я": "ia",
    }
    out = []
    for ch in text.lower():
        out.append(table.get(ch, ch))
    return "".join(out)


def _annotate_cyrillic(text: str, show_furigana: bool, show_romaji: bool,
                      learned_chars: Optional[set]) -> AnnotatedText:
    tokens = [AnnotatedToken(surface=ch, reading=ch) for ch in text]
    return AnnotatedText(
        original=text, tokens=tokens,
        html_ruby=text,
        html_romaji=_cyrillic_to_latin(text) if show_romaji else "",
        plain_reading=text,
    )


def _annotate_latin(text: str, show_furigana: bool, show_romaji: bool,
                    learned_chars: Optional[set]) -> AnnotatedText:
    """Latin-script languages: pass through, no annotation needed."""
    tokens = [AnnotatedToken(surface=ch) for ch in text]
    return AnnotatedText(
        original=text, tokens=tokens,
        html_ruby=text,
        html_romaji="",
        plain_reading=text,
    )


_DISPATCH = {
    "japanese": _annotate_japanese,
    "chinese": _annotate_chinese,
    "korean": _annotate_korean,
    "cyrillic": _annotate_cyrillic,
    "latin": _annotate_latin,
}


def annotate_text(text: str, language: str = "ja",
                  show_furigana: bool = True, show_romaji: bool = False,
                  learned_chars: Optional[set] = None) -> AnnotatedText:
    """Annotate text for the given study language.

    Parameters
    ----------
    text : str
        Text to annotate.
    language : str
        Study language code (e.g. 'ja', 'zh', 'en').
    show_furigana : bool
        Show reading aids (furigana/pinyin) when applicable.
    show_romaji : bool
        Show romanization (romaji/pinyin/romaja/transliteration).
    learned_chars : set or None
        Characters already learned; reading aids are hidden for them.
    """
    info: Optional[LanguageInfo] = get_language(language)
    backend = info.annotator if info else "latin"

    if not info or not info.has_furigana:
        show_furigana = False
    if not info or not info.has_romaji:
        show_romaji = False

    handler = _DISPATCH.get(backend, _annotate_latin)
    return handler(text, show_furigana, show_romaji, learned_chars)


def detect_level(text: str, language: str = "ja") -> str:
    """Detect the approximate proficiency level of text for a language.

    Only Japanese has a real implementation; others fall back to the
    language's default level.
    """
    if language == "ja":
        from .japanese import detect_japanese_level
        return detect_japanese_level(text)
    info = get_language(language)
    return info.default_level if info else ""