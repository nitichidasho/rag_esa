"""
ベクトル処理ユーティリティ
"""

import numpy as np
from typing import List, Tuple


class VectorUtils:
    """ベクトル処理ユーティリティクラス"""
    
    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """コサイン類似度の計算"""
        try:
            a = np.array(vec1)
            b = np.array(vec2)
            
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            similarity = dot_product / (norm_a * norm_b)
            return float(similarity)
        except Exception:
            return 0.0
    
    @staticmethod
    def euclidean_distance(vec1: List[float], vec2: List[float]) -> float:
        """ユークリッド距離の計算"""
        try:
            a = np.array(vec1)
            b = np.array(vec2)
            return float(np.linalg.norm(a - b))
        except Exception:
            return float('inf')
    
    @staticmethod
    def normalize_vector(vector: List[float]) -> List[float]:
        """ベクトルの正規化"""
        try:
            vec = np.array(vector)
            norm = np.linalg.norm(vec)
            if norm == 0:
                return vector
            return (vec / norm).tolist()
        except Exception:
            return vector
    
    @staticmethod
    def find_top_k_similar(
        query_vector: List[float],
        vectors: List[List[float]],
        k: int = 10
    ) -> List[Tuple[int, float]]:
        """最も類似度の高いk個のベクトルを取得"""
        similarities = []
        
        for i, vec in enumerate(vectors):
            similarity = VectorUtils.cosine_similarity(query_vector, vec)
            similarities.append((i, similarity))
        
        # 類似度で降順ソート
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:k]
    
    @staticmethod
    def vector_mean(vectors: List[List[float]]) -> List[float]:
        """ベクトルの平均を計算"""
        if not vectors:
            return []
        
        try:
            vectors_array = np.array(vectors)
            mean_vector = np.mean(vectors_array, axis=0)
            return mean_vector.tolist()
        except Exception:
            return vectors[0] if vectors else []
    
    @staticmethod
    def is_valid_vector(vector: List[float], expected_dim: int = None) -> bool:
        """ベクトルの妥当性をチェック"""
        if not vector:
            return False
        
        # すべて数値かチェック
        try:
            float_vector = [float(x) for x in vector]
        except (ValueError, TypeError):
            return False
        
        # 次元数チェック
        if expected_dim and len(vector) != expected_dim:
            return False
        
        # NaNや無限大値のチェック
        if any(np.isnan(x) or np.isinf(x) for x in float_vector):
            return False
        
        return True
