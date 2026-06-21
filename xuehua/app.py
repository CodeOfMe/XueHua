"""Xuehua - Language Learning Assistant - Flask Web Application."""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List

from flask import Flask, jsonify, render_template, request, Response, stream_with_context
from flask_cors import CORS

from .core.config import CONFIG, CHROMA_DIR, DATA_DIR, XUEHUA_DIR, load_config, save_config
from .core.constants import APP_NAME, APP_VERSION
from .core.annotation import annotate_text, detect_level
from .core.languages import get_language, get_levels, get_level_labels, default_level, list_languages, list_ui_languages
from .core.i18n import get_catalog, translate
from .core.kb_builder import EPUBParser, KnowledgeBaseBuilder
from .core.learning import ExerciseGenerator, ProgressTracker, SRSManager, SRSCard
from .core.vocab_networks import VOCAB_NETWORKS, get_all_domains, get_domain, get_domain_words, get_related_words, search_vocabulary
from .core.ollama_client import OllamaClient
from .core.photo_learn import IdentifyResult, PhotoItem, encode_image_file, generate_lesson, get_pinyin, identify_photo
from .core.vector_db import create_vector_db

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def _sanitize_collection_name(name: str) -> str:
    """Make a ChromaDB-safe collection name from arbitrary input.

    ChromaDB allows [a-zA-Z0-9._-], 3-512 chars, must start/end with alnum.
    Non-ASCII chars (e.g. Chinese) are transliterated to underscores and
    collapsed/trimmed to keep names readable and unique-ish.
    """
    import re
    safe = re.sub(r"[^a-zA-Z0-9._-]", "_", name)
    safe = re.sub(r"_{2,}", "_", safe)
    safe = safe.strip("._-")
    if not safe:
        safe = "kb"
    if len(safe) > 60:
        safe = safe[:60].rstrip("._-")
    return safe


def create_app():
    """Create and configure the Flask application."""
    # Initialize configuration and directories
    load_config()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    XUEHUA_DIR.mkdir(parents=True, exist_ok=True)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize backend services
    ollama = OllamaClient(CONFIG.ollama_url)

    try:
        chroma = create_vector_db(str(CHROMA_DIR), preferred="chroma")
    except Exception as e:
        logger.critical("[VectorDB] Init failed: %s", e)
        chroma = create_vector_db(str(CHROMA_DIR), preferred="memory")

    kb_builder = KnowledgeBaseBuilder(chroma, ollama, CONFIG)
    progress = ProgressTracker()
    srs = SRSManager()
    exercise_gen = ExerciseGenerator(CONFIG, progress, srs)

    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / "templates"),
        static_folder=str(Path(__file__).parent / "static"),
    )
    CORS(app)
    app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024

    # ── Pages ──────────────────────────────────────────────────────

    @app.route("/")
    def index():
        return render_template("index.html", config=CONFIG, app_name=APP_NAME, app_version=APP_VERSION)

    @app.route("/learn")
    def learn_page():
        return render_template("learn.html", config=CONFIG)

    @app.route("/review")
    def review_page():
        return render_template("review.html", config=CONFIG)

    @app.route("/chat")
    def chat_page():
        return render_template("chat.html", config=CONFIG)

    @app.route("/photo")
    def photo_page():
        return render_template("photo.html", config=CONFIG)

    # ── API: Models ─────────────────────────────────────────────────

    @app.route("/api/models")
    def get_models():
        ollama.api_url = CONFIG.ollama_url
        chat_models = ollama.get_chat_models()
        embed_models = ollama.get_embedding_models()
        return jsonify({
            "ollama_available": ollama.is_available(),
            "chat_models": chat_models,
            "embed_models": embed_models,
            "current_chat": CONFIG.chat_model,
            "current_embed": CONFIG.embedding_model,
        })

    @app.route("/api/settings", methods=["POST"])
    def update_settings():
        data = request.json or {}
        for key in [
            "ollama_url", "embedding_model", "chat_model",
            "chunk_size", "chunk_overlap", "rag_distance_threshold",
            "language", "ui_language", "romaji_enabled", "romaji_system",
            "show_furigana", "epub_dir", "current_level",
            "chat_provider", "chat_api_key", "chat_api_base_url",
        ]:
            if key in data:
                setattr(CONFIG, key, data[key])
        save_config()
        return jsonify({"success": True})

    @app.route("/api/settings", methods=["GET"])
    def get_settings():
        return jsonify({k: v for k, v in CONFIG.__dict__.items() if not k.startswith("_")})

    # ── API: Languages & UI ──────────────────────────────────────────

    @app.route("/api/languages")
    def api_languages():
        """List study languages and UI languages, plus current selection."""
        langs = [{
            "code": info.code,
            "name_zh": info.name_zh,
            "name_en": info.name_en,
            "endonym": info.endonym,
            "levels": info.levels,
            "level_labels": info.level_labels,
            "default_level": info.default_level,
            "has_furigana": info.has_furigana,
            "has_romaji": info.has_romaji,
            "script": info.script,
            "annotator": info.annotator,
            "extra": info.extra,
        } for info in list_languages()]
        return jsonify({
            "languages": langs,
            "ui_languages": list_ui_languages(),
            "current_language": CONFIG.language,
            "current_ui_language": CONFIG.ui_language,
            "current_level": CONFIG.normalize_level(),
        })

    @app.route("/api/i18n")
    def api_i18n():
        """Return the i18n catalog for the requested UI language.

        Query: ?ui=zh|en (default: CONFIG.ui_language)
        """
        ui = request.args.get("ui", CONFIG.ui_language)
        return jsonify({
            "ui_language": ui,
            "catalog": get_catalog(ui),
        })

    @app.route("/api/language/set", methods=["POST"])
    def api_set_language():
        """Switch study language and/or UI language, normalizing the level."""
        data = request.json or {}
        changed = False
        if "language" in data:
            from .core.languages import is_supported
            if is_supported(data["language"]):
                CONFIG.language = data["language"]
                CONFIG.current_level = CONFIG.normalize_level(data["language"])
                changed = True
        if "ui_language" in data:
            from .core.languages import is_ui_supported
            if is_ui_supported(data["ui_language"]):
                CONFIG.ui_language = data["ui_language"]
                changed = True
        if "level" in data:
            CONFIG.current_level = data["level"]
            changed = True
        if changed:
            save_config()
        return jsonify({
            "success": True,
            "language": CONFIG.language,
            "ui_language": CONFIG.ui_language,
            "current_level": CONFIG.current_level,
        })

    # ── API: Knowledge Base ──────────────────────────────────────────

    @app.route("/api/kb/browse", methods=["GET"])
    def browse_directory():
        """Browse filesystem directories for EPUB files.

        Query params:
            path  - directory to list (default: user home)
            root  - optional root constraint; navigation refuses to go above this
        Returns: current_path, parent, dirs[], epubs[], has_epubs, error
        """
        from pathlib import Path as _Path

        raw = request.args.get("path", "").strip()
        root_raw = request.args.get("root", "").strip()

        try:
            if raw:
                target = _Path(raw).expanduser()
            else:
                target = _Path.home()
            target = target.resolve()

            root = _Path(root_raw).expanduser().resolve() if root_raw else None

            if not target.exists():
                return jsonify({"success": False, "error": f"路径不存在: {target}"})
            if not target.is_dir():
                return jsonify({"success": False, "error": f"不是目录: {target}"})

            if root is not None:
                try:
                    target.relative_to(root)
                except ValueError:
                    target = root

            dirs = []
            epubs = []
            try:
                for entry in sorted(target.iterdir(), key=lambda p: p.name.lower()):
                    if entry.is_dir() and not entry.name.startswith("."):
                        dirs.append(entry.name)
                    elif entry.is_file() and entry.suffix.lower() == ".epub":
                        epubs.append(entry.name)
            except PermissionError:
                return jsonify({"success": False, "error": f"无权限访问: {target}"})

            parent = str(target.parent) if target != target.parent else ""

            quick = []
            home = _Path.home()
            candidates = [
                ("主目录", str(home)),
            ]
            cfg_epub = CONFIG.get_epub_dir()
            candidates.append(("默认 EPUB 目录", str(cfg_epub)))
            try:
                proj_root = _Path(__file__).resolve().parents[3]
                candidates.append(("项目目录", str(proj_root)))
            except Exception:
                pass
            seen = set()
            for label, p in candidates:
                try:
                    rp = _Path(p).expanduser().resolve()
                except Exception:
                    continue
                if rp in seen:
                    continue
                seen.add(rp)
                if rp.exists() and rp.is_dir():
                    quick.append({"label": label, "path": str(rp)})

            return jsonify({
                "success": True,
                "current_path": str(target),
                "parent": parent,
                "dirs": dirs,
                "epubs": epubs,
                "has_epubs": len(epubs) > 0,
                "quick": quick,
            })
        except Exception as e:
            logger.error("[KB] Browse error: %s", e)
            return jsonify({"success": False, "error": str(e)})

    @app.route("/api/kb/build", methods=["POST"])
    def build_knowledge_base():
        data = request.json or {}
        epub_dir = data.get("epub_dir", "") or str(CONFIG.get_language_epub_dir(CONFIG.language))
        collection_name = data.get("collection_name", "")
        language = data.get("language", CONFIG.language)

        epub_path = Path(epub_dir)
        if not epub_path.exists():
            return jsonify({"success": False, "error": f"Directory not found: {epub_dir}"})

        # Prefix collection with language code to keep KBs separate per language.
        # ChromaDB names allow [a-zA-Z0-9._-] only, so use a dot separator and
        # sanitize non-ASCII characters from the directory name.
        if not collection_name:
            collection_name = epub_path.name
        safe_name = _sanitize_collection_name(collection_name)
        if language and not safe_name.startswith(f"{language}."):
            safe_name = f"{language}.{safe_name}"
        collection_name = safe_name

        if not CONFIG.embedding_model:
            models = ollama.get_embedding_models()
            if models:
                CONFIG.embedding_model = models[0]
                save_config()
            else:
                return jsonify({"success": False, "error": "No embedding model available. Install one with: ollama pull nomic-embed-text"})

        try:
            files, chunks = kb_builder.build_from_directory(epub_path, collection_name)
            return jsonify({"success": True, "files": files, "chunks": chunks, "collection": collection_name})
        except Exception as e:
            logger.error("[KB] Build error: %s", e)
            return jsonify({"success": False, "error": str(e)})

    @app.route("/api/kb/collections")
    def list_collections():
        collections = chroma.list_collections()
        stats = chroma.get_stats()
        return jsonify({"collections": [{"name": c, "count": stats.get(c, 0)} for c in collections]})

    @app.route("/api/kb/collections/<name>", methods=["DELETE"])
    def delete_collection(name):
        success = chroma.delete_collection(name)
        return jsonify({"success": success})

    @app.route("/api/kb/search", methods=["POST"])
    def search_knowledge_base():
        data = request.json or {}
        query = data.get("query", "")
        collections = data.get("collections", None)
        top_k = data.get("top_k", 15)

        if not query:
            return jsonify({"success": False, "error": "Query is required"})

        if not CONFIG.embedding_model:
            return jsonify({"success": False, "error": "No embedding model configured"})

        try:
            results = kb_builder.search(query, collections, top_k)
            return jsonify({
                "success": True,
                "results": [{
                    "document": r["document"][:500],
                    "source": r.get("metadata", {}).get("file", ""),
                    "section": r.get("metadata", {}).get("section_title", ""),
                    "distance": r.get("distance", 0),
                    "collection": r.get("collection", ""),
                } for r in results],
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})

    # ── API: Japanese Processing ─────────────────────────────────────

    @app.route("/api/japanese/annotate", methods=["POST"])
    def annotate_japanese():
        data = request.json or {}
        text = data.get("text", "")
        show_furigana = data.get("show_furigana", CONFIG.show_furigana)
        show_romaji = data.get("show_romaji", CONFIG.romaji_enabled)
        learned_chars = set(data.get("learned_kanji", []) or data.get("learned_chars", []))
        language = data.get("language", CONFIG.language)

        if not text:
            return jsonify({"success": False, "error": "Text is required"})

        result = annotate_text(text, language=language,
                                show_furigana=show_furigana, show_romaji=show_romaji,
                                learned_chars=learned_chars)

        return jsonify({"success": True, **result.to_api_dict()})

    @app.route("/api/annotate", methods=["POST"])
    def annotate_any():
        """Language-agnostic alias of /api/japanese/annotate."""
        data = request.json or {}
        text = data.get("text", "")
        show_furigana = data.get("show_furigana", CONFIG.show_furigana)
        show_romaji = data.get("show_romaji", CONFIG.romaji_enabled)
        learned_chars = set(data.get("learned_chars", []) or data.get("learned_kanji", []))
        language = data.get("language", CONFIG.language)

        if not text:
            return jsonify({"success": False, "error": "Text is required"})

        result = annotate_text(text, language=language,
                                show_furigana=show_furigana, show_romaji=show_romaji,
                                learned_chars=learned_chars)
        return jsonify({"success": True, **result.to_api_dict()})

    @app.route("/api/japanese/tokenize", methods=["POST"])
    def tokenize_japanese():
        data = request.json or {}
        text = data.get("text", "")
        language = data.get("language", CONFIG.language)
        if not text:
            return jsonify({"success": False, "error": "Text is required"})

        result = annotate_text(text, language=language, show_furigana=False, show_romaji=False)
        return jsonify({
            "success": True,
            "tokens": [{
                "surface": t.surface,
                "lemma": t.lemma,
                "reading": t.reading,
                "pos": t.pos,
                "is_kanji": t.is_kanji,
                "is_kana": t.is_kana,
            } for t in result.tokens],
        })

    @app.route("/api/japanese/level", methods=["POST"])
    def detect_level_api():
        data = request.json or {}
        text = data.get("text", "")
        language = data.get("language", CONFIG.language)
        if not text:
            return jsonify({"success": False, "error": "Text is required"})
        level = detect_level(text, language=language)
        return jsonify({"success": True, "level": level})

    @app.route("/api/japanese/romaji", methods=["POST"])
    def convert_romaji():
        data = request.json or {}
        text = data.get("kana", "") or data.get("text", "")
        language = data.get("language", CONFIG.language)
        system = data.get("system", "hepburn")
        if not text:
            return jsonify({"success": False, "error": "Text is required"})
        result = annotate_text(text, language=language, show_furigana=False, show_romaji=True)
        return jsonify({"success": True, "romaji": result.html_romaji, "system": system})

    # ── API: Learning ────────────────────────────────────────────────

    @app.route("/api/learning/progress")
    def get_progress():
        return jsonify({"success": True, "data": progress.get_progress_summary()})

    @app.route("/api/learning/progress", methods=["POST"])
    def update_progress():
        data = request.json or {}
        if "current_level" in data:
            progress.set_current_level(data["current_level"])
        if "learned_kanji" in data:
            for k in data["learned_kanji"]:
                progress.learn_kanji(k)
        return jsonify({"success": True})

    @app.route("/api/learning/srs/stats")
    def srs_stats():
        return jsonify({"success": True, "data": srs.get_stats()})

    @app.route("/api/learning/srs/due")
    def srs_due():
        limit = request.args.get("limit", 20, type=int)
        level = request.args.get("level", "")
        cards = srs.get_due_cards(limit=limit, level=level)
        return jsonify({
            "success": True,
            "cards": [c.to_dict() for c in cards],
            "count": len(cards),
        })

    @app.route("/api/learning/srs/review", methods=["POST"])
    def srs_review():
        data = request.json or {}
        card_id = data.get("card_id", "")
        quality = data.get("quality", 3)
        if not card_id:
            return jsonify({"success": False, "error": "card_id required"})

        card = srs.review_card(card_id, quality)
        if card is None:
            return jsonify({"success": False, "error": "Card not found"})
        return jsonify({"success": True, "card": card.to_dict()})

    @app.route("/api/learning/srs/add", methods=["POST"])
    def srs_add():
        data = request.json or {}
        card = SRSCard(
            card_id=data.get("card_id", ""),
            front=data.get("front", ""),
            back=data.get("back", ""),
            reading=data.get("reading", ""),
            level=data.get("level", "N5"),
            category=data.get("category", ""),
        )
        if not card.card_id:
            import hashlib
            card.card_id = hashlib.md5(f"{card.front}_{card.back}".encode()).hexdigest()[:12]
        srs.add_card(card)
        return jsonify({"success": True, "card": card.to_dict()})

    # ── API: Exercise Generation ──────────────────────────────────────

    @app.route("/api/exercises/multiple_choice", methods=["POST"])
    def gen_multiple_choice():
        data = request.json or {}
        items = data.get("items", [])
        num_choices = data.get("num_choices", 4)
        if not items:
            return jsonify({"success": False, "error": "Items required"})
        exercises = exercise_gen.generate_multiple_choice(items, num_choices)
        return jsonify({"success": True, "exercises": exercises})

    @app.route("/api/exercises/reading_quiz", methods=["POST"])
    def gen_reading_quiz():
        data = request.json or {}
        vocabulary = data.get("vocabulary", [])
        learned_kanji = set(data.get("learned_kanji", []))
        if not vocabulary:
            return jsonify({"success": False, "error": "Vocabulary required"})
        exercises = exercise_gen.generate_reading_quiz(vocabulary, learned_kanji)
        return jsonify({"success": True, "exercises": exercises})

    # ── API: Vocabulary Networks ────────────────────────────────────

    @app.route("/api/vocab/domains")
    def vocab_domains():
        """List all vocabulary domains, optionally filtered by study language."""
        language = request.args.get("language", "")
        domains = get_all_domains(language=language)
        return jsonify({"success": True, "domains": domains})

    @app.route("/api/vocab/domain/<domain_id>")
    def vocab_domain(domain_id):
        """Get a specific vocabulary domain with all words."""
        network = get_domain(domain_id)
        if not network:
            return jsonify({"success": False, "error": f"Domain '{domain_id}' not found"})
        return jsonify({"success": True, **network.to_dict()})

    @app.route("/api/vocab/domain/<domain_id>/words")
    def vocab_domain_words_api(domain_id):
        """Get words from a domain, optionally filtered by level."""
        level = request.args.get("level", "")
        words = get_domain_words(domain_id, level)
        learned_kanji = set()
        result = []
        for w in words:
            annotated = annotate_text(
                w.word, language=CONFIG.language,
                show_furigana=CONFIG.show_furigana,
                show_romaji=CONFIG.romaji_enabled, learned_chars=learned_kanji,
            )
            result.append({
                **w.to_dict(),
                "html_ruby": annotated.html_ruby,
                "html_romaji": annotated.html_romaji,
                "plain_reading": annotated.plain_reading,
            })
        return jsonify({"success": True, "words": result, "domain_id": domain_id, "level": level})

    @app.route("/api/vocab/related/<word>")
    def vocab_related(word):
        """Find words related to a given word."""
        domain_id = request.args.get("domain", "")
        related = get_related_words(word, domain_id)
        learned_kanji = set()
        result = []
        for w in related:
            annotated = annotate_text(
                w.word, language=CONFIG.language,
                show_furigana=CONFIG.show_furigana,
                show_romaji=CONFIG.romaji_enabled, learned_chars=learned_kanji,
            )
            result.append({**w.to_dict(), "html_ruby": annotated.html_ruby, "html_romaji": annotated.html_romaji})
        return jsonify({"success": True, "word": word, "related": result})

    @app.route("/api/vocab/search")
    def vocab_search():
        """Search vocabulary across all domains."""
        query = request.args.get("q", "")
        domain_id = request.args.get("domain", "")
        level = request.args.get("level", "")
        if not query:
            return jsonify({"success": False, "error": "Query parameter 'q' is required"})
        results = search_vocabulary(query, domain_id, level)
        learned_kanji = set()
        for r in results:
            annotated = annotate_text(
                r["word"], language=CONFIG.language,
                show_furigana=CONFIG.show_furigana,
                show_romaji=CONFIG.romaji_enabled, learned_chars=learned_kanji,
            )
            r["html_ruby"] = annotated.html_ruby
            r["html_romaji"] = annotated.html_romaji
        return jsonify({"success": True, "results": results, "count": len(results)})

    # ── API: Chat ─────────────────────────────────────────────────────

    def _prepare_chat(data: dict, require_model: bool = True):
        """Prepare chat messages from request data.

        Returns (messages, model, error_json).
        If error_json is not None, the caller should return it immediately.
        """
        message = data.get("message", "")
        model = data.get("model", CONFIG.chat_model)
        use_kb = data.get("use_kb", True)
        collections = data.get("collections", None)
        language = data.get("language", CONFIG.language)

        if not message:
            return None, None, jsonify({"success": False, "error": "Message required"})

        if not model:
            models = ollama.get_chat_models()
            if models:
                model = models[0]
            elif require_model:
                return None, None, jsonify({"success": False, "error": "No chat model available"})

        system_prompt = _build_system_prompt(language)

        context = ""
        if use_kb:
            try:
                context = kb_builder.build_context(message, collections)
            except Exception:
                pass

        messages = [{"role": "system", "content": system_prompt}]
        if context:
            messages.append({"role": "system", "content": f"参考资料：\n{context}"})
        messages.append({"role": "user", "content": message})

        return messages, model, None

    @app.route("/api/chat", methods=["POST"])
    def chat():
        messages, model, error = _prepare_chat(request.json or {}, require_model=True)
        if error:
            return error
        response_text = ollama.chat_complete(messages, model)
        return jsonify({"success": True, "response": response_text})

    @app.route("/api/chat/stream", methods=["POST"])
    def chat_stream():
        messages, model, error = _prepare_chat(request.json or {}, require_model=False)
        if error:
            return error

        def generate():
            for chunk in ollama.chat_stream(messages, model):
                yield chunk

        return Response(stream_with_context(generate()), mimetype="text/plain")

    # ── API: Test Connection ──────────────────────────────────────────

    @app.route("/api/test-connection", methods=["POST"])
    def test_connection():
        url = request.json.get("url", CONFIG.ollama_url) if request.json else CONFIG.ollama_url
        try:
            import requests as req
            r = req.get(f"{url.rstrip('/')}/api/tags", timeout=5)
            return jsonify({"success": r.status_code == 200})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})

    # ── API: Photo Learning ───────────────────────────────────────────

    @app.route("/api/photo/identify", methods=["POST"])
    def photo_identify():
        data = request.json or {}
        image_data = data.get("image", "")
        model = data.get("model", "")

        if not image_data:
            return jsonify({"success": False, "error": "Image data required"})

        ollama.api_url = CONFIG.ollama_url
        if not ollama.is_available():
            return jsonify({"success": False, "error": "Ollama not available. Start Ollama first."})

        result = identify_photo(image_data, ollama, model)

        return jsonify({
            "success": True,
            "items": [
                {
                    "name": item.name,
                    "pinyin": item.pinyin,
                    "radical": item.radical,
                    "strokes": item.strokes,
                    "explanation": item.explanation,
                    "example": item.example,
                    "example_pinyin": item.example_pinyin,
                    "english": item.english,
                }
                for item in result.items
            ],
            "scene_description": result.scene_description,
            "raw_response": result.raw_response,
        })

    @app.route("/api/photo/upload", methods=["POST"])
    def photo_upload():
        if "image" not in request.files:
            return jsonify({"success": False, "error": "No image file provided"})

        file = request.files["image"]
        if not file.filename:
            return jsonify({"success": False, "error": "No file selected"})

        allowed_types = {"image/jpeg", "image/png", "image/webp", "image/gif"}
        if file.content_type not in allowed_types:
            return jsonify({"success": False, "error": f"Unsupported format: {file.content_type}. Use JPG/PNG/WebP/GIF."})

        try:
            image_bytes = file.read()
            if len(image_bytes) > 10 * 1024 * 1024:
                return jsonify({"success": False, "error": "Image too large (max 10MB)"})
            image_data = encode_image_file(image_bytes)
            return jsonify({"success": True, "image_data": image_data})
        except Exception as e:
            logger.error("[Photo] Upload error: %s", e)
            return jsonify({"success": False, "error": str(e)})

    @app.route("/api/photo/lesson", methods=["POST"])
    def photo_lesson():
        data = request.json or {}
        items_data = data.get("items", [])
        model = data.get("model", "")

        if not items_data:
            return jsonify({"success": False, "error": "Items required"})

        ollama.api_url = CONFIG.ollama_url
        items = [
            PhotoItem(
                name=i.get("name", ""),
                pinyin=i.get("pinyin", ""),
                radical=i.get("radical", ""),
                strokes=i.get("strokes", 0),
                explanation=i.get("explanation", ""),
                example=i.get("example", ""),
                example_pinyin=i.get("example_pinyin", ""),
                english=i.get("english", ""),
            )
            for i in items_data
        ]

        lesson = generate_lesson(items, ollama, model)

        return jsonify({
            "success": True,
            "lesson": {
                "title": lesson.title,
                "chant": lesson.chant,
                "story": lesson.story,
                "questions": lesson.questions,
                "words": [
                    {
                        "word": w.word,
                        "pinyin": w.pinyin,
                        "radical": w.radical,
                        "strokes": w.strokes,
                        "meaning": w.meaning,
                        "example_sentence": w.example_sentence,
                        "example_pinyin": w.example_pinyin,
                        "example_translation": w.example_translation,
                        "stroke_order_hint": w.stroke_order_hint,
                        "fun_fact": w.fun_fact,
                        "related_words": w.related_words,
                    }
                    for w in lesson.words
                ],
            },
        })

    @app.route("/api/photo/models")
    def photo_models():
        ollama.api_url = CONFIG.ollama_url
        available = ollama.is_available()
        vision_models = ollama.get_vision_models() if available else []
        chat_models = ollama.get_chat_models() if available else []
        return jsonify({
            "success": True,
            "available": available,
            "vision_models": vision_models,
            "chat_models": chat_models,
            "recommended": vision_models[0] if vision_models else (chat_models[0] if chat_models else ""),
        })

    # ── API: Pinyin ──────────────────────────────────────────────────

    @app.route("/api/pinyin", methods=["POST"])
    def get_pinyin_api():
        data = request.json or {}
        text = data.get("text", "")
        if not text:
            return jsonify({"success": False, "error": "Text required"})
        result = get_pinyin(text)
        return jsonify({"success": True, "pinyin": result})

    # ── Helper ───────────────────────────────────────────────────────

    def _build_system_prompt(language: str) -> str:
        """Build a system prompt for the given study language.

        The prompt adapts to the language: Japanese/Chinese/Korean get
        reading-aid instructions, Latin/Cyrillic get simpler guidance.
        """
        info = get_language(language) or get_language("ja")
        target = info.name_en
        endonym = info.endonym
        ui_lang = CONFIG.ui_language or "zh"
        if ui_lang == "zh":
            base = (
                f"你是学话(Xuehua)，一个{info.name_zh}({endonym})学习助手。"
                f"你的职责是通过清晰的讲解、例句和耐心的引导，帮助学习者练习{info.name_zh}。"
                f"遵循以下规则：\n\n"
            )
            rules = [
                "用学习者使用的语言回复，但包含目标语言的例句。",
                "提供例句时，附上目标语言原文、读音标注（如适用）、翻译。",
                "根据学习者当前级别逐步提高难度。",
                "用简单清晰的例子解释语法点。",
                "使用提供的参考资料给出准确、有据可依的回答。",
                "学习者出错时，温和纠正并解释原因。",
            ]
            if info.has_furigana:
                rules.insert(0, f"讨论{info.name_zh}文本时，始终为汉字/难词提供读音标注。")
            if info.has_romaji:
                rules.insert(1, f"对初学者，可附上{info.extra.get('romaji_label', '罗马音')}。")
            return base + "\n".join(f"{i}. {r}" for i, r in enumerate(rules, 1))

        base = (
            f"You are Xuehua, a {target} ({endonym}) language learning assistant. "
            f"Your role is to help learners practice {target} through clear explanations, "
            f"example sentences, and patient guidance. Follow these rules:\n\n"
        )
        rules = [
            "Respond in the language the learner uses, but include target-language examples.",
            "When giving example sentences, include the target-language text, reading aids (if applicable), and the translation.",
            "Progressively increase complexity based on the learner's level.",
            "Explain grammar points with clear, simple examples.",
            "Use the reference materials provided to give accurate, contextual answers.",
            "When the learner makes mistakes, gently correct them and explain why.",
        ]
        if info.has_furigana:
            rules.insert(0, f"Always provide reading aids for {target} characters when discussing {target} text.")
        if info.has_romaji:
            rules.insert(1, f"For beginners, include {info.extra.get('romaji_label', 'romanization')}.")
        return base + "\n".join(f"{i}. {r}" for i, r in enumerate(rules, 1))

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host=CONFIG.host, port=CONFIG.port, debug=True)