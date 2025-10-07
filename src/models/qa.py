"""
質問応答データ構造
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List
from .esa_models import Article


@dataclass
class QAResult:
    """質問応答結果"""
    question: str             # 質問
    answer: str               # 回答
    source_articles: List[Article]  # 根拠記事
    confidence: float         # 信頼度
    generated_at: datetime    # 生成日時
