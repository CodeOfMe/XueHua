"""Xuehua - Unified Python API for programmatic usage."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

from .core.config import CONFIG, DATA_DIR, XUEHUA_DIR, load_config, save_config
from .core.errors import XuehuaError, ToolResult
from .core.japanese import annotate_text, detect_japanese_level, kana_to_romaji, tokenize
from .core.kb_builder import KnowledgeBaseBuilder
from .core.learning import ExerciseGenerator, ProgressTracker, SRSManager
from .core.ollama_client import OllamaClient
from .core.vector_db import create_vector_db

logger = logging.getLogger(__name__)


def chat(
    message: str,
    *,
    model: str = "",
    use_kb: bool = True,
    collections: Optional[List[str]] = None,
    language: str = "ja",
) -> ToolResult:
    """Send a chat message to the language learning assistant.

    Parameters
    ----------
    message : str
        User message to send.
    model : str
        Ollama model name (empty string for default).
    use_kb : bool
        Whether to use RAG knowledge base retrieval.
    collections : list of str or None
        Specific KB collections to search.
    language : str
        Target language code (ja, zh, en, etc.).

    Returns
    -------
    ToolResult
        With data containing the assistant reply.
    """
    load_config()
    ollama = OllamaClient(CONFIG.ollama_url)
    chroma = create_vector_db(str(CONFIG.get("chroma_dir", str(XUEHUA_DIR / "chroma"))))
    kb = KnowledgeBaseBuilder(chroma, ollama, CONFIG)

    model_name = model or CONFIG.chat_model
    if not model_name:
        models = ollama.get_chat_models()
        if models:
            model_name = models[0]
        else:
            return ToolResult(success=False, error="No Ollama models available")

    lang_names = {"ja": "Japanese", "zh": "Chinese", "en": "English"}
    target = lang_names.get(language, "Japanese")

    system_prompt = (
        f"You are Xuehua, a {target} language learning assistant. "
        "Provide clear explanations, example sentences with furigana, "
        "and patient guidance for language learners."
    )

    context = ""
    if use_kb:
        context = kb.build_context(message, collections)

    messages = [{"role": "system", "content": system_prompt}]
    if context:
        messages.append({"role": "system", "content": f"Reference:\n{context}"})
    messages.append({"role": "user", "content": message})

    reply = ollama.chat_complete(messages, model_name)
    return ToolResult(success=True, data={"reply": reply}, message=reply)


def build_knowledge_base(
    epub_dir: str = "",
    collection_name: str = "",
    embedding_model: str = "",
) -> ToolResult:
    """Build knowledge base from EPUB files.

    Parameters
    ----------
    epub_dir : str
        Directory containing EPUB files.
    collection_name : str
        Name for the ChromaDB collection.
    embedding_model : str
        Ollama embedding model name.

    Returns
    -------
    ToolResult
        With data containing files_processed and chunks_created counts.
    """
    load_config()

    if embedding_model:
        CONFIG.embedding_model = embedding_model
        save_config()

    ollama = OllamaClient(CONFIG.ollama_url)

    if not CONFIG.embedding_model:
        models = ollama.get_embedding_models()
        if models:
            CONFIG.embedding_model = models[0]
            save_config()
        else:
            return ToolResult(success=False, error="No embedding model available")

    from .core.vector_db import create_vector_db
    chroma = create_vector_db(str(XUEHUA_DIR / "chroma"))
    kb = KnowledgeBaseBuilder(chroma, ollama, CONFIG)

    epub_path = Path(epub_dir) if epub_dir else CONFIG.get_epub_dir()
    if not epub_path.exists():
        return ToolResult(success=False, error=f"Directory not found: {epub_path}")

    files, chunks = kb.build_from_directory(epub_path, collection_name)
    return ToolResult(
        success=True,
        data={"files_processed": files, "chunks_created": chunks},
        message=f"Built KB: {files} files, {chunks} chunks",
    )