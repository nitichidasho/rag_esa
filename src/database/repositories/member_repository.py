"""
メンバーリポジトリ
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from ..connection import Base, get_db
from ...models.esa_models import EsaMember


class MemberORM(Base):
    """メンバーORM"""
    __tablename__ = "members"
    
    id = Column(Integer, primary_key=True, index=True)
    screen_name = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    icon = Column(String)
    role = Column(String)
    posts_count = Column(Integer, default=0)
    joined_at = Column(DateTime)


class MemberRepository:
    """メンバーリポジトリ"""
    
    def __init__(self, db: Session = None):
        self.db = db
    
    def get_session(self) -> Session:
        """セッションを取得"""
        if self.db:
            return self.db
        return next(get_db())
    
    def create(self, member: EsaMember) -> MemberORM:
        """メンバーを作成"""
        db = self.get_session()
        db_member = MemberORM(
            id=member.id,
            screen_name=member.screen_name,
            name=member.name,
            icon=member.icon,
            role=member.role,
            posts_count=member.posts_count,
            joined_at=member.joined_at
        )
        db.add(db_member)
        db.commit()
        db.refresh(db_member)
        return db_member
    
    def get_by_id(self, member_id: int) -> Optional[MemberORM]:
        """IDでメンバーを取得"""
        db = self.get_session()
        return db.query(MemberORM).filter(MemberORM.id == member_id).first()
    
    def get_by_screen_name(self, screen_name: str) -> Optional[MemberORM]:
        """スクリーンネームでメンバーを取得"""
        db = self.get_session()
        return db.query(MemberORM).filter(MemberORM.screen_name == screen_name).first()
    
    def get_all(self) -> List[MemberORM]:
        """全メンバーを取得"""
        db = self.get_session()
        return db.query(MemberORM).all()
    
    def update(self, member_id: int, member_data: Dict[str, Any]) -> Optional[MemberORM]:
        """メンバーを更新"""
        db = self.get_session()
        db_member = db.query(MemberORM).filter(MemberORM.id == member_id).first()
        if db_member:
            for key, value in member_data.items():
                setattr(db_member, key, value)
            db.commit()
            db.refresh(db_member)
        return db_member
    
    def upsert_member(self, member_data: Dict[str, Any]) -> MemberORM:
        """メンバーを作成または更新（screen_nameベース）"""
        db = self.get_session()
        
        # screen_nameで既存メンバーを検索
        screen_name = member_data.get("screen_name")
        if not screen_name:
            raise ValueError("screen_name is required for upsert operation")
        
        existing = db.query(MemberORM).filter(
            MemberORM.screen_name == screen_name
        ).first()
        
        if existing:
            # 更新
            for key, value in member_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            db.commit()
            db.refresh(existing)
            return existing
        else:
            # 新規作成
            try:
                db_member = MemberORM(**member_data)
                db.add(db_member)
                db.commit()
                db.refresh(db_member)
                return db_member
            except Exception as e:
                db.rollback()
                # 再度既存チェック（同時実行時の競合対応）
                existing = db.query(MemberORM).filter(
                    MemberORM.screen_name == screen_name
                ).first()
                if existing:
                    # 更新
                    for key, value in member_data.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                    db.commit()
                    db.refresh(existing)
                    return existing
                else:
                    # 再試行でも失敗の場合は例外を再発生
                    raise e
    
    def delete(self, member_id: int) -> bool:
        """メンバーを削除"""
        db = self.get_session()
        db_member = db.query(MemberORM).filter(MemberORM.id == member_id).first()
        if db_member:
            db.delete(db_member)
            db.commit()
            return True
        return False
