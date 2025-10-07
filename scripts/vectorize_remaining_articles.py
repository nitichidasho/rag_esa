#!/usr/bin/env python3
"""
残りの記事をベクトル化するスクリプト
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# プロジェクトルートを sys.path に追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.repositories.article_repository import ArticleRepository
from src.services.embedding_service import EmbeddingService
from src.services.search_service import SearchService
from src.database.connection import SessionLocal
from src.models.esa_models import Article


def vectorize_remaining_articles():
    """未ベクトル化の記事をすべてベクトル化"""
    print("=== 残り記事のベクトル化処理 ===")
    print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # データベースセッションを作成
    db_session = SessionLocal()
    
    try:
        article_repo = ArticleRepository(db=db_session)
        embedding_service = EmbeddingService()
        search_service = SearchService()
        
        # 全記事を取得
        print("📊 データベースから記事を取得中...")
        all_articles = article_repo.get_all()
        total_articles = len(all_articles)
        print(f"総記事数: {total_articles}件")
        
        # 未ベクトル化記事を特定
        articles_without_embeddings = [a for a in all_articles if a.embedding is None]
        articles_with_embeddings = [a for a in all_articles if a.embedding is not None]
        
        print(f"ベクトル化済み: {len(articles_with_embeddings)}件")
        print(f"未ベクトル化: {len(articles_without_embeddings)}件")
        print()
        
        if len(articles_without_embeddings) == 0:
            print("🎉 すべての記事が既にベクトル化済みです！")
            return
        
        print(f"🔄 {len(articles_without_embeddings)}件の記事をベクトル化します...")
        
        success_count = 0
        error_count = 0
        
        for i, article in enumerate(articles_without_embeddings):
            try:
                # 埋め込みベクトル生成
                text_for_embedding = f"{article.name} {article.processed_text}"
                
                # テキストが空でないかチェック
                if not text_for_embedding.strip():
                    print(f"⚠️ 記事 {article.number} のテキストが空です - スキップ")
                    continue
                
                embedding = embedding_service.generate_embedding(text_for_embedding)
                
                if embedding:
                    # データベースを更新
                    article_repo.update(article.number, {"embedding": embedding})
                    
                    # 記事をArticleオブジェクトに変換してベクトルDBに追加
                    article_obj = Article(
                        number=article.number,
                        name=article.name,
                        full_name=article.full_name,
                        wip=article.wip,
                        body_md=article.body_md,
                        body_html=article.body_html,
                        created_at=article.created_at,
                        updated_at=article.updated_at,
                        url=article.url,
                        tags=article.tags or [],
                        category=article.category or "",
                        created_by_id=article.created_by_id,
                        updated_by_id=article.updated_by_id,
                        processed_text=article.processed_text,
                        embedding=embedding,
                        summary=article.summary
                    )
                    
                    search_service.add_article(article_obj)
                    success_count += 1
                    
                    # 進捗表示
                    if (i + 1) % 50 == 0 or (i + 1) == len(articles_without_embeddings):
                        print(f"  進捗: {i + 1}/{len(articles_without_embeddings)} 記事を処理... (成功: {success_count}, エラー: {error_count})")
                        
                        # 50件ごとにコミット
                        try:
                            db_session.commit()
                        except Exception as commit_error:
                            print(f"⚠️ コミットエラー: {commit_error}")
                            db_session.rollback()
                else:
                    print(f"⚠️ 記事 {article.number} のベクトル生成に失敗")
                    error_count += 1
                    
            except Exception as e:
                print(f"⚠️ 記事 {article.number} のベクトル生成でエラー: {e}")
                error_count += 1
                continue
        
        # 最終コミット
        try:
            db_session.commit()
        except Exception as final_commit_error:
            print(f"⚠️ 最終コミットエラー: {final_commit_error}")
            db_session.rollback()
        
        print()
        print("🎉 ベクトル化処理が完了しました！")
        print(f"📊 成功: {success_count}件")
        print(f"📊 エラー: {error_count}件")
        print(f"📊 総ベクトル化記事数: {len(articles_with_embeddings) + success_count}件")
        print(f"完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ ベクトル化処理エラー: {e}")
        import traceback
        print(f"詳細: {traceback.format_exc()}")
        
    finally:
        # セッションを確実に閉じる
        db_session.close()


if __name__ == "__main__":
    vectorize_remaining_articles()
