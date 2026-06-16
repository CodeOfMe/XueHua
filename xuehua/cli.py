"""Command-line interface for Xuehua."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    """Main entry point for xuehua CLI."""
    from xuehua import __version__

    if len(sys.argv) > 1 and sys.argv[1] == "chat":
        _cli_chat(sys.argv[2:])
        return

    parser = argparse.ArgumentParser(
        prog="xuehua",
        description="Xuehua - Language Learning Assistant with EPUB Knowledge Base",
    )
    parser.add_argument("-V", "--version", action="version", version=f"xuehua {__version__}")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5050, help="Port to listen on")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Output as JSON")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress non-essential output")
    parser.add_argument("--data-dir", default=None, help="Custom data directory")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    kb_parser = subparsers.add_parser("kb", help="Knowledge base management")
    kb_parser.add_argument("action", choices=["build", "list", "search", "delete"], help="KB action")
    kb_parser.add_argument("--dir", default="", help="EPUB directory path")
    kb_parser.add_argument("--name", default="", help="Collection name")
    kb_parser.add_argument("--query", default="", help="Search query")
    kb_parser.add_argument("--model", default="", help="Embedding model")

    learn_parser = subparsers.add_parser("learn", help="Learning commands")
    learn_parser.add_argument("action", choices=["progress", "srs", "annotate"], help="Learning action")
    learn_parser.add_argument("--text", default="", help="Text to annotate")
    learn_parser.add_argument("--furigana", action="store_true", default=True, help="Show furigana")
    learn_parser.add_argument("--romaji", action="store_true", help="Show romaji")
    learn_parser.add_argument("--level", default="N5", help="JLPT level filter")

    args = parser.parse_args()

    if args.data_dir:
        import os
        os.environ["KOTOBA_DATA_DIR"] = args.data_dir

    from xuehua.core.config import load_config
    load_config()

    if args.command == "kb":
        _handle_kb(args)
    elif args.command == "learn":
        _handle_learn(args)
    else:
        _start_web_server(args)


def _start_web_server(args):
    from xuehua.app import app
    from xuehua.core.config import CONFIG

    host = args.host if args.host else CONFIG.host
    port = args.port if args.port else CONFIG.port

    if not args.quiet:
        print(f"Xuehua starting on http://{host}:{port}")

    app.run(host=host, port=port, debug=args.debug)


def _handle_kb(args):
    from xuehua.core.config import CONFIG, load_config, save_config
    from xuehua.core.kb_builder import KnowledgeBaseBuilder
    from xuehua.core.ollama_client import OllamaClient
    from xuehua.core.vector_db import create_vector_db
    from xuehua.core.config import XUEHUA_DIR

    load_config()
    ollama = OllamaClient(CONFIG.ollama_url)
    chroma = create_vector_db(str(XUEHUA_DIR / "chroma"))
    kb = KnowledgeBaseBuilder(chroma, ollama, CONFIG)

    if args.action == "build":
        from pathlib import Path
        epub_dir = Path(args.dir) if args.dir else CONFIG.get_epub_dir()
        if args.model:
            CONFIG.embedding_model = args.model
            save_config()
        if not CONFIG.embedding_model:
            models = ollama.get_embedding_models()
            if models:
                CONFIG.embedding_model = models[0]
                save_config()
            else:
                print("Error: No embedding model available. Install one: ollama pull nomic-embed-text")
                sys.exit(1)

        files, chunks = kb.build_from_directory(epub_dir, args.name)
        print(f"Built knowledge base: {files} files, {chunks} chunks")

    elif args.action == "list":
        collections = chroma.list_collections()
        stats = chroma.get_stats()
        if args.json_output:
            print(json.dumps([{"name": c, "count": stats.get(c, 0)} for c in collections], indent=2))
        else:
            for c in collections:
                print(f"  {c}: {stats.get(c, 0)} documents")

    elif args.action == "search":
        if not args.query:
            print("Error: --query required for search")
            sys.exit(1)
        results = kb.search(args.query)
        for r in results:
            print(f"[{r.get('metadata', {}).get('file', '')}] (distance: {r.get('distance', 0):.3f})")
            print(f"  {r['document'][:200]}...")
            print()

    elif args.action == "delete":
        if not args.name:
            print("Error: --name required for delete")
            sys.exit(1)
        success = chroma.delete_collection(args.name)
        print(f"Deleted collection '{args.name}': {'success' if success else 'failed'}")


def _handle_learn(args):
    from xuehua.core.config import CONFIG, load_config
    from xuehua.core.japanese import annotate_text, detect_japanese_level
    from xuehua.core.learning import ProgressTracker, SRSManager

    load_config()
    progress = ProgressTracker()
    srs = SRSManager()

    if args.action == "progress":
        summary = progress.get_progress_summary()
        if args.json_output:
            print(json.dumps(summary, indent=2))
        else:
            print(f"Lessons completed: {summary['lessons_completed']}")
            print(f"Vocabulary learned: {summary['vocabulary_count']}")
            print(f"Kanji learned: {summary['kanji_count']}")
            print(f"Current level: {summary['current_level']}")

    elif args.action == "srs":
        due = srs.get_due_cards(level=args.level)
        print(f"Cards due for review: {len(due)}")
        for card in due[:10]:
            print(f"  {card.front} -> {card.back} (level: {card.level})")

    elif args.action == "annotate":
        if not args.text:
            print("Error: --text required for annotate")
            sys.exit(1)
        result = annotate_text(
            args.text,
            show_furigana=args.furigana,
            show_romaji=args.romaji,
        )
        print(f"Original: {result.original}")
        print(f"Ruby: {result.html_ruby}")
        if result.html_romaji:
            print(f"Romaji: {result.html_romaji}")


def _cli_chat(args):
    """Interactive CLI chat mode."""
    from xuehua.core.config import CONFIG, load_config
    from xuehua.core.ollama_client import OllamaClient

    load_config()
    ollama = OllamaClient(CONFIG.ollama_url)

    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="", help="Model name")
    parser.add_argument("--no-kb", action="store_true", help="Disable knowledge base")
    cargs = parser.parse_args(args)

    model = cargs.model or CONFIG.chat_model
    if not model:
        models = ollama.get_chat_models()
        if models:
            model = models[0]
        else:
            print("No models available. Start Ollama first.")
            sys.exit(1)

    print(f"Xuehua Chat (model: {model})")
    print("Type 'quit' to exit, '/help' for commands\n")

    from xuehua.core.kb_builder import KnowledgeBaseBuilder
    from xuehua.core.vector_db import create_vector_db
    from xuehua.core.config import XUEHUA_DIR

    chroma = create_vector_db(str(XUEHUA_DIR / "chroma"))
    kb = KnowledgeBaseBuilder(chroma, ollama, CONFIG)

    messages = [{"role": "system", "content": "You are Xuehua, a Japanese language learning assistant."}]

    try:
        from prompt_toolkit import PromptSession
        session = PromptSession()
        get_input = lambda: session.prompt("xuehua> ")
    except ImportError:
        get_input = lambda: input("xuehua> ")

    while True:
        try:
            user_input = get_input()
            if user_input.strip().lower() in ("quit", "exit", "q"):
                break
            if not user_input.strip():
                continue

            context = ""
            if not cargs.no_kb:
                context = kb.build_context(user_input)

            msg_list = messages.copy()
            if context:
                msg_list.append({"role": "system", "content": f"Reference:\n{context}"})
            msg_list.append({"role": "user", "content": user_input})

            print("\n", end="")
            full_response = ""
            for chunk in ollama.chat_stream(msg_list, model):
                print(chunk, end="", flush=True)
                full_response += chunk
            print("\n")

            messages.append({"role": "user", "content": user_input})
            messages.append({"role": "assistant", "content": full_response})
        except (KeyboardInterrupt, EOFError):
            break

    print("\nGoodbye!")