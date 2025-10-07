"""
検索結果データ構造
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from .esa_models import Article


@dataclass
class SearchResult:
    """検索結果"""
    article: Article
    score: float              # 類似度スコア
    matched_text: str         # マッチしたテキスト部分
    highlights: List[str]     # ハイライト箇所


@dataclass
class SearchParams:
    """検索パラメータ"""
    query: str
    limit: int = 10
    filters: Optional[Dict[str, Any]] = None
    search_type: str = "semantic"  # "semantic", "hybrid"
    sparse_weight: Optional[float] = None
    dense_weight: Optional[float] = None
