"""Command-line interface for Xuehua."""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

# Suppress third-party import warnings (e.g. urllib3 version mismatches)
warnings.filterwarnings("ignore")


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
    kb_parser.add_argument("--language", default="", help="Study language code (e.g. ja, en, zh)")

    learn_parser = subparsers.add_parser("learn", help="Learning commands")
    learn_parser.add_argument("action", choices=["progress", "srs", "annotate"], help="Learning action")
    learn_parser.add_argument("--text", default="", help="Text to annotate")
    learn_parser.add_argument("--furigana", action=argparse.BooleanOptionalAction, default=True, help="Show furigana")
    learn_parser.add_argument("--romaji", action="store_true", help="Show romaji")
    learn_parser.add_argument("--level", default="N5", help="JLPT level filter")

    vocab_parser = subparsers.add_parser("vocab", help="Vocabulary domain management")
    vocab_parser.add_argument("action", choices=["domains", "domain", "list", "search", "export"],
                              help="Vocab action")
    vocab_parser.add_argument("target", nargs="?", default="", help="Domain ID, word, or search query")
    vocab_parser.add_argument("--domain", default="", help="Filter by domain ID")
    vocab_parser.add_argument("--level", default="", help="Filter by JLPT level (N5-N1)")
    vocab_parser.add_argument("--format", default="table", choices=["table", "json", "csv"],
                              help="Output format")

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
    elif args.command == "vocab":
        _handle_vocab(args)
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
        import re as _re
        language = args.language or CONFIG.language
        if args.dir:
            epub_dir = Path(args.dir)
        else:
            epub_dir = CONFIG.get_language_epub_dir(language)
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

        def _sanitize(name):
            safe = _re.sub(r"[^a-zA-Z0-9._-]", "_", name)
            safe = _re.sub(r"_{2,}", "_", safe).strip("._-")
            return safe or "kb"

        collection_name = args.name
        if not collection_name:
            collection_name = epub_dir.name
        collection_name = _sanitize(collection_name)
        if language and not collection_name.startswith(f"{language}."):
            collection_name = f"{language}.{collection_name}"

        files, chunks = kb.build_from_directory(epub_dir, collection_name)
        print(f"Built knowledge base: {files} files, {chunks} chunks (collection: {collection_name})")

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


def _handle_vocab(args):
    """Handle vocab domain commands."""
    from xuehua.core.vocab_networks import (
        VOCAB_NETWORKS, get_all_domains, get_domain, get_domain_words,
        get_related_words, search_vocabulary,
    )

    if args.action == "domains":
        _vocab_domains(args)
    elif args.action == "domain":
        _vocab_domain_detail(args)
    elif args.action == "list":
        _vocab_list(args)
    elif args.action == "search":
        _vocab_search(args)
    elif args.action == "export":
        _vocab_export(args)


def _vocab_domains(args):
    """List all vocabulary domains."""
    from xuehua.core.vocab_networks import get_all_domains, get_domain_words

    domains = get_all_domains()
    if args.format == "json":
        print(json.dumps(domains, indent=2, ensure_ascii=False))
        return

    if args.format == "csv":
        print("domain_id,domain_name,domain_name_ja,word_count,levels")
        for d in domains:
            print(f'{d["domain_id"]},{d["domain_name"]},{d["domain_name_ja"]},{d["word_count"]},{"|".join(d["levels"])}')
        return

    # table format
    print(f"\n{'Domain ID':20s} {'Name':18s} {'日本語':22s} {'Words':>5s}  JLPT Levels")
    print("-" * 85)
    for d in domains:
        levels_str = ", ".join(d["levels"])
        print(f'{d["domain_id"]:20s} {d["domain_name"]:18s} {d["domain_name_ja"]:22s} {d["word_count"]:5d}  {levels_str}')
    print(f'\n{len(domains)} domains total. Use "xuehua vocab list <domain_id>" to see words.')


def _vocab_domain_detail(args):
    """Show detailed info about a domain."""
    from xuehua.core.vocab_networks import get_domain

    if not args.target:
        print("Error: domain ID required (e.g. xuehua vocab domain computer)")
        sys.exit(1)

    network = get_domain(args.target)
    if not network:
        print(f"Error: domain '{args.target}' not found. Use 'xuehua vocab domains' to list available domains.")
        sys.exit(1)

    if args.format == "json":
        print(json.dumps(network.to_dict(), indent=2, ensure_ascii=False))
        return

    print(f"\n  Domain: {network.domain_name} ({network.domain_name_ja})")
    print(f"  Description: {network.description}")
    print(f"  Center words: {', '.join(network.center_words)}")
    print(f"  Words: {len(network.words)}")
    print(f"  Grammar points: {len(network.grammar_points)}")
    if network.grammar_points:
        print(f"\n  Grammar Patterns:")
        for gp in network.grammar_points:
            print(f"    {gp['pattern']:30s} — {gp['meaning']} [{gp['level']}]")
    print(f'\n  Use "xuehua vocab list {args.target}" to see all words.')


def _vocab_list(args):
    """List words in a domain with full details."""
    from xuehua.core.vocab_networks import get_domain_words, get_domain

    if not args.target:
        print("Error: domain ID or 'all' required (e.g. xuehua vocab list computer)")
        sys.exit(1)

    if args.target == "all":
        from xuehua.core.vocab_networks import VOCAB_NETWORKS
        words = []
        for net in VOCAB_NETWORKS.values():
            for w in net.words:
                if args.level and w.level != args.level:
                    continue
                words.append((w, net.domain_id))
    else:
        network = get_domain(args.target)
        if not network:
            print(f"Error: domain '{args.target}' not found.")
            sys.exit(1)
        words = [(w, args.target) for w in get_domain_words(args.target, args.level)]

    if not words:
        print("No words found matching the criteria.")
        return

    if args.format == "json":
        result = []
        for w, did in words:
            d = w.to_dict()
            d["domain_id"] = did
            result.append(d)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    if args.format == "csv":
        print("word,reading,meaning,level,pos,domain")
        for w, did in words:
            print(f'{w.word},{w.reading},{w.meaning},{w.level},{w.pos},{did}')
        return

    # table format
    print(f"\n{'Word':18s} {'Reading':18s} {'Meaning':14s} {'Level':>5s}  {'POS':10s}  Example")
    print("-" * 110)
    for w, did in words:
        example = w.example_jp[:45] + ("..." if len(w.example_jp) > 45 else "")
        print(f'{w.word:18s} {w.reading:18s} {w.meaning:14s} {w.level:>5s}  {w.pos:10s}  {example}')
    print(f'\n{len(words)} words. Use --level N5 to filter by JLPT level.')


def _vocab_search(args):
    """Search vocabulary across all domains."""
    from xuehua.core.vocab_networks import search_vocabulary

    if not args.target:
        print("Error: search query required (e.g. xuehua vocab search 写真)")
        sys.exit(1)

    results = search_vocabulary(args.target, domain_id=args.domain, level=args.level)

    if not results:
        print(f"No words found matching '{args.target}'.")
        return

    if args.format == "json":
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return

    if args.format == "csv":
        print("word,reading,meaning,level,pos,domain_id,domain_name")
        for r in results:
            print(f'{r["word"]},{r["reading"]},{r["meaning"]},{r["level"]},{r["pos"]},{r["domain_id"]},{r["domain_name"]}')
        return

    print(f"\nSearch results for '{args.target}':")
    print(f"{'Word':18s} {'Reading':18s} {'Meaning':14s} {'Level':>5s}  {'Domain':20s}")
    print("-" * 85)
    for r in results:
        print(f'{r["word"]:18s} {r["reading"]:18s} {r["meaning"]:14s} {r["level"]:>5s}  {r["domain_name"]:20s}')
    print(f'\n{len(results)} results.')


def _vocab_export(args):
    """Export vocabulary domain to a file."""
    from xuehua.core.vocab_networks import get_domain_words, get_domain
    from pathlib import Path

    if not args.target:
        print("Error: domain ID required for export (e.g. xuehua vocab export computer)")
        sys.exit(1)

    network = get_domain(args.target)
    if not network:
        print(f"Error: domain '{args.target}' not found.")
        sys.exit(1)

    words = get_domain_words(args.target, args.level)
    fmt = args.format

    if fmt == "json":
        data = {
            "domain": network.to_dict(),
            "exported_words": [w.to_dict() for w in words],
        }
        out_path = Path(f"{args.target}_vocab.json")
        out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Exported {len(words)} words to {out_path}")

    elif fmt == "csv":
        out_path = Path(f"{args.target}_vocab.csv")
        lines = ["word,reading,meaning,level,pos,example_jp,example_zh,example_reading,tags"]
        for w in words:
            tags = "|".join(w.tags)
            lines.append(f'{w.word},{w.reading},{w.meaning},{w.level},{w.pos},"{w.example_jp}","{w.example_zh}","{w.example_reading}","{tags}"')
        out_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"Exported {len(words)} words to {out_path}")

    else:
        # table format — print to stdout
        _vocab_list(args)


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