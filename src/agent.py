from typing import Callable
from .store import EmbeddingStore

class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.
    """

    def __init__(self, store: 'EmbeddingStore', llm_fn: Callable[[str], str]) -> None:
        # Lưu tham chiếu đến store (nơi chứa dữ liệu) và llm_fn (hàm gọi AI)
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        # Gọi đúng tên hàm 'search'
        search_results = self.store.search(query=question, top_k=top_k)
        
        # Lấy 'content' thay vì 'text'
        relevant_chunks = [res["content"] for res in search_results]
        
        context = "\n---\n".join(relevant_chunks)
        prompt = f"Context: {context}\n\nQuestion: {question}"
        
        return self.llm_fn(prompt)