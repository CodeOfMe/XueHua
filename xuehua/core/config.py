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

DEFAULT_LANG_DIR = Path(__file__).resolve().parent.parent.parent.parent / "日语"


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
    romaji_enabled: bool = True
    romaji_system: str = "hepburn"
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    epub_dir: str = ""
    show_furigana: bool = True
    current_level: str = "N5"

    chat_provider: str = "ollama"
    chat_api_key: str = ""
    chat_api_base_url: str = ""

    def get_epub_dir(self) -> Path:
        if self.epub_dir:
            return Path(self.epub_dir)
        return DEFAULT_LANG_DIR


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