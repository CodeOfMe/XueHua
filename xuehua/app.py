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
from .core.japanese import add_furigana, annotate_text, detect_japanese_level, kana_to_romaji, tokenize
from .core.kb_builder import EPUBParser, KnowledgeBaseBuilder
from .core.learning import ExerciseGenerator, ProgressTracker, SRSManager, SRSCard
from .core.ollama_client import OllamaClient
from .core.vector_db import create_vector_db

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Initialize
load_config()
DATA_DIR.mkdir(parents=True, exist_ok=True)
XUEHUA_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

OLLAMA = OllamaClient(CONFIG.ollama_url)

try:
    CHROMA = create_vector_db(str(CHROMA_DIR), preferred="chroma")
except Exception as e:
    logger.critical("[VectorDB] Init failed: %s", e)
    CHROMA = create_vector_db(str(CHROMA_DIR), preferred="memory")

KB_BUILDER = KnowledgeBaseBuilder(CHROMA, OLLAMA, CONFIG)
PROGRESS = ProgressTracker()
SRS = SRSManager()
EXERCISE_GEN = ExerciseGenerator(CONFIG, PROGRESS, SRS)


def create_app():
    """Create and configure the Flask application."""
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

    # ── API: Models ─────────────────────────────────────────────────

    @app.route("/api/models")
    def get_models():
        OLLAMA.api_url = CONFIG.ollama_url
        chat_models = OLLAMA.get_chat_models()
        embed_models = OLLAMA.get_embedding_models()
        return jsonify({
            "ollama_available": OLLAMA.is_available(),
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
            "language", "romaji_enabled", "romaji_system",
            "show_furigana", "current_level", "epub_dir",
            "chat_provider", "chat_api_key", "chat_api_base_url",
        ]:
            if key in data:
                setattr(CONFIG, key, data[key])
        save_config()
        return jsonify({"success": True})

    @app.route("/api/settings", methods=["GET"])
    def get_settings():
        return jsonify({k: v for k, v in CONFIG.__dict__.items() if not k.startswith("_")})

    # ── API: Knowledge Base ──────────────────────────────────────────

    @app.route("/api/kb/build", methods=["POST"])
    def build_knowledge_base():
        data = request.json or {}
        epub_dir = data.get("epub_dir", "") or str(CONFIG.get_epub_dir())
        collection_name = data.get("collection_name", "")

        epub_path = Path(epub_dir)
        if not epub_path.exists():
            return jsonify({"success": False, "error": f"Directory not found: {epub_dir}"})

        if not CONFIG.embedding_model:
            models = OLLAMA.get_embedding_models()
            if models:
                CONFIG.embedding_model = models[0]
                save_config()
            else:
                return jsonify({"success": False, "error": "No embedding model available. Install one with: ollama pull nomic-embed-text"})

        try:
            files, chunks = KB_BUILDER.build_from_directory(epub_path, collection_name)
            return jsonify({"success": True, "files": files, "chunks": chunks})
        except Exception as e:
            logger.error("[KB] Build error: %s", e)
            return jsonify({"success": False, "error": str(e)})

    @app.route("/api/kb/collections")
    def list_collections():
        collections = CHROMA.list_collections()
        stats = CHROMA.get_stats()
        return jsonify({"collections": [{"name": c, "count": stats.get(c, 0)} for c in collections]})

    @app.route("/api/kb/collections/<name>", methods=["DELETE"])
    def delete_collection(name):
        success = CHROMA.delete_collection(name)
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
            results = KB_BUILDER.search(query, collections, top_k)
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
        learned_kanji = set(data.get("learned_kanji", []))

        if not text:
            return jsonify({"success": False, "error": "Text is required"})

        result = annotate_text(text, show_furigana=show_furigana, show_romaji=show_romaji, learned_kanji=learned_kanji)

        return jsonify({
            "success": True,
            "original": result.original,
            "html_ruby": result.html_ruby,
            "html_romaji": result.html_romaji,
            "plain_reading": result.plain_reading,
            "tokens": [{
                "surface": t.surface,
                "reading": t.reading,
                "pos": t.pos,
                "is_kanji": t.is_kanji,
                "is_kana": t.is_kana,
                "is_mixed": t.is_mixed,
            } for t in result.tokens],
        })

    @app.route("/api/japanese/tokenize", methods=["POST"])
    def tokenize_japanese():
        data = request.json or {}
        text = data.get("text", "")
        if not text:
            return jsonify({"success": False, "error": "Text is required"})

        tokens = tokenize(text)
        return jsonify({
            "success": True,
            "tokens": [{
                "surface": t.surface,
                "lemma": t.lemma,
                "reading": t.reading,
                "pos": t.pos,
                "is_kanji": t.is_kanji,
                "is_kana": t.is_kana,
            } for t in tokens],
        })

    @app.route("/api/japanese/level", methods=["POST"])
    def detect_level():
        data = request.json or {}
        text = data.get("text", "")
        if not text:
            return jsonify({"success": False, "error": "Text is required"})
        level = detect_japanese_level(text)
        return jsonify({"success": True, "level": level})

    @app.route("/api/japanese/romaji", methods=["POST"])
    def convert_romaji():
        data = request.json or {}
        kana = data.get("kana", "")
        system = data.get("system", "hepburn")
        if not kana:
            return jsonify({"success": False, "error": "Kana text is required"})
        romaji = kana_to_romaji(kana, system)
        return jsonify({"success": True, "romaji": romaji})

    # ── API: Learning ────────────────────────────────────────────────

    @app.route("/api/learning/progress")
    def get_progress():
        return jsonify({"success": True, "data": PROGRESS.get_progress_summary()})

    @app.route("/api/learning/progress", methods=["POST"])
    def update_progress():
        data = request.json or {}
        if "current_level" in data:
            PROGRESS.set_current_level(data["current_level"])
        if "learned_kanji" in data:
            for k in data["learned_kanji"]:
                PROGRESS.learn_kanji(k)
        return jsonify({"success": True})

    @app.route("/api/learning/srs/stats")
    def srs_stats():
        return jsonify({"success": True, "data": SRS.get_stats()})

    @app.route("/api/learning/srs/due")
    def srs_due():
        limit = request.args.get("limit", 20, type=int)
        level = request.args.get("level", "")
        cards = SRS.get_due_cards(limit=limit, level=level)
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

        card = SRS.review_card(card_id, quality)
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
        SRS.add_card(card)
        return jsonify({"success": True, "card": card.to_dict()})

    # ── API: Exercise Generation ──────────────────────────────────────

    @app.route("/api/exercises/multiple_choice", methods=["POST"])
    def gen_multiple_choice():
        data = request.json or {}
        items = data.get("items", [])
        num_choices = data.get("num_choices", 4)
        if not items:
            return jsonify({"success": False, "error": "Items required"})
        exercises = EXERCISE_GEN.generate_multiple_choice(items, num_choices)
        return jsonify({"success": True, "exercises": exercises})

    @app.route("/api/exercises/reading_quiz", methods=["POST"])
    def gen_reading_quiz():
        data = request.json or {}
        vocabulary = data.get("vocabulary", [])
        learned_kanji = set(data.get("learned_kanji", []))
        if not vocabulary:
            return jsonify({"success": False, "error": "Vocabulary required"})
        exercises = EXERCISE_GEN.generate_reading_quiz(vocabulary, learned_kanji)
        return jsonify({"success": True, "exercises": exercises})

    # ── API: Chat ─────────────────────────────────────────────────────

    @app.route("/api/chat", methods=["POST"])
    def chat():
        data = request.json or {}
        message = data.get("message", "")
        model = data.get("model", CONFIG.chat_model)
        use_kb = data.get("use_kb", True)
        collections = data.get("collections", None)
        language = data.get("language", CONFIG.language)

        if not message:
            return jsonify({"success": False, "error": "Message required"})

        if not model:
            models = OLLAMA.get_chat_models()
            if models:
                model = models[0]
            else:
                return jsonify({"success": False, "error": "No chat model available"})

        system_prompt = _build_system_prompt(language)

        context = ""
        if use_kb:
            try:
                context = KB_BUILDER.build_context(message, collections)
            except Exception:
                pass

        messages = [{"role": "system", "content": system_prompt}]
        if context:
            messages.append({"role": "system", "content": f"参考资料：\n{context}"})
        messages.append({"role": "user", "content": message})

        response_text = OLLAMA.chat_complete(messages, model)
        return jsonify({"success": True, "response": response_text})

    @app.route("/api/chat/stream", methods=["POST"])
    def chat_stream():
        data = request.json or {}
        message = data.get("message", "")
        model = data.get("model", CONFIG.chat_model)
        use_kb = data.get("use_kb", True)
        collections = data.get("collections", None)
        language = data.get("language", CONFIG.language)

        if not model:
            models = OLLAMA.get_chat_models()
            model = models[0] if models else ""

        system_prompt = _build_system_prompt(language)

        context = ""
        if use_kb:
            try:
                context = KB_BUILDER.build_context(message, collections)
            except Exception:
                pass

        messages = [{"role": "system", "content": system_prompt}]
        if context:
            messages.append({"role": "system", "content": f"参考资料：\n{context}"})
        messages.append({"role": "user", "content": message})

        def generate():
            for chunk in OLLAMA.chat_stream(messages, model):
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

    # ── Helper ───────────────────────────────────────────────────────

    def _build_system_prompt(language: str) -> str:
        lang_names = {"ja": "Japanese", "zh": "Chinese", "en": "English", "ko": "Korean", "fr": "French", "de": "German", "es": "Spanish"}
        target = lang_names.get(language, "Japanese")

        return (
            f"You are Xuehua, a {target} language learning assistant. "
            f"Your role is to help learners practice {target} through clear explanations, "
            f"example sentences, and patient guidance. Follow these rules:\n\n"
            f"1. Always provide furigana (reading aids) for kanji when discussing Japanese text.\n"
            f"2. When giving example sentences, include: the Japanese text, furigana readings, "
            f"romaji (if helpful for beginners), and the translation.\n"
            f"3. Progressively increase complexity based on the learner's level.\n"
            f"4. Explain grammar points with clear, simple examples.\n"
            f"5. Use the reference materials provided to give accurate, contextual answers.\n"
            f"6. When the learner makes mistakes, gently correct them and explain why.\n"
            f"7. Respond in the same language the learner uses, but include {target} examples.\n"
        )

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host=CONFIG.host, port=CONFIG.port, debug=True)