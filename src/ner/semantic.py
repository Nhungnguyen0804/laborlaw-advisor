import json
import numpy as np
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from src.utils.paths import EMB_JSON
file_path = 'src/ner/semantic.txt'
class SemanticSearch:
    def __init__(self, embedding_file_path: str, model_name: str = "keepitreal/vietnamese-sbert"):
        """Load chunks với embeddings từ file JSON"""
        print(f"Đang load embeddings từ {embedding_file_path}...")
        with open(embedding_file_path, 'r', encoding='utf-8') as f:
            self.chunks = json.load(f)
        
        # Chuyển embeddings sang numpy array
        self.embeddings = np.array([chunk['embedding'] for chunk in self.chunks])
        print(f"Đã load {len(self.chunks)} chunks")
        
        # Load model để embed query 
        print(f"Đang load model {model_name}...")
        self.model = SentenceTransformer(model_name)
        print("Load model xong!")
    
    def get_query_embedding(self, query: str) -> np.ndarray:
        """Sinh embedding cho câu query bằng SentenceTransformer"""
        embedding = self.model.encode(query, normalize_embeddings=True)
        return embedding
    
    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Tính cosine similarity giữa 2 vectors"""
        # Nếu đã normalize thì cosine similarity = dot product
        return np.dot(vec1, vec2)
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
   
        
        # Sinh embedding cho query
        query_embedding = self.get_query_embedding(query)
        
        # Tính similarity với tất cả chunks 
        similarities = np.dot(self.embeddings, query_embedding)
        
        # Lấy top_k có score cao nhất
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Tạo kết quả
        results = []
        for rank, idx in enumerate(top_indices, 1):
            chunk = self.chunks[idx].copy()
            chunk['similarity_score'] = float(similarities[idx])
            chunk['rank'] = rank
            
            chunk.pop('embedding', None)# Xóa embedding để không hiển thị vì dài
            results.append(chunk)
        
        return results
    
    def display_results(self, query, results: List[Dict[str, Any]]):
        with open(file_path, "a", encoding="utf-8") as f:
           
            f.write('--------------------------')
            f.write(f"Câu hỏi: {query}\n")
            for result in results:
                metadata = result.get('metadata', {})

                

                # Score
                f.write(f"Score: {result.get('similarity_score', 0):.4f}\n")

                # Điều + title
                law_name = metadata.get('law_name', 'N/A')
                article_num = metadata.get('article_num', 'N/A')
                chapter_title = metadata.get('chapter_title', '')

                f.write(f"{law_name} - Điều {article_num}\n")
                if chapter_title:
                    f.write(f"{chapter_title}\n")

             
                content = result.get('content', result.get('content_with_context', ''))
                f.write("Nội dung:\n")
                f.write(f"{content}\n")



# DEMO
if __name__ == "__main__":
    EMBEDDING_FILE = EMB_JSON
    MODEL_NAME = "BAAI/bge-m3"  
    
    # Khởi tạo search engine
    search_engine = SemanticSearch(EMBEDDING_FILE, MODEL_NAME)
    
    # Test queries
    test_queries = [
        "Người lao động có quyền gì?",
        "Thời gian làm việc tối đa là bao nhiêu?",
        "Quy định về nghỉ phép hàng năm"
    ]
    
    for query in test_queries:
        results = search_engine.search(query, top_k=3)
        search_engine.display_results(query,results)
 