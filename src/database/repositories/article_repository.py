"""
記事リポジトリ
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON
from datetime import datetime

from ..connection import Base, get_db
from ...models.esa_models import Article


class ArticleORM(Base):
    """記事ORM"""
    __tablename__ = "articles"
    
    number = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    wip = Column(Boolean, default=False)
    body_md = Column(Text)
    body_html = Column(Text)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    url = Column(String)
    tags = Column(JSON)  # JSONフィールドとしてタグを保存
    category = Column(String)
    created_by_id = Column(Integer)
    updated_by_id = Column(Integer)
    processed_text = Column(Text)
    embedding = Column(JSON)  # JSONフィールドとして埋め込みベクトルを保存
    summary = Column(Text)


class ArticleRepository:
    """記事リポジトリ"""
    
    def __init__(self, db: Session = None):
        self.db = db
    
    def get_session(self) -> Session:
        """セッションを取得"""
        if self.db:
            return self.db
        return next(get_db())
    
    def create(self, article: Article) -> ArticleORM:
        """記事を作成"""
        db = self.get_session()
        db_article = ArticleORM(
            number=article.number,
            name=article.name,
            full_name=article.full_name,
            wip=article.wip,
            body_md=article.body_md,
            body_html=article.body_html,
            created_at=article.created_at,
            updated_at=article.updated_at,
            url=article.url,
            tags=article.tags,
            category=article.category,
            created_by_id=article.created_by_id,
            updated_by_id=article.updated_by_id,
            processed_text=article.processed_text,
            embedding=article.embedding,
            summary=article.summary
        )
        db.add(db_article)
        db.commit()
        db.refresh(db_article)
        return db_article
    
    def get_by_number(self, number: int) -> Optional[ArticleORM]:
        """記事番号で記事を取得"""
        db = self.get_session()
        return db.query(ArticleORM).filter(ArticleORM.number == number).first()
    
    def get_all(self, skip: int = 0, limit: Optional[int] = None) -> List[ArticleORM]:
        """全記事を取得"""
        db = self.get_session()
        query = db.query(ArticleORM).offset(skip)
        if limit is not None:
            query = query.limit(limit)
        return query.all()
    
    def update(self, number: int, article_data: Dict[str, Any]) -> Optional[ArticleORM]:
        """記事を更新"""
        db = self.get_session()
        db_article = db.query(ArticleORM).filter(ArticleORM.number == number).first()
        if db_article:
            for key, value in article_data.items():
                setattr(db_article, key, value)
            db.commit()
            db.refresh(db_article)
        return db_article
    
    def upsert_article(self, article_data: Dict[str, Any]) -> ArticleORM:
        """記事を作成または更新"""
        db = self.get_session()
        existing = db.query(ArticleORM).filter(
            ArticleORM.number == article_data.get("number")
        ).first()
        
        if existing:
            # 更新
            for key, value in article_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            db.commit()
            db.refresh(existing)
            return existing
        else:
            # 新規作成
            db_article = ArticleORM(**article_data)
            db.add(db_article)
            db.commit()
            db.refresh(db_article)
            return db_article
    
    def delete(self, number: int) -> bool:
        """記事を削除"""
        db = self.get_session()
        db_article = db.query(ArticleORM).filter(ArticleORM.number == number).first()
        if db_article:
            db.delete(db_article)
            db.commit()
            return True
        return False
    
    def search_by_category(self, category: str) -> List[ArticleORM]:
        """カテゴリで検索"""
        db = self.get_session()
        return db.query(ArticleORM).filter(ArticleORM.category.like(f"%{category}%")).all()
    
    def search_by_tags(self, tags: List[str]) -> List[ArticleORM]:
        """タグで検索"""
        db = self.get_session()
        # JSONフィールドでの検索（SQLiteの場合）
        articles = []
        for article in db.query(ArticleORM).all():
            if article.tags and any(tag in article.tags for tag in tags):
                articles.append(article)
        return articles
    
    def get_recent_articles(self, limit: int = 10) -> List[ArticleORM]:
        """最近の記事を取得"""
        db = self.get_session()
        return db.query(ArticleORM).order_by(ArticleORM.updated_at.desc()).limit(limit).all()
    
    def get_paginated(self, limit: int = 10, offset: int = 0) -> List[ArticleORM]:
        """ページ分割で記事を取得"""
        db = self.get_session()
        return db.query(ArticleORM).offset(offset).limit(limit).all()
    
    def search_by_category(self, category: str, limit: int = 10) -> List[ArticleORM]:
        """カテゴリで検索（改良版）"""
        db = self.get_session()
        return db.query(ArticleORM).filter(
            ArticleORM.category.like(f"%{category}%")
        ).limit(limit).all()
    
    def search_by_tags(self, tags: List[str], limit: int = 10) -> List[ArticleORM]:
        """タグで検索（改良版）"""
        db = self.get_session()
        articles = []
        for article in db.query(ArticleORM).all():
            if article.tags and any(tag in article.tags for tag in tags):
                articles.append(article)
                if len(articles) >= limit:
                    break
        return articles
    
    def count_articles(self) -> int:
        """記事数をカウント"""
        db = self.get_session()
        return db.query(ArticleORM).count()
