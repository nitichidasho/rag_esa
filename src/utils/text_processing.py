"""
テキスト処理ユーティリティ
"""

import re
from typing import List
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning, XMLParsedAsHTMLWarning
import markdown
import warnings

# BeautifulSoupの警告を無効化
warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


class TextProcessor:
    """テキスト処理クラス"""
    
    @staticmethod
    def clean_markdown(text: str) -> str:
        """マークダウンテキストのクリーニング"""
        if not text:
            return ""
        
        # HTMLタグを除去
        text = BeautifulSoup(text, "html.parser").get_text()
        
        # マークダウン記法を除去
        text = re.sub(r'#{1,6}\s+', '', text)  # ヘッダー
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # 太字
        text = re.sub(r'\*(.*?)\*', r'\1', text)  # 斜体
        text = re.sub(r'`(.*?)`', r'\1', text)  # インラインコード
        text = re.sub(r'```[\s\S]*?```', '', text)  # コードブロック
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # リンク
        text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'\1', text)  # 画像
        
        # 改行を統一
        text = re.sub(r'\r\n|\r|\n', ' ', text)
        
        # 複数の空白を単一の空白に
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    @staticmethod
    def extract_keywords(text: str, min_length: int = 2) -> List[str]:
        """キーワード抽出"""
        if not text:
            return []
        
        # 日本語・英数字のみを抽出
        words = re.findall(r'[ぁ-んァ-ヶ一-龯a-zA-Z0-9]+', text)
        
        # 最小文字数でフィルタリング
        keywords = [word for word in words if len(word) >= min_length]
        
        # 重複除去
        return list(set(keywords))
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 500) -> str:
        """テキストの切り詰め"""
        if not text or len(text) <= max_length:
            return text
        
        # 文の境界で切り詰め
        sentences = re.split(r'[。！？\.\!\?]', text)
        result = ""
        
        for sentence in sentences:
            if len(result + sentence) <= max_length:
                result += sentence
                if sentence != sentences[-1]:
                    result += "。"
            else:
                break
        
        if not result:
            result = text[:max_length]
        
        return result.strip()
    
    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """空白文字の正規化"""
        if not text:
            return ""
        
        # 全角スペースを半角スペースに
        text = text.replace('　', ' ')
        
        # 複数の空白を単一の空白に
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    @staticmethod
    def remove_urls(text: str) -> str:
        """URL除去"""
        if not text:
            return ""
        
        # HTTP/HTTPSのURL除去
        text = re.sub(r'https?://[^\s]+', '', text)
        
        # www.で始まるURL除去
        text = re.sub(r'www\.[^\s]+', '', text)
        
        return text.strip()
    
    @staticmethod
    def create_summary(text: str, max_sentences: int = 3) -> str:
        """簡単な要約作成"""
        if not text:
            return ""
        
        # 文に分割
        sentences = re.split(r'[。！？\.\!\?]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # 最初の数文を要約として使用
        summary_sentences = sentences[:max_sentences]
        summary = "。".join(summary_sentences)
        
        if summary and not summary.endswith('。'):
            summary += "。"
        
        return summary
