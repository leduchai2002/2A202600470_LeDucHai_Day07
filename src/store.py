from __future__ import annotations
import math
from typing import Any, Callable

from .chunking import _dot, compute_similarity
from .embeddings import _mock_embed
from .models import Document

class EmbeddingStore:
    """
    A vector store for text chunks.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb
            client = chromadb.Client()
            self._collection = client.get_or_create_collection(name=collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None
        try:
            import chromadb
            from chromadb.config import Settings
            
            # Sử dụng EphemeralClient để dữ liệu không bị lưu lại giữa các lần chạy test
            client = chromadb.Client(Settings(is_persistent=False))
            
            # Xóa collection cũ nếu trùng tên để reset size về 0
            try:
                client.delete_collection(name=collection_name)
            except:
                pass
                
            self._collection = client.create_collection(name=collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._store = [] # Reset list trong RAM

    def _make_record(self, doc: Document) -> dict[str, Any]:
        embedding = self._embedding_fn(doc.content)
        metadata = doc.metadata if doc.metadata else {"doc_id": doc.id or "default"}
        
        # SỬA TẠI ĐÂY: Sử dụng _next_index để đảm bảo ID không bao giờ trùng
        # Ngay cả khi bài test truyền vào doc.id giống nhau, ID trong Store vẫn riêng biệt
        unique_id = f"{doc.id}_{self._next_index}" if doc.id else f"chunk_{self._next_index}"
        
        return {
            "id": unique_id,
            "text": doc.content,
            "metadata": metadata,
            "embedding": embedding
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        query_embedding = self._embedding_fn(query)
        scored_records = []
        for rec in records:
            score = compute_similarity(query_embedding, rec["embedding"])
            new_rec = rec.copy()
            new_rec["score"] = score
            new_rec["content"] = rec["text"] # Yêu cầu key 'content' từ bộ test
            scored_records.append(new_rec)
        
        scored_records.sort(key=lambda x: x["score"], reverse=True)
        return scored_records[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """Nhúng tài liệu và lưu trữ chúng."""
        for doc in docs:
            # 1. Tăng index TRƯỚC để tạo ID mới
            self._next_index += 1
            
            # 2. Tạo record với ID đã được cá nhân hóa theo index
            record = self._make_record(doc)
            
            if self._use_chroma and self._collection:
                self._collection.add(
                    ids=[record["id"]],
                    documents=[record["text"]],
                    embeddings=[record["embedding"]],
                    metadatas=[record["metadata"]]
                )
            else:
                self._store.append(record)

    # CÁC HÀM DƯỚI ĐÂY ĐÃ ĐƯỢC THỤT LỀ VÀO TRONG CLASS
    def get_collection_size(self) -> int:
        """Trả về tổng số lượng chunk đang lưu trữ."""
        if self._use_chroma and self._collection:
            return self._collection.count()
        return len(self._store)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Tìm top_k tài liệu tương đồng nhất."""
        if self._use_chroma and self._collection:
            query_embedding = self._embedding_fn(query)
            results = self._collection.query(query_embeddings=[query_embedding], n_results=top_k)
            
            formatted = []
            if results['ids']:
                for i in range(len(results['ids'][0])):
                    formatted.append({
                        "id": results['ids'][0][i],
                        "content": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "score": 1.0 - results['distances'][0][i] if 'distances' in results else 0.0
                    })
            return formatted
        
        return self._search_records(query, self._store, top_k)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        if not metadata_filter:
            return self.search(query, top_k)

        filtered_records = []
        for rec in self._store:
            is_match = all(rec["metadata"].get(k) == v for k, v in metadata_filter.items())
            if is_match:
                filtered_records.append(rec)
        
        return self._search_records(query, filtered_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        initial_count = self.get_collection_size()
        
        if self._use_chroma and self._collection:
            self._collection.delete(where={"doc_id": doc_id})
        else:
            self._store = [rec for rec in self._store if rec["metadata"].get("doc_id") != doc_id]
            
        return self.get_collection_size() < initial_count