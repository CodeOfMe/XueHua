"""Xuehua - Language learning assistant powered by EPUB knowledge base and Ollama LLM."""

__version__ = "0.1.0"

from .api import ToolResult, chat, build_knowledge_base
from .core.config import CONFIG, DATA_DIR, XUEHUA_DIR

__all__ = [
    "__version__",
    "ToolResult",
    "chat",
    "build_knowledge_base",
    "CONFIG",
    "DATA_DIR",
    "XUEHUA_DIR",
]