"""
質問応答API - ハイブリッド検索対応版
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger
from datetime import datetime

# 進捗追跡のインポート
from .progress import create_progress_tracker, get_progress_tracker

# QAサービスの条件付きインポート
try:
    from ...services.langchain_qa_service import LangChainQAService
    LANGCHAIN_AVAILABLE = True
    logger.info("✅ LangChain QA service available")
except ImportError as e:
    LANGCHAIN_AVAILABLE = False
    LangChainQAService = None
    logger.warning(f"⚠️ LangChain QA service not available: {e}")

try:
    from ...services.qa_service import QAService
    ORIGINAL_QA_AVAILABLE = True
    logger.info("✅ Original QA service available")
except ImportError as e:
    ORIGINAL_QA_AVAILABLE = False
    QAService = None
    logger.warning(f"⚠️ Original QA service not available: {e}")

# ハイブリッド検索サービス
try:
    from ...services.hybrid_search_service import HybridSearchService
    HYBRID_SEARCH_AVAILABLE = True
    logger.info("✅ Hybrid search service available")
except ImportError as e:
    HYBRID_SEARCH_AVAILABLE = False
    HybridSearchService = None
    logger.warning(f"⚠️ Hybrid search service not available: {e}")

from ...config.settings import settings

router = APIRouter()


class QARequest(BaseModel):
    """質問応答リクエスト"""
    question: str
    context_limit: int = 5
    use_hybrid_search: bool = True  # ハイブリッド検索を使用するかどうか
    track_progress: bool = False  # 進捗追跡を有効にするかどうか


class QAWithProgressRequest(BaseModel):
    """進捗追跡付き質問応答リクエスト"""
    question: str
    context_limit: int = 5
    use_hybrid_search: bool = True


@router.post("/with-progress")
async def answer_question_with_progress(request: QAWithProgressRequest):
    """進捗追跡付きで質問に対する回答を生成"""
    # 進捗追跡を作成
    task_id, progress_tracker = create_progress_tracker()
    
    try:
        progress_tracker.update(5, "QAサービスを初期化中...")
        
        # 利用可能なサービスに応じて選択
        qa_service = None
        service_used = None
        
        # LangChainサービスを優先
        if LANGCHAIN_AVAILABLE and settings.qa_service_type in ["langchain", "auto"]:
            try:
                qa_service = LangChainQAService()
                service_used = "LangChain RAG Service"
                logger.info("Using LangChain QA service")
                progress_tracker.update(10, "LangChain QAサービスを使用します")
            except Exception as e:
                logger.warning(f"LangChain service failed: {e}")
                qa_service = None
        
        # フォールバック: オリジナルQAサービス
        if qa_service is None and ORIGINAL_QA_AVAILABLE:
            try:
                qa_service = QAService()
                service_used = "Original QA Service (fallback)"
                logger.info("Using original QA service as fallback")
                progress_tracker.update(10, "オリジナルQAサービスにフォールバック")
            except Exception as e:
                logger.error(f"Original QA service also failed: {e}")
                qa_service = None
        
        # どちらも利用できない場合
        if qa_service is None:
            progress_tracker.error("QAサービスが利用できません")
            return {
                "task_id": task_id,
                "question": request.question,
                "answer": "申し訳ございません。現在QAサービスは利用できません。依存関係のインストールが必要です。",
                "sources": [],
                "confidence": 0.0,
                "service_used": "fallback",
                "error": "QA service dependencies not available"
            }
        
        progress_tracker.update(15, "ハイブリッド検索を開始中...")
        
        # 質問応答実行
        if request.use_hybrid_search and HYBRID_SEARCH_AVAILABLE:
            # ハイブリッド検索を使用してコンテキストを取得
            hybrid_service = HybridSearchService()
            search_results = await hybrid_service.hybrid_search(
                query=request.question,
                limit=request.context_limit
            )
            
            progress_tracker.update(50, f"ハイブリッド検索完了 ({len(search_results.results)}件の記事)")
            
            # ハイブリッド検索結果をQAサービス用の形式に変換
            context_articles = []
            for result in search_results:
                # HybridSearchResultからArticle形式を構築
                from ...models.esa_models import Article
                from datetime import datetime
                
                article = Article(
                    number=result.article_id,
                    name=result.title,
                    full_name=result.title,
                    wip=False,
                    body_md=result.content,
                    body_html="",
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    url="",
                    tags=[],
                    category="",
                    created_by_id=0,
                    updated_by_id=0,
                    processed_text=result.content,
                    embedding=None,
                    summary=None
                )
                context_articles.append(article)
            
            # QAサービスでハイブリッド検索の結果を使用
            result = qa_service.answer_question_with_context(
                question=request.question,
                contexts=search_results,
                context_limit=request.context_limit,
                progress_tracker=progress_tracker
            )
            service_used += " + Hybrid Search"
        else:
            # 従来の検索方法を使用
            progress_tracker.update(50, "従来の検索方法を使用中...")
            result = qa_service.answer_question(
                question=request.question,
                context_limit=request.context_limit
            )
        
        # レスポンス構築
        response = {
            "task_id": task_id,
            "question": result.question,
            "answer": result.answer,
            "sources": [
                {
                    "name": article.name,
                    "url": article.url,
                    "category": article.category,
                    "tags": article.tags or []
                }
                for article in result.source_articles
            ],
            "confidence": result.confidence,
            "service_used": service_used
        }
        
        # LangChainサービスの場合、追加情報を含める
        if hasattr(result, 'model_info') and result.model_info:
            response["model_info"] = result.model_info
        
        return response
        
    except Exception as e:
        logger.error(f"QA API error: {e}")
        progress_tracker.error(str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def answer_question(request: QARequest):
    """質問に対する回答を生成（通常版）"""
    try:
        # 利用可能なサービスに応じて選択
        qa_service = None
        service_used = None
        
        # LangChainサービスを優先
        if LANGCHAIN_AVAILABLE and settings.qa_service_type in ["langchain", "auto"]:
            try:
                qa_service = LangChainQAService()
                service_used = "LangChain RAG Service"
                logger.info("Using LangChain QA service")
            except Exception as e:
                logger.warning(f"LangChain service failed: {e}")
                qa_service = None
        
        # フォールバック: オリジナルQAサービス
        if qa_service is None and ORIGINAL_QA_AVAILABLE:
            try:
                qa_service = QAService()
                service_used = "Original QA Service (fallback)"
                logger.info("Using original QA service as fallback")
            except Exception as e:
                logger.error(f"Original QA service also failed: {e}")
                qa_service = None
        
        # どちらも利用できない場合
        if qa_service is None:
            return {
                "question": request.question,
                "answer": "申し訳ございません。現在QAサービスは利用できません。依存関係のインストールが必要です。",
                "sources": [],
                "confidence": 0.0,
                "service_used": "fallback",
                "error": "QA service dependencies not available"
            }
        
        # 質問応答実行
        if request.use_hybrid_search and HYBRID_SEARCH_AVAILABLE:
            # ハイブリッド検索を使用してコンテキストを取得
            hybrid_service = HybridSearchService()
            search_results = await hybrid_service.hybrid_search(
                query=request.question,
                limit=request.context_limit
            )
            
            # QAサービスでハイブリッド検索の結果を使用
            result = qa_service.answer_question_with_context(
                question=request.question,
                contexts=search_results,
                context_limit=request.context_limit
            )
            service_used += " + Hybrid Search"
        else:
            # 従来の検索方法を使用
            result = qa_service.answer_question(
                question=request.question,
                context_limit=request.context_limit
            )
        
        # レスポンス構築
        response = {
            "question": result.question,
            "answer": result.answer,
            "sources": [
                {
                    "name": article.name,
                    "url": article.url,
                    "category": article.category,
                    "tags": article.tags or []
                }
                for article in result.source_articles
            ],
            "confidence": result.confidence,
            "service_used": service_used
        }
        
        # LangChainサービスの場合、追加情報を含める
        if hasattr(result, 'model_info') and result.model_info:
            response["model_info"] = result.model_info
        
        return response
        
    except Exception as e:
        logger.error(f"QA API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
