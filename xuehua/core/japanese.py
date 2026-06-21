"""Japanese text processing: furigana annotation, romaji conversion, tokenization.

Uses fugashi + UniDic for morphological analysis.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

try:
    import fugashi
    _TAGGER = fugashi.Tagger()
    _FUGASHI_AVAILABLE = True
except ImportError:
    _TAGGER = None
    _FUGASHI_AVAILABLE = False

try:
    import jaconv
    _JACONV_AVAILABLE = True
except ImportError:
    _JACONV_AVAILABLE = False


@dataclass
class Token:
    """A parsed Japanese token with annotations."""
    surface: str
    lemma: str = ""
    pos: str = ""
    pos_detail: str = ""
    reading: str = ""
    is_kanji: bool = False
    is_kana: bool = False
    is_mixed: bool = False


@dataclass
class AnnotatedText:
    """Text annotated with furigana and romaji."""
    original: str
    tokens: List[Token] = field(default_factory=list)
    html_ruby: str = ""
    html_romaji: str = ""
    plain_reading: str = ""


_KANJI_RANGE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]")
_KANA_RANGE = re.compile(r"[\u3040-\u309f\u30a0-\u30ff\uFF65-\uFF9f]")
_ROMAJI_MAP_H = {
    "あ": "a", "い": "i", "う": "u", "え": "e", "お": "o",
    "か": "ka", "き": "ki", "く": "ku", "け": "ke", "こ": "ko",
    "さ": "sa", "し": "shi", "す": "su", "せ": "se", "そ": "so",
    "た": "ta", "ち": "chi", "つ": "tsu", "て": "te", "と": "to",
    "な": "na", "に": "ni", "ぬ": "nu", "ね": "ne", "の": "no",
    "は": "ha", "ひ": "hi", "ふ": "fu", "へ": "he", "ほ": "ho",
    "ま": "ma", "み": "mi", "む": "mu", "め": "me", "も": "mo",
    "や": "ya", "ゆ": "yu", "よ": "yo",
    "ら": "ra", "り": "ri", "る": "ru", "れ": "re", "ろ": "ro",
    "わ": "wa", "を": "wo", "ん": "n",
    "が": "ga", "ぎ": "gi", "ぐ": "gu", "げ": "ge", "ご": "go",
    "ざ": "za", "じ": "ji", "ず": "zu", "ぜ": "ze", "ぞ": "zo",
    "だ": "da", "ぢ": "ji", "づ": "zu", "で": "de", "ど": "do",
    "ば": "ba", "び": "bi", "ぶ": "bu", "べ": "be", "ぼ": "bo",
    "ぱ": "pa", "ぴ": "pi", "ぷ": "pu", "ぺ": "pe", "ぽ": "po",
    "きゃ": "kya", "きゅ": "kyu", "きょ": "kyo",
    "しゃ": "sha", "しゅ": "shu", "しょ": "sho",
    "ちゃ": "cha", "ちゅ": "chu", "ちょ": "cho",
    "にゃ": "nya", "にゅ": "nyu", "にょ": "nyo",
    "ひゃ": "hya", "ひゅ": "hyu", "ひょ": "hyo",
    "みゃ": "mya", "みゅ": "myu", "みょ": "myo",
    "りゃ": "rya", "りゅ": "ryu", "りょ": "ryo",
    "ぎゃ": "gya", "ぎゅ": "gyu", "ぎょ": "gyo",
    "じゃ": "ja", "じゅ": "ju", "じょ": "jo",
    "びゃ": "bya", "びゅ": "byu", "びょ": "byo",
    "ぴゃ": "pya", "ぴゅ": "pyu", "ぴょ": "pyo",
}


def _extract_unidic_field(feature_str: str, field_name: str) -> str:
    """Extract a named field from UniDic feature string like pron='ガクセイ'."""
    pattern = re.compile(rf"{field_name}='([^']*)'")
    match = pattern.search(feature_str)
    if match:
        return match.group(1)
    return ""


def tokenize(text: str) -> List[Token]:
    """Tokenize Japanese text using fugashi/UniDic morphological analyzer."""
    if not _FUGASHI_AVAILABLE or _TAGGER is None:
        return _simple_tokenize(text)

    tokens = []
    for word in _TAGGER(text):
        surface = word.surface
        feature_str = str(word.feature)

        pos = _extract_unidic_field(feature_str, "pos1")
        if not pos:
            parts = feature_str.split(",")
            pos = parts[0] if parts else ""

        lemma = _extract_unidic_field(feature_str, "lemma") or surface
        if lemma.startswith("*") or lemma == surface:
            lemma = surface

        reading = _extract_unidic_field(feature_str, "pron")
        if not reading or reading == "*":
            reading = _extract_unidic_field(feature_str, "kana")
        if not reading or reading == "*":
            reading = surface

        pos_detail = _extract_unidic_field(feature_str, "pos2") or ""

        has_kanji = bool(_KANJI_RANGE.search(surface))
        has_kana = bool(_KANA_RANGE.search(surface))

        tokens.append(Token(
            surface=surface,
            lemma=lemma,
            pos=pos,
            pos_detail=pos_detail,
            reading=reading,
            is_kanji=has_kanji and not has_kana,
            is_kana=has_kana and not has_kanji,
            is_mixed=has_kanji and has_kana,
        ))
    return tokens


def _simple_tokenize(text: str) -> List[Token]:
    """Fallback tokenization when fugashi is not available."""
    tokens = []
    current = ""
    current_type = ""

    for char in text:
        if _KANJI_RANGE.match(char):
            char_type = "kanji"
        elif _KANA_RANGE.match(char):
            char_type = "kana"
        elif char.strip():
            char_type = "other"
        else:
            char_type = "space"

        if current and char_type != current_type and current_type != "space":
            tokens.append(Token(
                surface=current,
                is_kanji=current_type == "kanji",
                is_kana=current_type == "kana",
                is_mixed=current_type == "mixed",
            ))
            current = char
            current_type = char_type
        else:
            current += char
            if current_type == "mixed" or (current_type == "kanji" and _KANA_RANGE.search(current)):
                current_type = "mixed"

    if current:
        tokens.append(Token(
            surface=current,
            is_kanji=current_type == "kanji",
            is_kana=current_type == "kana",
            is_mixed=current_type == "mixed",
        ))

    return tokens


def add_furigana(text: str, learned_kanji: Optional[set] = None) -> str:
    """Add furigana annotations to Japanese text using HTML ruby tags.

    Parameters
    ----------
    text : str
        Japanese text to annotate.
    learned_kanji : set or None
        Set of kanji characters the user has already learned.
        Furigana will be hidden for these kanji.

    Returns
    -------
    str
        HTML string with ruby annotations.
    """
    if learned_kanji is None:
        learned_kanji = set()

    tokens = tokenize(text)
    parts = []

    for tok in tokens:
        if tok.is_kanji or tok.is_mixed:
            reading = tok.reading
            if _FUGASHI_AVAILABLE and reading and reading != tok.surface:
                kanji_part = tok.surface
                needs_furigana = any(
                    c not in learned_kanji
                    for c in kanji_part
                    if _KANJI_RANGE.match(c)
                )
                if needs_furigana:
                    parts.append(f"<ruby>{kanji_part}<rp>(</rp><rt>{reading}</rt><rp>)</rp></ruby>")
                else:
                    parts.append(kanji_part)
            else:
                parts.append(tok.surface)
        else:
            parts.append(tok.surface)

    return "".join(parts)


def kana_to_romaji(kana: str, system: str = "hepburn") -> str:
    """Convert hiragana/katakana to romaji.

    Parameters
    ----------
    kana : str
        Hiragana or katakana string.
    system : str
        Romanization system: "hepburn" (default). Other systems fall back
        to a manual mapping that approximates Hepburn.
    """
    # Prefer jaconv's built-in romanization (Hepburn only)
    if _JACONV_AVAILABLE and system == "hepburn":
        try:
            return jaconv.kana2alphabet(kana)
        except Exception:
            pass

    # Manual fallback for when jaconv is unavailable or non-Hepburn requested
    try:
        hiragana = jaconv.kata2hira(kana) if _JACONV_AVAILABLE else kana
        result = []
        i = 0
        while i < len(hiragana):
            if i + 1 < len(hiragana):
                digraph = hiragana[i:i+2]
                if digraph in _ROMAJI_MAP_H:
                    result.append(_ROMAJI_MAP_H[digraph])
                    i += 2
                    continue
            char = hiragana[i]
            if char in _ROMAJI_MAP_H:
                result.append(_ROMAJI_MAP_H[char])
            elif char == "っ":
                if i + 1 < len(hiragana) and hiragana[i+1] in _ROMAJI_MAP_H:
                    result.append(_ROMAJI_MAP_H[hiragana[i+1]][0])
                i += 1
                continue
            elif char == "ー":
                result.append("-")
            else:
                result.append(char)
            i += 1
        return "".join(result)
    except Exception:
        return kana


def annotate_text(text: str, show_furigana: bool = True, show_romaji: bool = False,
                  learned_kanji: Optional[set] = None) -> AnnotatedText:
    """Full annotation of Japanese text with furigana and optional romaji.

    Parameters
    ----------
    text : str
        Japanese text to annotate.
    show_furigana : bool
        Whether to show furigana above kanji.
    show_romaji : bool
        Whether to show romaji for kana.
    learned_kanji : set or None
        Set of kanji the user has learned (furigana hidden for these).
    """
    if learned_kanji is None:
        learned_kanji = set()

    tokens = tokenize(text)

    if show_furigana:
        html_ruby = add_furigana(text, learned_kanji)
    else:
        html_ruby = text

    if show_romaji:
        romaji_parts = []
        for tok in tokens:
            if tok.is_kanji or tok.is_mixed:
                reading = tok.reading if tok.reading else tok.surface
                romaji_parts.append(kana_to_romaji(reading))
            elif tok.is_kana:
                romaji_parts.append(kana_to_romaji(tok.surface))
            else:
                romaji_parts.append(tok.surface)
        html_romaji = " ".join(romaji_parts)
    else:
        html_romaji = ""

    reading_parts = []
    for tok in tokens:
        if tok.is_kanji or tok.is_mixed:
            reading_parts.append(tok.reading if tok.reading else tok.surface)
        else:
            reading_parts.append(tok.surface)
    plain_reading = "".join(reading_parts)

    return AnnotatedText(
        original=text,
        tokens=tokens,
        html_ruby=html_ruby,
        html_romaji=html_romaji,
        plain_reading=plain_reading,
    )


_N5_KANJI = set("一二三四五六七八九十百千万円時日月年私今何大小人中男女子女父母友先生日国語学校長高低新古多少近遠")
_N4_KANJI = set("会間事市京夜思話働通問題意力物待持受合教頭気味方部員明代写考売買医病院映画音楽")
_N3_KANJI = set("経験説明練習約束連絡準備紹介趣味発表意見質問返事活動社会経済政治国際問題環境関係")
_N2_KANJI = set("推測維持影響可能性範囲状況課題実現提案判断責任構造制度価値資源技術産業効果")


def detect_japanese_level(text: str) -> str:
    """Detect the approximate JLPT level of Japanese text.

    Returns one of: 'N5', 'N4', 'N3', 'N2', 'N1'
    """
    text_kanji = set(_KANJI_RANGE.findall(text))
    total_chars = len(text.strip())
    if total_chars == 0:
        return "N5"

    n5_known = text_kanji & _N5_KANJI
    n4_known = text_kanji & _N4_KANJI
    n3_known = text_kanji & _N3_KANJI
    n2_known = text_kanji & _N2_KANJI

    advanced_kanji = text_kanji - _N5_KANJI - _N4_KANJI - _N3_KANJI - _N2_KANJI

    if len(advanced_kanji) > 0:
        return "N1"
    if n2_known and len(n2_known) > 2:
        return "N2"
    if n3_known and len(n3_known) > 2:
        return "N3"
    if n4_known and len(n4_known) > 2:
        return "N4"
    if n5_known or len(text_kanji) < 3:
        return "N5"

    has_hiragana = bool(re.search(r"[\u3040-\u309f]", text))
    has_katakana = bool(re.search(r"[\u30a0-\u30ff]", text))

    if has_hiragana and not text_kanji:
        return "N5"
    if has_hiragana or has_katakana:
        return "N4"
    return "N3"