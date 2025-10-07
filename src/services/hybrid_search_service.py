"""
ハイブリッド検索サービス
BM25（Sparse）+ Vector Search（Dense）の組み合わせ
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from loguru import logger

from ..models.search import SearchResult
from ..utils.query_processor import QueryProcessor
from .search_service import SearchService
from .embedding_service import EmbeddingService
from ..database.repositories.article_repository import ArticleRepository


@dataclass
class HybridSearchResult:
    """ハイブリッド検索結果"""
    article_id: int
    title: str
    content: str
    sparse_score: float  # BM25スコア
    dense_score: float   # Vector類似度スコア
    hybrid_score: float  # 統合スコア
    search_type: str     # "sparse", "dense", "hybrid"


class HybridSearchService:
    """
    ハイブリッド検索サービス
    
    実装方針:
    1. Sparse Search (BM25) - キーワード一致重視
    2. Dense Search (Vector) - 意味的類似度重視  
    3. Score Fusion - 両方の結果を統合
    """
    
    def __init__(self):
        self.query_processor = QueryProcessor()
        self.search_service = SearchService()
        self.embedding_service = EmbeddingService()
        self.article_repo = ArticleRepository()
        
        # ハイブリッド検索の重み設定
        self.sparse_weight = 0.6  # BM25の重み
        self.dense_weight = 0.4   # Vector検索の重み
        
        logger.info("HybridSearchService initialized")
    
    async def hybrid_search(
        self,
        query: str,
        limit: int = 10,
        sparse_weight: Optional[float] = None,
        dense_weight: Optional[float] = None
    ) -> List[HybridSearchResult]:
        """
        ハイブリッド検索の実行
        """
        logger.info(f"Hybrid search started: '{query}' (limit={limit})")
        
        # 重みを動的に設定可能
        if sparse_weight is not None:
            self.sparse_weight = sparse_weight
        if dense_weight is not None:
            self.dense_weight = dense_weight
        
        # クエリ処理
        processed = self.query_processor.process_query(query)
        sparse_query = processed['recommended_query']
        
        logger.info(f"Query processing - Original: '{query}' → Sparse: '{sparse_query}'")
        
        # 並列で検索実行
        sparse_task = self._sparse_search(sparse_query, limit * 2)  # より多くの結果を取得
        dense_task = self._dense_search(query, limit * 2)
        
        sparse_results, dense_results = await asyncio.gather(
            sparse_task, dense_task, return_exceptions=True
        )
        
        # エラーハンドリング
        if isinstance(sparse_results, Exception):
            logger.error(f"Sparse search failed: {sparse_results}")
            sparse_results = []
        if isinstance(dense_results, Exception):
            logger.error(f"Dense search failed: {dense_results}")
            dense_results = []
        
        # 結果の統合
        hybrid_results = self._fuse_results(sparse_results, dense_results, limit)
        
        logger.info(f"Hybrid search completed: {len(hybrid_results)} results")
        return hybrid_results
    
    async def _sparse_search(self, query: str, limit: int) -> List[SearchResult]:
        """Sparse検索（BM25ベース）"""
        try:
            # SearchServiceのsemantic_searchを利用
            # semantic_searchは内部でBM25相当の機能を持っている
            results = self.search_service.semantic_search(query, limit)
            logger.debug(f"Sparse search found {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Sparse search error: {e}")
            return []
    
    async def _dense_search(self, query: str, limit: int) -> List[SearchResult]:
        """Dense検索（Vector Similarity）"""
        try:
            # ChromaDBのベクター検索を直接活用
            chroma_collection = self.search_service.collection
            
            # クエリのベクター化
            query_embedding = self.embedding_service.generate_embedding(query)
            
            # ベクター検索実行
            chroma_results = chroma_collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                include=['documents', 'metadatas', 'distances']
            )
            
            # SearchResult形式に変換
            results = []
            if chroma_results['ids'] and chroma_results['ids'][0]:
                for i, article_id in enumerate(chroma_results['ids'][0]):
                    try:
                        # メタデータからタイトルと記事情報を取得
                        metadata = chroma_results['metadatas'][0][i]
                        distance = chroma_results['distances'][0][i]
                        
                        # 距離を類似度スコアに変換（0-1の範囲）
                        similarity_score = max(0, 1 - distance)
                        
                        # 記事情報の取得（メタデータから簡易構築）
                        try:
                            # ChromaDBのメタデータから記事情報を取得
                            from ..models.esa_models import Article
                            from datetime import datetime
                            
                            article = Article(
                                number=int(article_id),
                                name=metadata.get('name', f'Article {article_id}'),
                                full_name=metadata.get('name', f'Article {article_id}'),
                                wip=metadata.get('wip', False),
                                body_md=chroma_results['documents'][0][i],
                                body_html="",
                                created_at=datetime.fromisoformat(metadata['created_at']) if metadata.get('created_at') else datetime.now(),
                                updated_at=datetime.fromisoformat(metadata['updated_at']) if metadata.get('updated_at') else datetime.now(),
                                url=metadata.get('url', ''),
                                tags=metadata.get('tags', '').split(',') if metadata.get('tags') else [],
                                category=metadata.get('category', ''),
                                created_by_id=metadata.get('created_by_id'),
                                updated_by_id=metadata.get('created_by_id'),
                                processed_text=chroma_results['documents'][0][i],
                                embedding=None,
                                summary=None
                            )
                            
                            result = SearchResult(
                                article=article,
                                score=similarity_score,
                                matched_text=f"Vector similarity: {similarity_score:.3f}",
                                highlights=[]
                            )
                            results.append(result)
                        except Exception as meta_error:
                            logger.warning(f"Metadata processing error for article {article_id}: {meta_error}")
                            continue
                    except Exception as e:
                        logger.warning(f"Error processing dense result {i}: {e}")
                        continue
            
            logger.debug(f"Dense search found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Dense search error: {e}")
            return []
    
    def _fuse_results(
        self, 
        sparse_results: List[SearchResult], 
        dense_results: List[SearchResult], 
        limit: int
    ) -> List[HybridSearchResult]:
        """
        検索結果の統合（Score Fusion）
        
        使用手法: RRF (Reciprocal Rank Fusion) + Score Weighting
        """
        # 記事IDをキーとした結果辞書
        article_scores: Dict[int, Dict[str, Any]] = {}
        
        # Sparse結果の処理
        for rank, result in enumerate(sparse_results, 1):
            article_id = result.article.number
            if article_id not in article_scores:
                article_scores[article_id] = {
                    'article': result.article,
                    'sparse_score': 0.0,
                    'dense_score': 0.0,
                    'sparse_rank': float('inf'),
                    'dense_rank': float('inf')
                }
            
            article_scores[article_id]['sparse_score'] = result.score
            article_scores[article_id]['sparse_rank'] = rank
        
        # Dense結果の処理
        for rank, result in enumerate(dense_results, 1):
            article_id = result.article.number
            if article_id not in article_scores:
                article_scores[article_id] = {
                    'article': result.article,
                    'sparse_score': 0.0,
                    'dense_score': 0.0,
                    'sparse_rank': float('inf'),
                    'dense_rank': float('inf')
                }
            
            article_scores[article_id]['dense_score'] = result.score
            article_scores[article_id]['dense_rank'] = rank
        
        # ハイブリッドスコアの計算
        hybrid_results = []
        for article_id, scores in article_scores.items():
            # RRF (Reciprocal Rank Fusion) スコア
            k = 60  # RRFパラメータ
            rrf_score = (
                1 / (k + scores['sparse_rank']) + 
                1 / (k + scores['dense_rank'])
            )
            
            # 重み付きスコア
            weighted_score = (
                self.sparse_weight * scores['sparse_score'] + 
                self.dense_weight * scores['dense_score']
            )
            
            # 最終的なハイブリッドスコア（RRF + 重み付き）
            final_score = 0.7 * weighted_score + 0.3 * rrf_score
            
            # 検索タイプの判定
            search_type = "hybrid"
            if scores['sparse_rank'] == float('inf'):
                search_type = "dense"
            elif scores['dense_rank'] == float('inf'):
                search_type = "sparse"
            
            hybrid_result = HybridSearchResult(
                article_id=article_id,
                title=scores['article'].name,
                content=scores['article'].body_md[:500] + "..." if len(scores['article'].body_md) > 500 else scores['article'].body_md,
                sparse_score=scores['sparse_score'],
                dense_score=scores['dense_score'],
                hybrid_score=final_score,
                search_type=search_type
            )
            hybrid_results.append(hybrid_result)
        
        # スコア順でソート
        hybrid_results.sort(key=lambda x: x.hybrid_score, reverse=True)
        
        # 上位limit件を返す
        return hybrid_results[:limit]
    
    def explain_search(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """
        検索プロセスの詳細説明（デバッグ用）
        """
        # クエリ処理分析
        processed = self.query_processor.process_query(query)
        
        # 各検索手法の結果を取得
        results = asyncio.run(self.hybrid_search(query, limit))
        
        explanation = {
            "original_query": query,
            "query_processing": {
                "normalized": processed['normalized_query'],
                "keywords": processed['keywords'],
                "technical_terms": processed['technical_terms'],
                "recommended": processed['recommended_query']
            },
            "search_weights": {
                "sparse_weight": self.sparse_weight,
                "dense_weight": self.dense_weight
            },
            "results": [
                {
                    "title": r.title,
                    "hybrid_score": round(r.hybrid_score, 3),
                    "sparse_score": round(r.sparse_score, 3),
                    "dense_score": round(r.dense_score, 3),
                    "search_type": r.search_type
                }
                for r in results
            ],
            "result_distribution": {
                "sparse_only": len([r for r in results if r.search_type == "sparse"]),
                "dense_only": len([r for r in results if r.search_type == "dense"]),
                "hybrid": len([r for r in results if r.search_type == "hybrid"])
            }
        }
        
        return explanation
