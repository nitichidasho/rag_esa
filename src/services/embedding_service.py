"""
埋め込みベクトル生成サービス
"""

import numpy as np
import re
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer
from loguru import logger

from ..config.settings import settings


class EmbeddingService:
    """埋め込みベクトル生成サービス"""
    
    def __init__(self):
        self.model_name = settings.hf_model_name
        self.model = None
        # より高品質な日本語対応モデルの候補
        self.fallback_models = [
            "sentence-transformers/all-MiniLM-L6-v2",  # 現在のモデル
            "intfloat/multilingual-e5-base",  # 多言語対応・高性能
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"  # 多言語対応
        ]
        self._load_model()
    
    def _load_model(self):
        """モデルの読み込み（フォールバック対応）"""
        models_to_try = [self.model_name] + self.fallback_models
        
        for model_name in models_to_try:
            try:
                logger.info(f"Loading embedding model: {model_name}")
                self.model = SentenceTransformer(model_name)
                self.model_name = model_name  # 実際に使用されたモデル名を記録
                logger.info(f"Embedding model loaded successfully: {model_name}")
                break
            except Exception as e:
                logger.warning(f"Failed to load model {model_name}: {e}")
                if model_name == models_to_try[-1]:  # 最後のモデルでも失敗
                    logger.error("All embedding models failed to load")
                    raise
    
    def generate_embedding(self, text: str, use_chunking: bool = True) -> List[float]:
        """テキストの埋め込みベクトルを生成（改良版）"""
        if not self.model:
            self._load_model()
        
        try:
            if use_chunking and len(text) > 400:  # 長いテキストはチャンク分割
                return self._generate_chunked_embedding(text)
            else:
                # 短いテキストは従来通り
                processed_text = self._preprocess_text_enhanced(text)
                embedding = self.model.encode(processed_text, normalize_embeddings=True)
                return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return []
    
    def _generate_chunked_embedding(self, text: str) -> List[float]:
        """長いテキストをチャンク分割してベクトル化（情報損失を最小化）"""
        try:
            # テキストを意味のある単位で分割
            chunks = self._split_text_semantically(text)
            
            if not chunks:
                return []
            
            # 各チャンクのベクトルを生成
            chunk_embeddings = []
            for chunk in chunks:
                processed_chunk = self._preprocess_text_enhanced(chunk)
                if processed_chunk:
                    embedding = self.model.encode(processed_chunk, normalize_embeddings=True)
                    chunk_embeddings.append(embedding)
            
            if not chunk_embeddings:
                return []
            
            # チャンクベクトルを統合（重み付き平均）
            chunk_weights = [len(chunk) for chunk in chunks]  # 長さによる重み
            total_weight = sum(chunk_weights)
            
            if total_weight == 0:
                return []
            
            # 重み付き平均でベクトルを統合
            final_embedding = np.zeros_like(chunk_embeddings[0])
            for embedding, weight in zip(chunk_embeddings, chunk_weights):
                final_embedding += embedding * (weight / total_weight)
            
            # 正規化
            norm = np.linalg.norm(final_embedding)
            if norm > 0:
                final_embedding = final_embedding / norm
            
            return final_embedding.tolist()
            
        except Exception as e:
            logger.error(f"Failed to generate chunked embedding: {e}")
            # フォールバック：従来の方法
            processed_text = self._preprocess_text_enhanced(text)
            embedding = self.model.encode(processed_text, normalize_embeddings=True)
            return embedding.tolist()
    
    def _split_text_semantically(self, text: str, max_chunk_size: int = 400) -> List[str]:
        """テキストを意味のある単位で分割"""
        if len(text) <= max_chunk_size:
            return [text]
        
        # 文単位で分割
        sentences = re.split(r'[。！？\.\!\?]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # 句読点を復元
            sentence_with_punct = sentence + "。"
            
            # チャンクサイズを超える場合
            if len(current_chunk + sentence_with_punct) > max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence_with_punct
                else:
                    # 単一文が長すぎる場合は強制分割
                    chunks.extend(self._force_split_long_sentence(sentence_with_punct, max_chunk_size))
            else:
                current_chunk += sentence_with_punct
        
        # 最後のチャンクを追加
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _force_split_long_sentence(self, sentence: str, max_size: int) -> List[str]:
        """長すぎる文を強制分割"""
        chunks = []
        for i in range(0, len(sentence), max_size):
            chunks.append(sentence[i:i + max_size])
        return chunks
    
    def generate_batch_embeddings(self, texts: List[str], use_chunking: bool = True) -> List[List[float]]:
        """複数テキストの埋め込みベクトルを一括生成（改良版）"""
        if not self.model:
            self._load_model()
        
        try:
            results = []
            for text in texts:
                embedding = self.generate_embedding(text, use_chunking=use_chunking)
                results.append(embedding)
            return results
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            return []
    
    def _preprocess_text_enhanced(self, text: str) -> str:
        """強化されたテキスト前処理"""
        if not text:
            return ""
        
        # 基本的なクリーニング
        text = text.replace('\n', ' ').replace('\r', ' ')
        text = text.replace('　', ' ')  # 全角スペースを半角に
        
        # 複数の空白を単一の空白に統合
        text = ' '.join(text.split())
        
        # 特殊文字の正規化（ただし重要な記号は保持）
        text = re.sub(r'[''"""]', '"', text)  # クォート統一
        text = re.sub(r'[‐－−‒–—―]', '-', text)  # ハイフン統一
        
        # URL除去（ただし重要なキーワードは保持）
        text = re.sub(r'https?://[^\s]+', '[URL]', text)
        
        # 最大長制限を緩和（チャンクベースなので）
        max_length = 450  # 以前の512から調整
        if len(text) > max_length:
            # 文の境界で切り詰め
            sentences = re.split(r'[。！？\.\!\?]', text)
            result = ""
            for sentence in sentences:
                if len(result + sentence + "。") <= max_length:
                    result += sentence + "。"
                else:
                    break
            if result:
                text = result
            else:
                text = text[:max_length]
        
        return text.strip()
    
    def _preprocess_text(self, text: str) -> str:
        """従来のテキスト前処理（後方互換性）"""
        return self._preprocess_text_enhanced(text)
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """2つの埋め込みベクトル間のコサイン類似度を計算"""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # コサイン類似度の計算
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
        except Exception as e:
            logger.error(f"Failed to calculate similarity: {e}")
            return 0.0
