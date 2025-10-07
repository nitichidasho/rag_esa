"""
FastAPI メインアプリケーション
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
import secrets

from ..config.settings import settings
from ..database.connection import init_db
from .routes import articles, search, export, progress

# ハイブリッド検索の条件付きインポート
try:
    from .routes import hybrid_search
    HYBRID_SEARCH_AVAILABLE = True
    print("✅ Hybrid search service loaded")
except ImportError as e:
    print(f"⚠️ Hybrid search not available: {e}")
    HYBRID_SEARCH_AVAILABLE = False

# QAルートの条件付きインポート
try:
    from .routes import qa
    QA_AVAILABLE = True
    qa_router = qa.router
    print("✅ Full QA service loaded")
except ImportError as e:
    print(f"⚠️ Full QA service not available: {e}")
    print("🔄 Loading fallback QA service...")
    try:
        from .routes import qa_fallback
        QA_AVAILABLE = False
        qa_router = qa_fallback.router
        print("✅ Fallback QA service loaded")
    except ImportError as fallback_error:
        print(f"❌ Even fallback QA failed: {fallback_error}")
        QA_AVAILABLE = None
        qa_router = None

# FastAPIアプリケーションの作成
app = FastAPI(
    title="研究室 esa.io RAGシステム API",
    description="esa.io記事の検索・質問応答システム",
    version="1.0.0"
)

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],  # Streamlitのデフォルトポート
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# セキュリティ設定
security = HTTPBasic()


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """基本認証の検証"""
    is_correct_username = secrets.compare_digest(
        credentials.username, settings.basic_auth_username
    )
    is_correct_password = secrets.compare_digest(
        credentials.password, settings.basic_auth_password
    )
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証に失敗しました",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


# データベース初期化
@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の処理"""
    init_db()


# ルーターの登録
app.include_router(
    articles.router,
    prefix="/api/articles",
    tags=["articles"],
    dependencies=[Depends(verify_credentials)]
)

app.include_router(
    search.router,
    prefix="/api/search",
    tags=["search"],
    dependencies=[Depends(verify_credentials)]
)

app.include_router(
    export.router,
    prefix="/api/export",
    tags=["export"],
    dependencies=[Depends(verify_credentials)]
)

# 進捗追跡ルートの登録
app.include_router(
    progress.router,
    prefix="/api/progress",
    tags=["progress"],
    dependencies=[Depends(verify_credentials)]
)

# ハイブリッド検索ルートの登録
if HYBRID_SEARCH_AVAILABLE:
    app.include_router(
        hybrid_search.router,
        prefix="/api/search",
        tags=["hybrid-search"],
        dependencies=[Depends(verify_credentials)]
    )
    print("✅ Hybrid search endpoints registered")

# QAルートの登録
if qa_router is not None:
    app.include_router(
        qa_router,
        prefix="/api/qa",
        tags=["qa"],
        dependencies=[Depends(verify_credentials)]
    )
    if QA_AVAILABLE:
        print("✅ Full QA endpoints registered")
    else:
        print("⚠️ Fallback QA endpoints registered")
else:
    print("❌ No QA endpoints available")


@app.get("/")
async def root():
    """ルートエンドポイント"""
    # 利用可能なエンドポイントを動的に生成
    available_endpoints = [
        "/docs - API Documentation",
        "/api/articles - Article management",
        "/api/search - Article search (basic + hybrid)",
        "/api/export - Data export",
        "/api/progress - Progress tracking"
    ]
    
    if HYBRID_SEARCH_AVAILABLE:
        available_endpoints.extend([
            "/api/search/hybrid - Advanced hybrid search",
            "/api/search/hybrid/explain - Search explanation",
            "/api/search/hybrid/compare - Method comparison"
        ])
    
    if qa_router is not None:
        if QA_AVAILABLE:
            available_endpoints.append("/api/qa - Question Answering (Full)")
        else:
            available_endpoints.append("/api/qa - Question Answering (Fallback)")
    
    return {
        "message": "研究室 esa.io RAGシステム API",
        "version": "1.0.0",
        "docs": "/docs",
        "qa_status": "available" if QA_AVAILABLE else "fallback" if qa_router else "unavailable",
        "hybrid_search_status": "available" if HYBRID_SEARCH_AVAILABLE else "unavailable",
        "available_endpoints": available_endpoints
    }


@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "healthy"}
