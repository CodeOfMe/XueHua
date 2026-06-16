"""Vector database abstraction layer for Xuehua.

Supports ChromaDB (default) and in-memory numpy fallback.
"""

from __future__ import annotations

import hashlib
import json
import logging
import shutil
import sys
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class VectorDBBase(ABC):
    """Abstract base class for vector database backends."""

    @property
    @abstractmethod
    def db_type(self) -> str:
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def get_or_create_collection(self, name: str) -> Any:
        pass

    @abstractmethod
    def collection_exists(self, name: str) -> bool:
        pass

    @abstractmethod
    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict],
        ids: List[str],
    ) -> bool:
        pass

    @abstractmethod
    def search(
        self,
        collection_name: str,
        query_embedding: List[float],
        top_k: int = 10,
    ) -> List[Dict]:
        pass

    @abstractmethod
    def list_collections(self) -> List[str]:
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, int]:
        pass

    @abstractmethod
    def delete_collection(self, name: str) -> bool:
        pass


class ChromaDBBackend(VectorDBBase):
    """ChromaDB backend for persistent vector storage."""

    def __init__(self, persist_dir: str):
        self.persist_dir = persist_dir
        self.client = None
        self._collections = {}
        self._init_client()

    def _init_client(self):
        try:
            import chromadb

            backup_dir = Path(self.persist_dir + "_backup")
            try:
                self.client = chromadb.PersistentClient(path=self.persist_dir)
                self.client.list_collections()
            except Exception as e:
                logger.error("[ChromaDB] Init error, attempting recovery: %s", e)
                if Path(self.persist_dir).exists():
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_dir = Path(self.persist_dir) / f"../chroma_backup_{timestamp}"
                    shutil.move(self.persist_dir, str(backup_dir))
                    logger.info("[ChromaDB] Backed up corrupted data to %s", backup_dir)
                Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
                self.client = chromadb.PersistentClient(path=self.persist_dir)
        except ImportError:
            logger.error("[ChromaDB] chromadb package not installed")
            self.client = None

    @property
    def db_type(self) -> str:
        return "chroma"

    @property
    def is_available(self) -> bool:
        return self.client is not None

    def get_or_create_collection(self, name: str) -> Any:
        if self.client is None:
            return None
        return self.client.get_or_create_collection(
            name=name, metadata={"hnsw:space": "cosine"}
        )

    def collection_exists(self, name: str) -> bool:
        if self.client is None:
            return False
        try:
            self.client.get_collection(name=name)
            return True
        except Exception:
            return False

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict],
        ids: List[str],
    ) -> bool:
        if self.client is None:
            return False
        collection = self.get_or_create_collection(collection_name)
        if collection is None:
            return False
        collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )
        return True

    def search(
        self,
        collection_name: str,
        query_embedding: List[float],
        top_k: int = 10,
    ) -> List[Dict]:
        if self.client is None:
            return []
        collection = self.get_or_create_collection(collection_name)
        if collection is None:
            return []
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count()) if collection.count() > 0 else 1,
        )
        output = []
        if results and results.get("documents"):
            for i in range(len(results["documents"][0])):
                item = {
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                    "id": results["ids"][0][i] if results.get("ids") else "",
                    "distance": results["distances"][0][i] if results.get("distances") else 0.0,
                }
                output.append(item)
        return output

    def list_collections(self) -> List[str]:
        if self.client is None:
            return []
        return [c.name for c in self.client.list_collections()]

    def get_stats(self) -> Dict[str, int]:
        if self.client is None:
            return {}
        stats = {}
        for name in self.list_collections():
            try:
                collection = self.client.get_collection(name=name)
                stats[name] = collection.count()
            except Exception:
                stats[name] = 0
        return stats

    def delete_collection(self, name: str) -> bool:
        if self.client is None:
            return False
        try:
            self.client.delete_collection(name=name)
            return True
        except Exception:
            return False


class InMemoryBackend(VectorDBBase):
    """In-memory numpy-based vector database fallback."""

    def __init__(self, persist_dir: str = ""):
        self.persist_dir = persist_dir
        self._collections: Dict[str, Dict] = {}

    @property
    def db_type(self) -> str:
        return "memory"

    @property
    def is_available(self) -> bool:
        return True

    def get_or_create_collection(self, name: str) -> Any:
        if name not in self._collections:
            self._collections[name] = {
                "documents": [],
                "embeddings": [],
                "metadatas": [],
                "ids": [],
            }
        return self._collections[name]

    def collection_exists(self, name: str) -> bool:
        return name in self._collections

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict],
        ids: List[str],
    ) -> bool:
        if collection_name not in self._collections:
            self.get_or_create_collection(collection_name)
        col = self._collections[collection_name]
        col["documents"].extend(documents)
        col["embeddings"].extend(embeddings)
        col["metadatas"].extend(metadatas)
        col["ids"].extend(ids)
        return True

    def search(
        self,
        collection_name: str,
        query_embedding: List[float],
        top_k: int = 10,
    ) -> List[Dict]:
        if collection_name not in self._collections:
            return []
        col = self._collections[collection_name]
        if not col["embeddings"]:
            return []

        query_vec = np.array(query_embedding)
        emb_matrix = np.array(col["embeddings"])
        norms = np.linalg.norm(emb_matrix, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        normed = emb_matrix / norms
        query_norm = np.linalg.norm(query_vec)
        if query_norm == 0:
            return []
        normed_query = query_vec / query_norm
        similarities = normed @ normed_query
        distances = 1 - similarities
        top_indices = np.argsort(distances)[:top_k]

        return [
            {
                "document": col["documents"][i],
                "metadata": col["metadatas"][i],
                "id": col["ids"][i],
                "distance": float(distances[i]),
            }
            for i in top_indices
        ]

    def list_collections(self) -> List[str]:
        return list(self._collections.keys())

    def get_stats(self) -> Dict[str, int]:
        return {name: len(data["documents"]) for name, data in self._collections.items()}

    def delete_collection(self, name: str) -> bool:
        if name in self._collections:
            del self._collections[name]
            return True
        return False


def create_vector_db(persist_dir: str, preferred: str = "chroma") -> VectorDBBase:
    """Create a vector database backend."""
    if preferred == "chroma":
        try:
            backend = ChromaDBBackend(persist_dir)
            if backend.is_available:
                return backend
        except Exception:
            pass

    logger.info("[VectorDB] Falling back to in-memory backend")
    return InMemoryBackend(persist_dir)