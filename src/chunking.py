from __future__ import annotations
import math
import re
from typing import Callable, List, Optional, Dict

# Giả định file .store đã có class EmbeddingStore
#from .store import EmbeddingStore 

class FixedSizeChunker:
    """Chia văn bản thành các đoạn có kích thước cố định với phần chồng lấn (overlap)."""
    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks

class SentenceChunker:
    """Chia văn bản theo số lượng câu tối đa trong mỗi đoạn."""
    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text.strip():
            return []
        
        # Tách câu dựa trên các dấu kết thúc phổ biến
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        
        chunks = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            chunk_text = " ".join(sentences[i : i + self.max_sentences_per_chunk]).strip()
            if chunk_text:
                chunks.append(chunk_text)
        return chunks

class RecursiveChunker:
    """Chia văn bản đệ quy theo thứ tự ưu tiên của các ký tự phân tách."""
    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if len(current_text) <= self.chunk_size:
            return [current_text]
        
        if not remaining_separators:
            return [current_text[i : i + self.chunk_size] for i in range(0, len(current_text), self.chunk_size)]

        sep = remaining_separators[0]
        next_seps = remaining_separators[1:]
        
        final_chunks = []
        # Tách bằng separator hiện tại
        parts = current_text.split(sep) if sep != "" else list(current_text)
        
        temp_text = ""
        for p in parts:
            if len(temp_text) + (len(sep) if temp_text else 0) + len(p) <= self.chunk_size:
                temp_text += (sep if temp_text else "") + p
            else:
                if temp_text:
                    final_chunks.append(temp_text)
                
                # Nếu phần 'p' đơn lẻ vẫn quá dài, dùng separator tiếp theo để chia nhỏ nó
                if len(p) > self.chunk_size:
                    final_chunks.extend(self._split(p, next_seps))
                else:
                    temp_text = p
        
        if temp_text:
            final_chunks.append(temp_text)
            
        return final_chunks

# --- Các hàm toán học bổ trợ ---

def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))

def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Tính Cosine Similarity giữa hai vector."""
    dot_product = _dot(vec_a, vec_b)
    norm_a = math.sqrt(_dot(vec_a, vec_a))
    norm_b = math.sqrt(_dot(vec_b, vec_b))
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return dot_product / (norm_a * norm_b)

# --- Agent và So sánh ---

class KnowledgeBaseAgent:
    """Agent trả lời câu hỏi bằng cách sử dụng cơ sở kiến thức vector (RAG)."""
    def __init__(self, store: 'EmbeddingStore', llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        # 1. Retrieval
        relevant_chunks = self.store.retrieve(query=question, top_k=top_k)
        
        # 2. Build Prompt
        context = "\n---\n".join(relevant_chunks)
        prompt = (
            f"Dựa vào ngữ cảnh sau đây để trả lời câu hỏi.\n"
            f"Ngữ cảnh:\n{context}\n\n"
            f"Câu hỏi: {question}\n"
            f"Trả lời:"
        )

        # 3. Generation
        return self.llm_fn(prompt)

class ChunkingStrategyComparator:
    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=20),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=2),
            "recursive": RecursiveChunker(chunk_size=chunk_size)
        }
        
        comparison = {}
        for name, strategy in strategies.items():
            chunks = strategy.chunk(text)
            comparison[name] = {
                "count": len(chunks),
                "avg_length": sum(len(c) for c in chunks) / len(chunks) if chunks else 0,
                "chunks": chunks  # ĐỔI TÊN: Từ 'sample_chunks' thành 'chunks'
            }
        return comparison