"""
検索サービス
"""

from typing import List, Dict, Any, Optional
import chromadb
from loguru import logger

from ..config.settings import settings
from ..models.search import SearchResult
from ..models.esa_models import Article
from .embedding_service import EmbeddingService


class SearchService:
    """検索サービス"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.chroma_client = None
        self.collection = None
        self._initialize_chroma()
    
    def _initialize_chroma(self):
        """ChromaDBの初期化"""
        try:
            self.chroma_client = chromadb.PersistentClient(path=settings.vector_db_path)
            self.collection = self.chroma_client.get_or_create_collection(
                name="articles",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("ChromaDB initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    def add_article(self, article: Article):
        """記事をベクトルデータベースに追加"""
        try:
            # 埋め込みベクトル生成
            if not article.embedding:
                article.embedding = self.embedding_service.generate_embedding(
                    f"{article.name} {article.body_md}"
                )
            
            # ChromaDBに追加
            metadata = {
                "name": article.name,
                "category": article.category or "",
                "tags": ",".join(article.tags) if article.tags else "",
                "created_at": article.created_at.isoformat() if article.created_at else "",
                "updated_at": article.updated_at.isoformat() if article.updated_at else "",
                "wip": article.wip,
                "url": article.url or ""
            }
            
            # None値を除外
            if article.created_by_id is not None:
                metadata["created_by_id"] = article.created_by_id
                
            self.collection.add(
                ids=[str(article.number)],
                embeddings=[article.embedding],
                metadatas=[metadata],
                documents=[article.processed_text or article.body_md]
            )
            
            logger.info(f"Added article {article.number} to vector database")
        except Exception as e:
            logger.error(f"Failed to add article to vector database: {e}")
    
    def semantic_search(self, query: str, limit: int = 10, filters: Optional[Dict] = None, debug_mode: bool = False) -> List[SearchResult]:
        """セマンティック検索（タイトルマッチング強化版）"""
        try:
            # 1. まずタイトルマッチング記事を探す
            title_matched_articles = self._find_title_matches(query, debug_mode)
            
            # 2. クエリの埋め込みベクトル生成
            query_embedding = self.embedding_service.generate_embedding(query)
            
            # より多くの結果を取得してから多様性フィルタリング
            extended_limit = min(limit * 4, 100)  # 4倍の結果を取得（最大100件）
            
            # ChromaDBで検索
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=extended_limit,
                include=["metadatas", "documents", "distances"]
            )
            
            search_results = []
            categories_seen = {}  # カテゴリごとの件数をカウント
            title_keywords_seen = set()
            processed_article_ids = set()
            
            # デバッグ情報
            if debug_mode:
                logger.info(f"Debug: Found {len(results['ids'][0])} raw results from ChromaDB")
                logger.info(f"Debug: Found {len(title_matched_articles)} title-matched articles")
            
            # 3. タイトルマッチ記事を最優先で追加
            for article_result in title_matched_articles:
                article_id = str(article_result.article.number)
                processed_article_ids.add(article_id)
                search_results.append(article_result)
                
                # カテゴリカウンター更新
                category = article_result.article.category or ""
                categories_seen[category] = categories_seen.get(category, 0) + 1
                
                if debug_mode:
                    logger.info(f"Debug: Added title-matched article {article_id}: {article_result.article.name} (score: {article_result.score:.6f})")
            
            # 4. 残りのセマンティック検索結果を処理
            high_quality_results_count = 0  # 高品質結果のカウント
            
            for i, (metadata, document, distance) in enumerate(zip(
                results["metadatas"][0],
                results["documents"][0], 
                results["distances"][0]
            )):
                article_id = results["ids"][0][i]
                
                # 既に処理済みの記事はスキップ
                if article_id in processed_article_ids:
                    if debug_mode and article_id == "818":
                        logger.info(f"Debug: Article 818 already processed as title match")
                    continue
                
                category = metadata.get("category", "")
                title = metadata.get("name", "")
                title_words = set(title.lower().split())
                
                # デバッグ情報
                if debug_mode and (article_id == "818" or "筋電" in title.lower()):
                    logger.info(f"Debug: Processing article {article_id}: {title}")
                    logger.info(f"Debug: Distance: {distance:.6f}, Category: {category}")
                
                # 類似度スコア計算（距離を類似度に変換）
                similarity_score = 1.0 - distance
                
                # タイトルマッチボーナスを事前計算してスレッショルドを調整
                title_match_bonus = 0.0
                query_words = query.lower().split()
                has_title_match = False
                for query_word in query_words:
                    if query_word in title.lower():
                        # タイトルの完全一致には非常に大きなボーナス
                        title_match_bonus += 0.5  # さらに大きなボーナス
                        has_title_match = True
                        if debug_mode and article_id == "818":
                            logger.info(f"Debug: Article 818 title match bonus: {title_match_bonus}")
                        break  # 最初のマッチで十分
                
                # 部分一致ボーナス
                for query_word in query_words:
                    for title_word in title_words:
                        if query_word in title_word or title_word in query_word:
                            title_match_bonus += 0.2  # 部分一致も強化
                            break
                
                # 最小類似度閾値をチェック（より厳格に設定）
                base_threshold = 0.6  # 大幅に上げる
                min_similarity_threshold = 0.4 if has_title_match else base_threshold
                
                # 特定のキーワードが本文に全く含まれない場合は除外
                content_relevance_check = self._check_content_relevance(document, query)
                if not content_relevance_check and similarity_score < 0.7:
                    if debug_mode:
                        logger.info(f"Debug: Article {article_id} filtered out by content relevance check")
                    continue
                
                if similarity_score < min_similarity_threshold:
                    if debug_mode and article_id == "818":
                        logger.info(f"Debug: Article 818 filtered out by similarity threshold: {similarity_score:.6f} (min: {min_similarity_threshold:.6f})")
                    continue
                
                # 高品質結果としてカウント
                high_quality_results_count += 1
                
                # カテゴリ多様性管理（同じカテゴリは最大3件まで）
                category_count = categories_seen.get(category, 0)
                if category_count >= 3:
                    if debug_mode and article_id == "818":
                        logger.info(f"Debug: Article 818 filtered out by category limit: {category} (count: {category_count})")
                    continue
                
                # 多様性ボーナス計算
                diversity_bonus = 0.0
                if category and category_count == 0:
                    diversity_bonus += 0.05  # 新しいカテゴリにボーナス
                
                # タイトルの重複チェック（既存のタイトルとの類似性）
                keyword_overlap_penalty = 0.0
                for seen_words in title_keywords_seen:
                    overlap_ratio = len(title_words & seen_words) / max(len(title_words), 1)
                    if overlap_ratio > 0.6:  # 60%以上重複
                        keyword_overlap_penalty = 0.1
                        break
                
                # 最終スコア計算
                final_score = similarity_score + title_match_bonus + diversity_bonus - keyword_overlap_penalty
                
                if debug_mode and article_id == "818":
                    logger.info(f"Debug: Article 818 final score: {final_score:.6f} (sim: {similarity_score:.6f}, title: {title_match_bonus:.6f}, div: {diversity_bonus:.6f}, penalty: {keyword_overlap_penalty:.6f})")
                
                # Article オブジェクトを構築
                # IDを正しく取得（ChromaDBのIDから）
                article_number = int(article_id)
                
                article = Article(
                    number=article_number,
                    name=metadata["name"],
                    full_name=metadata["name"],
                    wip=metadata["wip"],
                    body_md=document,
                    body_html="",
                    created_at=metadata["created_at"],
                    updated_at=metadata["updated_at"],
                    url=metadata["url"],
                    tags=metadata["tags"].split(",") if metadata["tags"] else [],
                    category=metadata["category"],
                    created_by_id=metadata.get("created_by_id"),
                    updated_by_id=metadata.get("created_by_id"),
                    processed_text=document
                )
                
                # より関連性の高いマッチテキストを抽出
                matched_text = self._extract_relevant_text(document, query)
                
                search_result = SearchResult(
                    article=article,
                    score=final_score,
                    matched_text=matched_text,
                    highlights=[query]
                )
                search_results.append(search_result)
                
                if debug_mode and article_id == "818":
                    logger.info(f"Debug: Article 818 successfully added to results")
                
                # カウンター更新
                categories_seen[category] = category_count + 1
                title_keywords_seen.add(frozenset(title_words))
            
            # 高品質な結果が少ない場合の警告
            total_quality_results = len(title_matched_articles) + high_quality_results_count
            if total_quality_results < 2:  # 閾値を2に下げる
                logger.warning(f"Very low quality search results for query '{query}': only {total_quality_results} high-quality matches found")
                
                # 関連記事がほとんどない場合は空の結果を返す
                if total_quality_results == 0:
                    logger.warning(f"No relevant articles found for query '{query}' - returning empty results")
                    return []
            
            # スコア順でソートして上位limit件を返す
            search_results.sort(key=lambda x: x.score, reverse=True)
            final_results = search_results[:limit]
            
            if debug_mode:
                logger.info(f"Debug: Final results count: {len(final_results)}")
                for i, result in enumerate(final_results):
                    logger.info(f"Debug: Result {i+1}: Article {result.article.number} (score: {result.score:.6f})")
            
            logger.info(f"Found {len(final_results)} diverse results for query: {query} (quality results: {total_quality_results})")
            return final_results
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    def _check_content_relevance(self, document: str, query: str) -> bool:
        """クエリと記事内容の関連性をチェック"""
        try:
            query_words = query.lower().split()
            document_lower = document.lower()
            
            # クエリの主要キーワードが本文に含まれているかチェック
            # 技術用語の場合は厳格にチェック
            tech_keywords = ['ubuntu', 'linux', 'windows', 'macos', 'docker', 'kubernetes', 'python', 'java', 'javascript']
            
            for word in query_words:
                if len(word) > 2:  # 短すぎる単語は除外
                    if word in tech_keywords:
                        # 技術用語は完全一致または関連語彙をチェック
                        related_terms = {
                            'ubuntu': ['ubuntu', 'linux', 'debian', 'apt'],
                            'linux': ['linux', 'unix', 'ubuntu', 'centos', 'redhat'],
                            'docker': ['docker', 'container', 'dockerfile', 'コンテナ'],
                            'python': ['python', 'pip', 'django', 'flask', 'pandas']
                        }
                        
                        if word in related_terms:
                            if any(term in document_lower for term in related_terms[word]):
                                return True
                        elif word in document_lower:
                            return True
                    else:
                        # 一般的な単語は部分一致でOK
                        if word in document_lower:
                            return True
            
            return False
            
        except Exception:
            # エラーの場合は緩い判定
            return True
    
    def _extract_relevant_text(self, document: str, query: str, max_length: int = 300) -> str:
        """クエリに最も関連する部分のテキストを抽出"""
        try:
            # クエリのキーワードを取得
            query_words = query.lower().split()
            sentences = document.split('。')
            
            best_sentence = ""
            best_score = 0
            
            for sentence in sentences:
                if len(sentence.strip()) < 10:  # 短すぎる文は除外
                    continue
                    
                sentence_lower = sentence.lower()
                score = sum(1 for word in query_words if word in sentence_lower)
                
                if score > best_score:
                    best_score = score
                    best_sentence = sentence
            
            # 最適な文が見つからない場合は冒頭を使用
            if not best_sentence:
                best_sentence = document[:max_length]
            
            # 長さ制限
            if len(best_sentence) > max_length:
                best_sentence = best_sentence[:max_length] + "..."
            
            return best_sentence.strip()
            
        except Exception:
            # エラーの場合は単純に冒頭を返す
            return document[:max_length] + "..." if len(document) > max_length else document
    
    def keyword_search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """キーワード検索"""
        try:
            # 簡単なキーワード検索の実装
            # 実際の実装では、より高度な全文検索エンジンを使用することを推奨
            results = self.collection.query(
                query_texts=[query],
                n_results=limit,
                include=["metadatas", "documents", "distances"]
            )
            
            search_results = []
            for i, (metadata, document, distance) in enumerate(zip(
                results["metadatas"][0],
                results["documents"][0],
                results["distances"][0]
            )):
                if query.lower() in document.lower():
                    article = Article(
                        number=int(results["ids"][0][i]),
                        name=metadata["name"],
                        full_name=metadata["name"],
                        wip=metadata["wip"],
                        body_md=document,
                        body_html="",
                        created_at=metadata["created_at"],
                        updated_at=metadata["updated_at"],
                        url=metadata["url"],
                        tags=metadata["tags"].split(",") if metadata["tags"] else [],
                        category=metadata["category"],
                        created_by_id=metadata["created_by_id"],
                        updated_by_id=metadata["created_by_id"],
                        processed_text=document
                    )
                    
                    search_result = SearchResult(
                        article=article,
                        score=0.8,  # キーワード検索のスコア
                        matched_text=document[:200] + "..." if len(document) > 200 else document,
                        highlights=[query]
                    )
                    search_results.append(search_result)
            
            return search_results[:limit]
            
        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return []
    
    def get_article_by_id(self, article_id: int) -> Optional[Article]:
        """記事IDで記事を取得"""
        try:
            from ..database.repositories.article_repository import ArticleRepository
            from ..database.connection import SessionLocal
            
            db_session = SessionLocal()
            try:
                article_repo = ArticleRepository(db=db_session)
                return article_repo.get_by_number(article_id)
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Failed to get article by ID {article_id}: {e}")
            return None
    
    def get_all_articles(self, limit: int = None, offset: int = 0) -> List[Article]:
        """全記事を取得"""
        try:
            from ..database.repositories.article_repository import ArticleRepository
            from ..database.connection import SessionLocal
            
            db_session = SessionLocal()
            try:
                article_repo = ArticleRepository(db=db_session)
                if limit:
                    return article_repo.get_paginated(limit=limit, offset=offset)
                else:
                    return article_repo.get_all()
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Failed to get all articles: {e}")
            return []
    
    def search_articles_by_category(self, category: str, limit: int = 10) -> List[Article]:
        """カテゴリで記事を検索"""
        try:
            from ..database.repositories.article_repository import ArticleRepository
            from ..database.connection import SessionLocal
            
            db_session = SessionLocal()
            try:
                article_repo = ArticleRepository(db=db_session)
                return article_repo.search_by_category(category, limit=limit)
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Failed to search articles by category {category}: {e}")
            return []
    
    def search_articles_by_tags(self, tags: List[str], limit: int = 10) -> List[Article]:
        """タグで記事を検索"""
        try:
            from ..database.repositories.article_repository import ArticleRepository
            from ..database.connection import SessionLocal
            
            db_session = SessionLocal()
            try:
                article_repo = ArticleRepository(db=db_session)
                return article_repo.search_by_tags(tags, limit=limit)
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Failed to search articles by tags {tags}: {e}")
            return []
    
    def _find_title_matches(self, query: str, debug_mode: bool = False) -> List[SearchResult]:
        """タイトルに直接マッチする記事を検索"""
        try:
            # ChromaDBから全記事のメタデータを取得
            all_results = self.collection.get(
                include=["metadatas", "documents"]
            )
            
            title_matches = []
            query_words = query.lower().split()
            
            for i, metadata in enumerate(all_results['metadatas']):
                title = metadata.get('name', '').lower()
                article_id = all_results['ids'][i]
                
                # クエリのキーワードがタイトルに含まれるかチェック
                has_match = False
                for query_word in query_words:
                    if query_word in title:
                        has_match = True
                        break
                
                if has_match:
                    # 高いスコアを付与（タイトルマッチなので優先度最高）
                    score = 2.0  # セマンティック検索より高いスコア
                    
                    # Article オブジェクトを構築
                    article_number = int(article_id)
                    document = all_results['documents'][i]
                    
                    article = Article(
                        number=article_number,
                        name=metadata["name"],
                        full_name=metadata["name"],
                        wip=metadata["wip"],
                        body_md=document,
                        body_html="",
                        created_at=metadata["created_at"],
                        updated_at=metadata["updated_at"],
                        url=metadata["url"],
                        tags=metadata["tags"].split(",") if metadata["tags"] else [],
                        category=metadata["category"],
                        created_by_id=metadata.get("created_by_id"),
                        updated_by_id=metadata.get("created_by_id"),
                        processed_text=document
                    )
                    
                    matched_text = self._extract_relevant_text(document, query)
                    
                    search_result = SearchResult(
                        article=article,
                        score=score,
                        matched_text=matched_text,
                        highlights=[query]
                    )
                    title_matches.append(search_result)
                    
                    if debug_mode:
                        logger.info(f"Debug: Title match found - Article {article_id}: {metadata['name']}")
            
            # タイトルマッチ記事をスコア順でソート（念のため）
            title_matches.sort(key=lambda x: x.score, reverse=True)
            
            return title_matches
            
        except Exception as e:
            logger.error(f"Title search error: {e}")
            return []
