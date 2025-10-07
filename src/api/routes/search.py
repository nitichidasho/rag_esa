"""
検索API
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...services.search_service import SearchService
from ...services.hybrid_search_service import HybridSearchService

router = APIRouter()


class SearchRequest(BaseModel):
    """検索リクエスト"""
    query: str
    limit: int = 10
    filters: Optional[Dict[str, Any]] = None
    search_type: str = "semantic"  # "semantic", "hybrid"
    sparse_weight: Optional[float] = None
    dense_weight: Optional[float] = None


@router.post("/")
async def search_articles(request: SearchRequest):
    """記事検索（セマンティック/ハイブリッド対応）"""
    try:
        if request.search_type == "hybrid":
            # ハイブリッド検索を実行
            hybrid_service = HybridSearchService()
            hybrid_results = await hybrid_service.hybrid_search(
                query=request.query,
                limit=request.limit,
                sparse_weight=request.sparse_weight,
                dense_weight=request.dense_weight
            )
            
            # レスポンス形式に変換
            search_results = []
            for result in hybrid_results:
                search_results.append({
                    "article": {
                        "number": result.article_id,
                        "name": result.title,
                        "content": result.content
                    },
                    "score": result.hybrid_score,
                    "sparse_score": result.sparse_score,
                    "dense_score": result.dense_score,
                    "search_type": result.search_type,
                    "matched_text": f"Hybrid search: {result.search_type}",
                    "highlights": []
                })
        else:
            # 従来のセマンティック検索
            search_service = SearchService()
            results = search_service.semantic_search(
                query=request.query,
                limit=request.limit,
                filters=request.filters
            )
            
            # レスポンス形式に変換
            search_results = []
            for result in results:
                search_results.append({
                    "article": {
                        "number": result.article.number,
                        "name": result.article.name,
                        "full_name": result.article.full_name,
                        "wip": result.article.wip,
                        "created_at": result.article.created_at.isoformat() if hasattr(result.article.created_at, 'isoformat') else str(result.article.created_at),
                        "updated_at": result.article.updated_at.isoformat() if hasattr(result.article.updated_at, 'isoformat') else str(result.article.updated_at),
                        "url": result.article.url,
                        "tags": result.article.tags,
                        "category": result.article.category
                    },
                    "score": result.score,
                    "matched_text": result.matched_text,
                    "highlights": result.highlights
                })
        
        return {
            "results": search_results,
            "total": len(search_results),
            "query": request.query,
            "search_type": request.search_type,
            "query_time": 0.5  # 実際の処理時間を計測する場合は実装が必要
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"検索エラー: {str(e)}")


@router.get("/keyword/{query}")
async def keyword_search(query: str, limit: int = 10):
    """キーワード検索"""
    try:
        search_service = SearchService()
        results = search_service.keyword_search(query=query, limit=limit)
        
        search_results = []
        for result in results:
            search_results.append({
                "article": {
                    "number": result.article.number,
                    "name": result.article.name,
                    "full_name": result.article.full_name,
                    "category": result.article.category,
                    "tags": result.article.tags,
                    "url": result.article.url
                },
                "score": result.score,
                "matched_text": result.matched_text
            })
        
        return {
            "results": search_results,
            "total": len(search_results),
            "query": query
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"キーワード検索エラー: {str(e)}")
