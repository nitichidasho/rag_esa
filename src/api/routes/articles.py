"""
記事API
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...database.connection import get_db
from ...database.repositories.article_repository import ArticleRepository

router = APIRouter()


@router.get("/{article_number}")
async def get_article(article_number: int, db: Session = Depends(get_db)):
    """特定記事の取得"""
    repo = ArticleRepository(db)
    article = repo.get_by_number(article_number)
    
    if not article:
        raise HTTPException(status_code=404, detail="記事が見つかりません")
    
    return {
        "number": article.number,
        "name": article.name,
        "full_name": article.full_name,
        "wip": article.wip,
        "body_md": article.body_md,
        "created_at": article.created_at,
        "updated_at": article.updated_at,
        "url": article.url,
        "tags": article.tags,
        "category": article.category,
        "summary": article.summary
    }


@router.get("/")
async def get_articles(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """記事一覧の取得"""
    repo = ArticleRepository(db)
    
    if category:
        articles = repo.search_by_category(category)
    else:
        articles = repo.get_all(skip=skip, limit=limit)
    
    return {
        "articles": [
            {
                "number": article.number,
                "name": article.name,
                "full_name": article.full_name,
                "wip": article.wip,
                "created_at": article.created_at,
                "updated_at": article.updated_at,
                "url": article.url,
                "tags": article.tags,
                "category": article.category
            }
            for article in articles
        ],
        "total": len(articles)
    }


@router.get("/recent/")
async def get_recent_articles(limit: int = 10, db: Session = Depends(get_db)):
    """最近の記事を取得"""
    repo = ArticleRepository(db)
    articles = repo.get_recent_articles(limit=limit)
    
    return {
        "articles": [
            {
                "number": article.number,
                "name": article.name,
                "full_name": article.full_name,
                "wip": article.wip,
                "created_at": article.created_at,
                "updated_at": article.updated_at,
                "url": article.url,
                "tags": article.tags,
                "category": article.category
            }
            for article in articles
        ]
    }
