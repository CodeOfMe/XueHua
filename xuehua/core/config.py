"""Configuration management for Xuehua."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

from .constants import (
    DEFAULT_CHAT_MODEL,
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_HOST,
    DEFAULT_LANGUAGE,
    DEFAULT_PORT,
    DEFAULT_RAG_DISTANCE_THRESHOLD,
    OLLAMA_DEFAULT_URL,
)


def _get_data_dir() -> Path:
    """Determine the data directory."""
    env = os.environ.get("KOTOBA_DATA_DIR")
    if env:
        return Path(env).expanduser().resolve()

    pkg_dir = Path(__file__).resolve().parent.parent
    if "site-packages" in str(pkg_dir) or "dist-packages" in str(pkg_dir):
        return Path.home() / ".xuehua"
    return Path("./data")


DATA_DIR = _get_data_dir()
XUEHUA_DIR = DATA_DIR / "xuehua"
CHROMA_DIR = XUEHUA_DIR / "chroma"
EPUB_DIR = XUEHUA_DIR / "epub"
PROGRESS_DIR = XUEHUA_DIR / "progress"
CONFIG_FILE = XUEHUA_DIR / "xuehua_config.json"


@dataclass
class Config:
    """Xuehua configuration."""

    ollama_url: str = OLLAMA_DEFAULT_URL
    embedding_model: str = DEFAULT_EMBEDDING_MODEL
    chat_model: str = DEFAULT_CHAT_MODEL
    chunk_size: int = DEFAULT_CHUNK_SIZE
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
    rag_distance_threshold: float = DEFAULT_RAG_DISTANCE_THRESHOLD
    language: str = DEFAULT_LANGUAGE
    """Study language code (ISO 639-1): ja, zh, en, ko, fr, de, es, pt, it, ru."""

    ui_language: str = "zh"
    """Interface language: zh or en."""

    romaji_enabled: bool = True
    romaji_system: str = "hepburn"
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    epub_dir: str = ""
    show_furigana: bool = True
    current_level: str = "N5"
    """Current proficiency level for the study language."""

    chat_provider: str = "ollama"
    chat_api_key: str = ""
    chat_api_base_url: str = ""

    def get_epub_dir(self) -> Path:
        if self.epub_dir:
            return Path(self.epub_dir)
        EPUB_DIR.mkdir(parents=True, exist_ok=True)
        return EPUB_DIR

    def get_language_epub_dir(self, language: str = "") -> Path:
        """Return the default EPUB directory for a study language.

        Layout: <XUEHUA_DIR>/epub/<language>/. Falls back to the shared
        epub root when the language-specific subdir does not exist yet.
        """
        if self.epub_dir:
            return Path(self.epub_dir)
        lang = language or self.language
        if lang:
            lang_dir = EPUB_DIR / lang
            if lang_dir.exists():
                return lang_dir
            lang_dir.mkdir(parents=True, exist_ok=True)
            return lang_dir
        EPUB_DIR.mkdir(parents=True, exist_ok=True)
        return EPUB_DIR

    def normalize_level(self, language: str = "") -> str:
        """Return a valid level for the given study language.

        If current_level is not in the language's level set, returns the
        language default level. Empty levels return ''.
        """
        from .languages import get_levels, default_level
        lang = language or self.language
        levels = get_levels(lang)
        if not levels:
            return ""
        if self.current_level in levels:
            return self.current_level
        return default_level(lang)


def load_config() -> Config:
    """Load config from file, creating defaults if missing."""
    global CONFIG
    XUEHUA_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            CONFIG = Config(**{k: v for k, v in data.items() if k in Config.__dataclass_fields__})
        except (json.JSONDecodeError, TypeError):
            CONFIG = Config()
    else:
        CONFIG = Config()
        save_config()
    return CONFIG


def save_config() -> None:
    """Save config to file."""
    global CONFIG
    XUEHUA_DIR.mkdir(parents=True, exist_ok=True)
    data = {k: v for k, v in CONFIG.__dict__.items() if not k.startswith("_")}
    CONFIG_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


CONFIG = Config()