"""EPUB parser and knowledge base builder for Xuehua.

Reads EPUB files, extracts text content, chunks it, generates embeddings,
and stores them in ChromaDB for RAG retrieval.
"""

from __future__ import annotations

import hashlib
import logging
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .config import Config
from .constants import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE, MIN_CHUNK_LENGTH
from .ollama_client import OllamaClient
from .vector_db import VectorDBBase

logger = logging.getLogger(__name__)


class EPUBParser:
    """Parse EPUB files and extract structured text content."""

    def __init__(self):
        self._toc_pattern = re.compile(r"(第[一二三四五六七八九十百千万\d]+[章节目课]|[Cc]hapter|\d+\.)")

    def parse(self, epub_path: Path) -> List[Dict]:
        """Parse an EPUB file into structured sections.

        Returns list of dicts with keys: title, content, chapter_order
        """
        try:
            from ebooklib import epub
        except ImportError:
            logger.error("[EPUB] ebooklib not installed. Run: pip install ebooklib")
            return []

        try:
            book = epub.read_epub(str(epub_path), options={"ignore_ncx": True})
        except Exception as e:
            logger.error("[EPUB] Failed to read %s: %s", epub_path.name, e)
            return []

        sections = []
        order = 0

        spine_ids = [item_id for item_id, _ in book.spine]
        id_to_item = {item.get_id(): item for item in book.get_items_of_type(9)}

        for item_id in spine_ids:
            item = id_to_item.get(item_id)
            if item is None:
                continue

            try:
                content = item.get_content().decode("utf-8", errors="replace")
            except Exception:
                continue

            text = self._html_to_text(content)
            if not text.strip():
                continue

            title = self._extract_title(content) or f"Section {order + 1}"

            chapter_match = self._toc_pattern.search(title)
            chapter_order = order
            if chapter_match:
                try:
                    num_part = re.search(r"\d+", chapter_match.group())
                    if num_part:
                        chapter_order = int(num_part.group())
                except (ValueError, AttributeError):
                    pass

            sections.append({
                "title": title.strip(),
                "content": text.strip(),
                "chapter_order": chapter_order,
                "source_file": epub_path.name,
                "item_id": item_id,
            })
            order += 1

        sections.sort(key=lambda s: s["chapter_order"])
        return sections

    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML to plain text using BeautifulSoup."""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return self._html_to_text_regex(html_content)

        soup = BeautifulSoup(html_content, "lxml")

        # Handle ruby annotations: <ruby>漢字<rt>かんじ</rt></ruby> → 漢字（かんじ）
        for ruby in soup.find_all("ruby"):
            rb = ruby.find("rb")
            rt = ruby.find("rt")
            if rb and rt:
                ruby.replace_with(f"{rb.get_text()}（{rt.get_text()}）")
            elif rt:
                ruby.replace_with(rt.get_text())

        text = soup.get_text(separator="\n")

        # Normalize whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)

        return text.strip()

    def _html_to_text_regex(self, html_content: str) -> str:
        """Fallback: convert HTML to plain text using regex."""
        text = html_content

        text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"</p>", "\n\n", text, flags=re.IGNORECASE)
        text = re.sub(r"</div>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"</li>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"</h[1-6]>", "\n\n", text, flags=re.IGNORECASE)
        text = re.sub(r"</tr>", "\n", text, flags=re.IGNORECASE)

        text = re.sub(r"<ruby>.*?<rb>([^<]+)</rb>.*?<rt>([^<]+)</rt>.*?</ruby>", r"\1（\2）", text)
        text = re.sub(r"<rp>[^<]*</rp>", "", text)
        text = re.sub(r"<rt>[^<]*</rt>", "", text)

        text = re.sub(r"<[^>]+>", "", text)

        text = re.sub(r"&nbsp;", " ", text)
        text = re.sub(r"&lt;", "<", text)
        text = re.sub(r"&gt;", ">", text)
        text = re.sub(r"&amp;", "&", text)
        text = re.sub(r"&quot;", '"', text)
        text = re.sub(r"&#\d+;", "", text)

        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)

        return text.strip()

    def _extract_title(self, html_content: str) -> Optional[str]:
        """Extract title from HTML content."""
        match = re.search(r"<title>([^<]+)</title>", html_content, re.IGNORECASE)
        if match and match.group(1).strip():
            return match.group(1).strip()

        for level in range(1, 7):
            match = re.search(
                rf"<h{level}[^>]*>([^<]+)</h{level}>", html_content, re.IGNORECASE
            )
            if match and match.group(1).strip():
                return match.group(1).strip()
        return None


class KnowledgeBaseBuilder:
    """Build and manage knowledge bases from EPUB files."""

    def __init__(self, chroma: VectorDBBase, ollama: OllamaClient, config: Config):
        self.chroma = chroma
        self.ollama = ollama
        self.config = config
        self.parser = EPUBParser()

    def build_from_directory(self, epub_dir: Path, collection_name: str = "") -> Tuple[int, int]:
        """Build knowledge base from all EPUB files in a directory.

        Returns (files_processed, chunks_created)
        """
        if not epub_dir.exists():
            logger.error("[KB] Directory not found: %s", epub_dir)
            return 0, 0

        epub_files = list(epub_dir.glob("*.epub"))
        if not epub_files:
            logger.error("[KB] No EPUB files found in %s", epub_dir)
            return 0, 0

        if not collection_name:
            collection_name = epub_dir.name

        total_chunks = 0
        files_processed = 0

        for epub_path in epub_files:
            logger.info("[KB] Processing: %s", epub_path.name)
            print(f"[KB] Processing: {epub_path.name}", file=sys.stderr)

            sections = self.parser.parse(epub_path)
            if not sections:
                logger.warning("[KB] No sections extracted from %s", epub_path.name)
                continue

            chunks_created = self._index_sections(sections, collection_name, epub_path.name)
            total_chunks += chunks_created
            files_processed += 1

            print(
                f"[KB]   {epub_path.name}: {len(sections)} sections, {chunks_created} chunks",
                file=sys.stderr,
            )

        print(
            f"[KB] Complete: {files_processed} files, {total_chunks} chunks",
            file=sys.stderr,
        )
        return files_processed, total_chunks

    def build_from_file(self, epub_path: Path, collection_name: str = "") -> Tuple[int, int]:
        """Build knowledge base from a single EPUB file."""
        if not collection_name:
            collection_name = epub_path.stem

        sections = self.parser.parse(epub_path)
        if not sections:
            return 0, 0

        chunks_created = self._index_sections(sections, collection_name, epub_path.name)
        return 1, chunks_created

    def _index_sections(
        self, sections: List[Dict], collection_name: str, filename: str
    ) -> int:
        """Index sections into ChromaDB."""
        if not self.config.embedding_model:
            print("[KB] No embedding model configured, skipping indexing", file=sys.stderr)
            return 0

        documents = []
        embeddings = []
        metadatas = []
        ids = []

        for section in sections:
            content = section["content"]
            chunks = self._chunk_text(
                content, self.config.chunk_size, self.config.chunk_overlap
            )

            for i, chunk in enumerate(chunks):
                if len(chunk.strip()) < MIN_CHUNK_LENGTH:
                    continue

                try:
                    emb = self.ollama.embed(chunk, self.config.embedding_model)
                    if not emb:
                        continue

                    doc_id = hashlib.md5(
                        f"{filename}_{section.get('chapter_order', 0)}_{i}".encode()
                    ).hexdigest()

                    documents.append(chunk)
                    embeddings.append(emb)
                    metadatas.append({
                        "source": collection_name,
                        "file": filename,
                        "section_title": section.get("title", ""),
                        "chunk": i,
                    })
                    ids.append(doc_id)
                except Exception as e:
                    logger.error("[KB] Error embedding chunk %d of %s: %s", i, filename, e)
                    continue

        if documents:
            self.chroma.add_documents(collection_name, documents, embeddings, metadatas, ids)

        return len(documents)

    def _chunk_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Split text into overlapping chunks."""
        if overlap >= chunk_size:
            overlap = max(0, chunk_size - 1)
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk)
            start = end - overlap
        return chunks

    def search(
        self, query: str, collections: List[str] = None, top_k: int = 15
    ) -> List[Dict]:
        """Search knowledge base for relevant content."""
        if not self.config.embedding_model:
            return []

        try:
            query_emb = self.ollama.embed(query, self.config.embedding_model)
        except Exception as e:
            logger.error("[KB] Error embedding query: %s", e)
            return []

        if collections is None:
            collections = self.chroma.list_collections()

        all_results = []
        seen_docs = set()

        for col_name in collections:
            if not self.chroma.collection_exists(col_name):
                continue

            results = self.chroma.search(col_name, query_emb, top_k=top_k)

            for r in results:
                if r["distance"] >= self.config.rag_distance_threshold:
                    continue

                doc_id = r.get("id", "")
                if doc_id in seen_docs:
                    continue
                seen_docs.add(doc_id)

                r["collection"] = col_name
                all_results.append(r)

        all_results.sort(key=lambda x: x["distance"])
        return all_results

    def build_context(self, query: str, collections: List[str] = None, max_length: int = 3000) -> str:
        """Build RAG context string from search results."""
        results = self.search(query, collections)
        if not results:
            return ""

        context_parts = []
        total_len = 0

        for r in results:
            source = r.get("metadata", {}).get("file", "")
            section = r.get("metadata", {}).get("section_title", "")
            header = f"[{source}"
            if section:
                header += f" - {section}"
            header += "]"

            text = r["document"]
            entry = f"{header}\n{text}"
            if total_len + len(entry) > max_length:
                break
            context_parts.append(entry)
            total_len += len(entry)

        return "\n\n".join(context_parts)