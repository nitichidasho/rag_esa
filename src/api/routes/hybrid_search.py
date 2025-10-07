"""
ハイブリッド検索API
Sparse + Dense 検索の統合エンドポイント
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel, Field

from ...services.hybrid_search_service import HybridSearchService, HybridSearchResult
from ...models.search import SearchParams


router = APIRouter()


class HybridSearchResponse(BaseModel):
    """ハイブリッド検索レスポンス"""
    query: str
    processed_query: str
    total_results: int
    search_weights: dict
    results: List[dict]
    performance_info: dict


class HybridSearchRequest(BaseModel):
    """ハイブリッド検索リクエスト"""
    query: str = Field(..., description="検索クエリ")
    limit: int = Field(10, ge=1, le=50, description="結果数上限")
    use_query_processing: bool = Field(True, description="クエリ前処理を使用")
    sparse_weight: Optional[float] = Field(0.6, ge=0, le=1, description="Sparse検索の重み")
    dense_weight: Optional[float] = Field(0.4, ge=0, le=1, description="Dense検索の重み")


# ハイブリッド検索サービスのインスタンス
hybrid_service = HybridSearchService()


@router.post("/hybrid", response_model=HybridSearchResponse)
async def hybrid_search(request: HybridSearchRequest):
    """
    ハイブリッド検索（Sparse + Dense）
    
    特徴:
    - BM25ベースのキーワード検索
    - ベクター埋め込みによる意味的検索
    - RRF + 重み付きスコアによる結果統合
    """
    try:
        # 重みの正規化
        total_weight = request.sparse_weight + request.dense_weight
        if total_weight > 0:
            normalized_sparse = request.sparse_weight / total_weight
            normalized_dense = request.dense_weight / total_weight
        else:
            normalized_sparse = 0.6
            normalized_dense = 0.4
        
        # ハイブリッド検索実行
        results = await hybrid_service.hybrid_search(
            query=request.query,
            limit=request.limit,
            use_query_processing=request.use_query_processing,
            sparse_weight=normalized_sparse,
            dense_weight=normalized_dense
        )
        
        # レスポンス形式に変換
        response_results = []
        for result in results:
            response_results.append({
                "article_id": result.article_id,
                "title": result.title,
                "content": result.content,
                "scores": {
                    "hybrid": round(result.hybrid_score, 3),
                    "sparse": round(result.sparse_score, 3),
                    "dense": round(result.dense_score, 3)
                },
                "search_type": result.search_type
            })
        
        # クエリ処理情報の取得
        processed_info = hybrid_service.query_processor.process_query(request.query)
        
        return HybridSearchResponse(
            query=request.query,
            processed_query=processed_info['recommended_query'] if request.use_query_processing else request.query,
            total_results=len(results),
            search_weights={
                "sparse_weight": normalized_sparse,
                "dense_weight": normalized_dense
            },
            results=response_results,
            performance_info={
                "query_processing_used": request.use_query_processing,
                "extracted_keywords": processed_info['keywords'] if request.use_query_processing else [],
                "technical_terms": processed_info['technical_terms'] if request.use_query_processing else []
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ハイブリッド検索エラー: {str(e)}")


@router.get("/hybrid/explain")
async def explain_hybrid_search(
    query: str = Query(..., description="検索クエリ"),
    limit: int = Query(5, ge=1, le=20, description="結果数")
):
    """
    ハイブリッド検索の詳細説明
    
    検索プロセスの透明化とデバッグ用
    """
    try:
        explanation = hybrid_service.explain_search(query, limit)
        return explanation
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"検索説明エラー: {str(e)}")


@router.get("/hybrid/compare")
async def compare_search_methods(
    query: str = Query(..., description="検索クエリ"),
    limit: int = Query(5, ge=1, le=20, description="結果数")
):
    """
    検索手法の比較
    
    Sparse vs Dense vs Hybrid の結果を並列表示
    """
    try:
        # 各検索手法を並列実行
        hybrid_results = await hybrid_service.hybrid_search(query, limit, use_query_processing=True)
        sparse_results = await hybrid_service.hybrid_search(query, limit, sparse_weight=1.0, dense_weight=0.0)
        dense_results = await hybrid_service.hybrid_search(query, limit, sparse_weight=0.0, dense_weight=1.0)
        
        return {
            "query": query,
            "comparison": {
                "hybrid": {
                    "total_results": len(hybrid_results),
                    "top_3": [
                        {
                            "title": r.title,
                            "hybrid_score": round(r.hybrid_score, 3),
                            "search_type": r.search_type
                        }
                        for r in hybrid_results[:3]
                    ]
                },
                "sparse_only": {
                    "total_results": len(sparse_results),
                    "top_3": [
                        {
                            "title": r.title,
                            "sparse_score": round(r.sparse_score, 3)
                        }
                        for r in sparse_results[:3]
                    ]
                },
                "dense_only": {
                    "total_results": len(dense_results),
                    "top_3": [
                        {
                            "title": r.title,
                            "dense_score": round(r.dense_score, 3)
                        }
                        for r in dense_results[:3]
                    ]
                }
            },
            "analysis": {
                "hybrid_advantages": [
                    "両方の検索手法の利点を統合",
                    "キーワード一致と意味的類似度の両方を考慮",
                    "より包括的で精度の高い結果"
                ],
                "recommendations": "ハイブリッド検索は一般的により良い結果を提供します"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"比較検索エラー: {str(e)}")


@router.get("/hybrid/config")
async def get_hybrid_config():
    """ハイブリッド検索の設定情報"""
    return {
        "current_weights": {
            "sparse_weight": hybrid_service.sparse_weight,
            "dense_weight": hybrid_service.dense_weight
        },
        "supported_features": [
            "BM25 sparse search",
            "Vector dense search", 
            "RRF score fusion",
            "Query preprocessing",
            "Multi-language support"
        ],
        "optimal_use_cases": {
            "sparse_preferred": [
                "正確なキーワード検索",
                "技術用語での検索",
                "固有名詞での検索"
            ],
            "dense_preferred": [
                "概念的な質問",
                "自然言語での質問",
                "類似した内容の検索"
            ],
            "hybrid_optimal": [
                "一般的な検索",
                "複合的な質問",
                "最高の検索精度が必要な場合"
            ]
        }
    }


# 既存の検索APIとの統合ヘルパー
class HybridSearchIntegration:
    """既存システムとのスムーズな統合"""
    
    @staticmethod
    def migrate_from_basic_search(basic_query: str, basic_limit: int = 10):
        """
        既存の基本検索からハイブリッド検索への移行
        """
        return HybridSearchRequest(
            query=basic_query,
            limit=basic_limit,
            use_query_processing=True,
            sparse_weight=0.6,
            dense_weight=0.4
        )
    
    @staticmethod
    def get_compatibility_layer():
        """既存APIとの互換性レイヤー"""
        return {
            "migration_guide": {
                "from": "/api/search/semantic",
                "to": "/api/search/hybrid",
                "benefits": [
                    "より高い検索精度",
                    "自然言語質問の改善された処理",
                    "キーワード検索と意味検索の統合"
                ]
            },
            "backward_compatibility": "既存のsemantic検索APIは引き続き利用可能",
            "recommended_migration": "新しい検索機能にはhybrid検索の使用を推奨"
        }
