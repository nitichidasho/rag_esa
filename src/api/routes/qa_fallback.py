"""
フォールバック QA API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class QARequest(BaseModel):
    """質問応答リクエスト"""
    question: str
    context_limit: int = 5


@router.post("/")
async def answer_question_fallback(request: QARequest):
    """フォールバック質問応答エンドポイント"""
    return {
        "question": request.question,
        "answer": "申し訳ございません。現在QAサービスは利用できません。依存関係のインストールが必要です。",
        "confidence": 0.0,
        "generated_at": datetime.now().isoformat(),
        "service_used": "fallback",
        "sources": [],
        "error": "QA service dependencies not available"
    }


@router.get("/health")
async def qa_health_check_fallback():
    """QAサービスのヘルスチェック（フォールバック）"""
    return {
        "status": "fallback",
        "message": "QA service dependencies not available",
        "available_endpoints": ["/api/search", "/api/articles", "/api/export"]
    }
