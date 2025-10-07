"""
esa.io データモデル（最適化版）
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class EsaMember:
    """esa.io メンバー情報"""
    id: int                   # メンバーID（主キー）
    screen_name: str          # スクリーンネーム
    name: str                 # 表示名
    icon: str                 # アイコンURL
    role: str                 # ロール（owner, member等）
    posts_count: int          # 投稿数
    joined_at: datetime       # 参加日時


@dataclass
class Article:
    """記事データ"""
    # esa.io基本データ
    number: int               # 記事番号（主キー）
    name: str                 # 記事名
    full_name: str           # フルネーム（カテゴリ含む）
    wip: bool                # 作業中フラグ
    body_md: str             # マークダウン本文
    body_html: str           # HTML本文
    created_at: datetime     # 作成日時
    updated_at: datetime     # 更新日時
    url: str                 # 記事URL
    tags: List[str]          # タグリスト
    category: str            # カテゴリ
    created_by_id: int       # 作成者ID（外部キー）
    updated_by_id: int       # 最終更新者ID（外部キー）
    
    # 処理後データ
    processed_text: str      # 前処理済みテキスト
    embedding: Optional[List[float]] = None  # 埋め込みベクトル
    summary: Optional[str] = None            # 要約


@dataclass
class ArticleComment:
    """記事コメント"""
    id: int                   # コメントID
    article_number: int       # 記事番号（外部キー）
    body_md: str             # マークダウン本文
    created_at: datetime     # 作成日時
    user_id: int             # 作成者ID（外部キー）


@dataclass
class ArticleStar:
    """記事スター"""
    id: int                   # スターID
    article_number: int       # 記事番号（外部キー）
    user_id: int             # ユーザーID（外部キー）
    created_at: datetime     # 作成日時
