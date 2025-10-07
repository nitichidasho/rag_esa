"""
質問応答API - 修正版
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger
from datetime import datetime

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

from ...config.settings import settings

router = APIRouter()


class QARequest(BaseModel):
    """質問応答リクエスト"""
    question: str
    context_limit: int = 5


@router.post("/")
async def answer_question(request: QARequest):
    """質問に対する回答を生成"""
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


@router.get("/status")
async def qa_status():
    """QAサービスの状態を取得"""
    status = {
        "langchain_available": LANGCHAIN_AVAILABLE,
        "original_qa_available": ORIGINAL_QA_AVAILABLE,
        "current_service": settings.qa_service_type,
        "auto_fallback": settings.auto_fallback
    }
    
    # GPU情報を追加
    try:
        import torch
        status["gpu_available"] = torch.cuda.is_available()
        if torch.cuda.is_available():
            status["gpu_count"] = torch.cuda.device_count()
            status["gpu_name"] = torch.cuda.get_device_name(0)
    except ImportError:
        status["gpu_available"] = False
    
    return status


@router.get("/models")
async def available_models():
    """利用可能なモデル情報を取得"""
    models = []
    
    if LANGCHAIN_AVAILABLE:
        try:
            service = LangChainQAService()
            if hasattr(service, 'get_model_info'):
                model_info = service.get_model_info()
                models.append({
                    "service": "langchain",
                    "status": "available",
                    **model_info
                })
        except Exception as e:
            models.append({
                "service": "langchain", 
                "status": "error",
                "error": str(e)
            })
    
    if ORIGINAL_QA_AVAILABLE:
        models.append({
            "service": "original",
            "status": "available",
            "model_name": settings.hf_llm_model,
            "type": "T5-based"
        })
    
    return {"models": models}
