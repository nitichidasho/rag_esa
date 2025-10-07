#!/usr/bin/env python3
"""
記事表示・検索のデモスクリプト
"""

import sys
from pathlib import Path

# プロジェクトルートを sys.path に追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.search_service import SearchService
from src.database.repositories.article_repository import ArticleRepository
from src.database.connection import SessionLocal


def demo_article_search():
    """記事検索のデモ"""
    print("=== 記事検索・表示デモ ===")
    
    search_service = SearchService()
    
    # 1. 記事数確認
    print("\n📊 データ確認:")
    db_session = SessionLocal()
    try:
        article_repo = ArticleRepository(db=db_session)
        total_articles = article_repo.count_articles()
        print(f"総記事数: {total_articles}件")
        
        # 2. 最新記事表示
        print("\n📝 最新記事 (5件):")
        recent_articles = article_repo.get_recent_articles(limit=5)
        for i, article in enumerate(recent_articles, 1):
            print(f"{i}. [{article.number}] {article.name}")
            print(f"   カテゴリ: {article.category}")
            print(f"   更新日: {article.updated_at}")
            print()
        
        # 3. カテゴリ検索
        print("\n🏷️ カテゴリ検索 ('研究' を含む記事):")
        category_articles = article_repo.search_by_category("研究", limit=3)
        for i, article in enumerate(category_articles, 1):
            print(f"{i}. [{article.number}] {article.name}")
            print(f"   カテゴリ: {article.category}")
            print()
        
    finally:
        db_session.close()
    
    # 4. セマンティック検索
    print("\n🔍 セマンティック検索 ('機械学習'):")
    search_results = search_service.semantic_search("機械学習", limit=3)
    for i, result in enumerate(search_results, 1):
        print(f"{i}. [{result.article.number}] {result.article.name}")
        print(f"   スコア: {result.score:.4f}")
        print(f"   マッチしたテキスト: {result.matched_text[:100]}...")
        print()
    
    # 5. 特定記事の詳細表示
    if search_results:
        article_id = search_results[0].article.number
        print(f"\n📖 記事詳細表示 (記事ID: {article_id}):")
        article = search_service.get_article_by_id(article_id)
        if article:
            print(f"タイトル: {article.name}")
            print(f"フルタイトル: {article.full_name}")
            print(f"カテゴリ: {article.category}")
            print(f"タグ: {article.tags}")
            print(f"WIP: {'はい' if article.wip else 'いいえ'}")
            print(f"URL: {article.url}")
            print(f"作成日: {article.created_at}")
            print(f"更新日: {article.updated_at}")
            print(f"要約: {article.summary[:200] if article.summary else 'なし'}...")
            print(f"本文（最初の300文字）:")
            print(f"{article.body_md[:300] if article.body_md else 'なし'}...")


def demo_browse_articles():
    """記事ブラウジングのデモ"""
    print("\n=== 記事ブラウジングデモ ===")
    
    db_session = SessionLocal()
    try:
        article_repo = ArticleRepository(db=db_session)
        
        # ページ分割で記事を表示
        page_size = 5
        page = 0
        
        while True:
            print(f"\n📄 ページ {page + 1} (記事 {page * page_size + 1}-{(page + 1) * page_size}):")
            articles = article_repo.get_paginated(limit=page_size, offset=page * page_size)
            
            if not articles:
                print("これ以上記事がありません。")
                break
            
            for i, article in enumerate(articles, 1):
                print(f"{page * page_size + i}. [{article.number}] {article.name}")
                print(f"   カテゴリ: {article.category}")
                print(f"   更新日: {article.updated_at}")
                print()
            
            # 簡単なページング制御（デモ用）
            if page >= 2:  # 3ページまで表示してデモ終了
                print("（デモのため、ここで終了します）")
                break
            
            page += 1
            
    finally:
        db_session.close()


def main():
    print("=== 研究室 esa.io RAGシステム 記事機能デモ ===")
    
    try:
        # 記事検索デモ
        demo_article_search()
        
        # 記事ブラウジングデモ
        demo_browse_articles()
        
        print("\n✅ デモ完了")
        
    except Exception as e:
        print(f"❌ デモ実行エラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
