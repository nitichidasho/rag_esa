"""
クエリ前処理モジュール
RAGシステムにおける自然言語質問からの効果的なキーワード抽出
"""

import re
import unicodedata
from typing import List, Set, Dict, Optional
from loguru import logger


class QueryProcessor:
    """質問文の前処理とキーワード抽出"""
    
    def __init__(self):
        # 日本語ストップワード（一般的な助詞・助動詞など）
        self.stop_words = {
            'の', 'に', 'は', 'を', 'が', 'で', 'と', 'も', 'から', 'まで', 'より', 'へ',
            'について', 'において', 'という', 'として', 'による', 'により',
            'これ', 'それ', 'あれ', 'この', 'その', 'あの', 'どの', 'どれ', 'なに', '何',
            'です', 'である', 'だ', 'ます', 'ました', 'です', 'でした', 'する', 'した',
            'ある', 'ない', 'いる', 'ていう', 'という', 'といった', 'みたいな',
            'お', 'ご', 'さん', 'ちゃん', 'くん', 'さま', '様'
        }
        
        # 疑問詞・質問表現（抽出対象外）
        self.question_words = {
            'どうやって', 'どのように', 'どんな', 'なぜ', 'いつ', 'どこ', 'だれ', '誰',
            'なんで', '何で', 'どうして', 'いかに', 'どう', 'どれ', 'どちら',
            '教えて', '知りたい', '分からない', 'わからない', '方法', '手順', 'やり方'
        }
        
        # 技術用語・専門用語の同義語マッピング
        self.synonyms = {
            'ubuntu': ['ubuntu', 'ウブントゥ', 'ウブンツ'],
            'install': ['インストール', 'install', 'installation', 'setup', 'セットアップ'],
            'python': ['python', 'パイソン', 'py'],
            'ros': ['ros', 'robot operating system', 'ロボットオペレーティングシステム'],
            'rag': ['rag', 'retrieval augmented generation', 'retrieval-augmented generation', 'ラグ', '検索拡張生成', 'レトリーバル'],
            'ai': ['ai', '人工知能', 'artificial intelligence', 'machine learning', '機械学習'],
            'docker': ['docker', 'コンテナ', 'container'],
            'raspberry pi': ['raspberry pi', 'ラズパイ', 'raspberry', 'ラズベリーパイ'],
            'gpu': ['gpu', 'graphics processing unit', 'グラフィックス', 'cuda'],
            'neural network': ['neural network', 'ニューラルネットワーク', '神経回路網', 'nn'],
            'deep learning': ['deep learning', 'ディープラーニング', '深層学習'],
            'esa': ['esa', 'エサ', 'チームエサ', 'team esa', 'エササービス'],
            'api': ['api', 'application programming interface', 'アプリケーションプログラミングインターフェース', 'アプリケーションプログラムインターフェース'],
        }
    
    def process_query(self, query: str) -> Dict[str, any]:
        """
        クエリを前処理して検索に最適化
        
        Args:
            query: 原文の質問
            
        Returns:
            処理結果辞書（キーワード、展開クエリなど）
        """
        # 基本前処理
        normalized_query = self._normalize_text(query)
        
        # キーワード抽出
        keywords = self._extract_keywords(normalized_query)
        
        # 技術用語の正規化
        technical_terms = self._extract_technical_terms(keywords)
        
        # 同義語展開
        expanded_keywords = self._expand_synonyms(technical_terms)
        
        # 検索用クエリ生成
        search_queries = self._generate_search_queries(keywords, expanded_keywords)
        
        # 最適なクエリを選択
        recommended_query = self._select_best_query(search_queries, normalized_query)
        
        result = {
            'original_query': query,
            'normalized_query': normalized_query,
            'keywords': keywords,
            'technical_terms': technical_terms,
            'expanded_keywords': expanded_keywords,
            'search_queries': search_queries,
            'recommended_query': recommended_query
        }
        
        logger.debug(f"Query processing result: {result}")
        return result
    
    def _normalize_text(self, text: str) -> str:
        """テキストの正規化"""
        if not text:
            return ""
        
        # Unicode正規化
        text = unicodedata.normalize('NFKC', text)
        
        # 改行・タブを空白に
        text = re.sub(r'[\r\n\t]+', ' ', text)
        
        # 連続する空白を単一に
        text = re.sub(r'\s+', ' ', text)
        
        # 前後の空白除去
        text = text.strip()
        
        return text
    
    def _extract_keywords(self, text: str) -> List[str]:
        """重要キーワードの抽出（改善版）"""
        keywords = []
        
        # 1. 英語単語の抽出（アルファベットのみ）
        english_words = re.findall(r'[a-zA-Z][a-zA-Z0-9\-_.]*[a-zA-Z0-9]|[a-zA-Z]', text)
        for word in english_words:
            if len(word) >= 2 and word.lower() not in self.stop_words:
                keywords.append(word)
        
        # 2. 日本語キーワードの抽出（より柔軟なパターン）
        # カタカナ語の抽出
        katakana_words = re.findall(r'[ァ-ヶー]+', text)
        for word in katakana_words:
            if len(word) >= 2 and word not in self.stop_words:
                keywords.append(word)
        
        # 3. 複合語の抽出（技術用語が含まれる可能性）
        # ひらがな+カタカナ+漢字の組み合わせ
        japanese_compounds = re.findall(r'[ぁ-んァ-ヶ一-龯]{3,}', text)
        for compound in japanese_compounds:
            # 知られた技術用語パターンをチェック
            if self._contains_technical_pattern(compound):
                keywords.append(compound)
        
        # 4. 特定の技術用語の直接抽出
        technical_patterns = [
            r'[Uu]buntu', r'インストール', r'セットアップ', r'設定',
            r'[Pp]ython', r'[Dd]ocker', r'[Rr][Oo][Ss]', r'ラズパイ',
            r'機械学習', r'[Aa][Ii]', r'ディープラーニング', r'深層学習',
            r'ニューラルネットワーク', r'[Gg][Pp][Uu]', r'環境構築'
        ]
        
        for pattern in technical_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if match not in keywords:
                    keywords.append(match)
        
        # 5. 重複除去とフィルタリング
        seen = set()
        unique_keywords = []
        for word in keywords:
            word_lower = word.lower()
            if (word_lower not in seen and 
                word_lower not in self.stop_words and 
                word_lower not in self.question_words and
                len(word) >= 2):
                seen.add(word_lower)
                unique_keywords.append(word)
        
        return unique_keywords
    
    def _contains_technical_pattern(self, text: str) -> bool:
        """技術的なパターンを含むかチェック"""
        technical_indicators = [
            'インストール', 'セットアップ', '設定', '構築', '開発',
            '実装', '学習', '訓練', 'モデル', 'システム', 'ツール',
            'ライブラリ', 'フレームワーク', 'プラットフォーム'
        ]
        
        for indicator in technical_indicators:
            if indicator in text:
                return True
        return False
    
    def _extract_technical_terms(self, keywords: List[str]) -> List[str]:
        """技術用語の抽出と正規化（改善版）"""
        technical_terms = []
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # 1. 直接マッチング：技術用語辞書との照合（完全一致優先）
            found_match = False
            for base_term, variants in self.synonyms.items():
                # 完全一致チェック
                if keyword_lower in [v.lower() for v in variants]:
                    technical_terms.append(base_term)
                    found_match = True
                    break
            
            # 2. 部分マッチング（より厳密に）
            if not found_match:
                for base_term, variants in self.synonyms.items():
                    for variant in variants:
                        variant_lower = variant.lower()
                        # 3文字以上で、完全にキーワード内に含まれる場合のみ
                        if (len(variant) >= 3 and 
                            len(keyword) >= 3 and
                            (variant_lower == keyword_lower or 
                             (len(variant) >= 4 and variant_lower in keyword_lower and len(keyword_lower) - len(variant_lower) <= 2) or
                             (len(keyword) >= 4 and keyword_lower in variant_lower and len(variant_lower) - len(keyword_lower) <= 2))):
                            technical_terms.append(base_term)
                            found_match = True
                            break
                    if found_match:
                        break
            
            # 3. パターンマッチング：技術的パターンの検出
            if not found_match and self._is_technical_pattern(keyword):
                technical_terms.append(keyword)
        
        return list(set(technical_terms))  # 重複除去
    
    def _is_technical_pattern(self, word: str) -> bool:
        """技術用語パターンの判定（改善版）"""
        word_lower = word.lower()
        
        # 1. 明確な技術用語パターン
        tech_patterns = [
            r'^[a-z]+\d+$',  # python3, ros2など
            r'^[a-z]+[-_][a-z]+$',  # deep-learning, machine_learningなど
            r'\.js$|\.py$|\.cpp$|\.java$',  # ファイル拡張子
            r'^[a-z]{4,}$',  # 4文字以上の英単語
        ]
        
        for pattern in tech_patterns:
            if re.match(pattern, word_lower):
                return True
        
        # 2. 日本語の技術用語パターン
        japanese_tech_patterns = [
            'インストール', 'セットアップ', '環境構築', '設定',
            'システム', 'プラットフォーム', 'フレームワーク',
            'ライブラリ', 'ツール', 'アプリ', 'ソフトウェア',
            '機械学習', '深層学習', 'ニューラルネットワーク',
            'データベース', 'サーバー', 'クライアント'
        ]
        
        for pattern in japanese_tech_patterns:
            if pattern in word:
                return True
        
        return False
    
    def _expand_synonyms(self, technical_terms: List[str]) -> List[str]:
        """同義語展開"""
        expanded = []
        
        for term in technical_terms:
            term_lower = term.lower()
            
            # 同義語マッピングから展開
            if term_lower in self.synonyms:
                expanded.extend(self.synonyms[term_lower])
            else:
                expanded.append(term)
        
        # 重複除去
        return list(set(expanded))
    
    def _generate_search_queries(self, keywords: List[str], expanded_keywords: List[str]) -> List[str]:
        """検索用クエリの生成（改善版）"""
        queries = []
        
        # 1. 展開キーワード優先のクエリ（最も重要）
        if expanded_keywords:
            # RAGやesaなど重要キーワードを優先
            priority_keywords = []
            other_keywords = []
            
            for keyword in expanded_keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in ['rag', 'retrieval augmented generation', 'retrieval-augmented generation', '検索拡張生成']:
                    priority_keywords.append(keyword)
                elif keyword_lower in ['esa', 'エサ', 'チームエサ', 'team esa']:
                    priority_keywords.append(keyword)
                else:
                    other_keywords.append(keyword)
            
            # 優先キーワードを含むクエリを作成
            if priority_keywords:
                # RAGとesaの両方がある場合は両方使用
                if any('rag' in k.lower() or '検索拡張生成' in k for k in priority_keywords) and \
                   any('esa' in k.lower() or 'エサ' in k for k in priority_keywords):
                    rag_terms = [k for k in priority_keywords if 'rag' in k.lower() or '検索拡張生成' in k][:2]
                    esa_terms = [k for k in priority_keywords if 'esa' in k.lower() or 'エサ' in k][:1]
                    simple_query = ' '.join(rag_terms + esa_terms)
                else:
                    # 優先キーワードのみ使用
                    simple_query = ' '.join(priority_keywords[:3])
                queries.append(simple_query)
            else:
                # 優先キーワードがない場合は従来通り
                simple_query = ' '.join(expanded_keywords[:3])
                queries.append(simple_query)
        
        # 2. 技術用語から技術用語を抽出
        tech_keywords = []
        action_keywords = []
        
        for kw in keywords:
            kw_lower = kw.lower()
            # 特定の技術用語の優先マッチング（RAG, ROS等の混同を防ぐ）
            if kw_lower == 'rag':
                tech_keywords.append('rag')
            elif kw_lower == 'ros':
                tech_keywords.append('ros')
            elif kw_lower in ['esa', 'エサ']:
                tech_keywords.append('esa')
            # 一般的な技術用語の判定
            elif (any(tech in kw_lower for tech in ['ubuntu', 'python', 'docker']) or
                  kw_lower in self.synonyms):
                tech_keywords.append(kw)
            # アクション語の判定
            elif any(action in kw for action in ['インストール', 'セットアップ', '設定', '構築', '方法']):
                action_keywords.append(kw)
        
        # 3. 技術用語 + アクション語の組み合わせ
        if tech_keywords and action_keywords:
            combined_query = ' '.join(tech_keywords[:2] + action_keywords[:1])
            queries.append(combined_query)
        elif tech_keywords:
            # 技術用語のみのクエリ
            tech_query = ' '.join(tech_keywords[:3])
            queries.append(tech_query)
        
        # 4. 重複除去と検証
        unique_queries = []
        for query in queries:
            query = query.strip()
            if query and query not in unique_queries and len(query.split()) >= 1:
                unique_queries.append(query)
        
        return unique_queries[:3]  # 最大3つまで
    
    def _select_best_query(self, search_queries: List[str], normalized_query: str) -> str:
        """最適なクエリを選択"""
        if not search_queries:
            return normalized_query
        
        # 最初のクエリ（展開キーワード優先）を使用
        best_query = search_queries[0]
        
        # 元の正規化クエリと比較して長さが適切かチェック
        if len(best_query) < 3:
            return normalized_query
        
        return best_query
    
    def suggest_better_query(self, original_query: str) -> str:
        """より良い検索クエリの提案"""
        result = self.process_query(original_query)
        
        # 最適化されたクエリを提案
        if result['recommended_query'] != result['normalized_query']:
            return result['recommended_query']
        
        return original_query
    
    def extract_core_concepts(self, query: str) -> List[str]:
        """コアコンセプトの抽出（デバッグ用）"""
        result = self.process_query(query)
        
        core_concepts = []
        core_concepts.extend(result['technical_terms'])
        
        # 技術用語以外の重要キーワード
        other_important = [k for k in result['keywords'] 
                          if k.lower() not in [t.lower() for t in result['technical_terms']] 
                          and len(k) >= 3]
        core_concepts.extend(other_important[:2])
        
        return core_concepts
