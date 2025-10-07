#!/usr/bin/env python3
"""
データ確認スクリプト
"""

import sys
from pathlib import Path

# プロジェクトルートを sys.path に追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.repositories.article_repository import ArticleRepository
from src.database.repositories.member_repository import MemberRepository
from src.database.connection import SessionLocal


def check_articles():
    """記事データの確認"""
    print("📊 記事データを確認中...")
    
    db_session = SessionLocal()
    try:
        article_repo = ArticleRepository(db=db_session)
        articles = article_repo.get_all()
        
        print(f"📈 総記事数: {len(articles)}件")
        
        if articles:
            print("\n📝 最初の3件の記事:")
            for i, article in enumerate(articles[:3]):
                print(f"\n記事 {i+1}:")
                print(f"  番号: {article.number}")
                print(f"  タイトル: {article.name}")
                print(f"  カテゴリ: {article.category}")
                print(f"  作成日: {article.created_at}")
                print(f"  更新日: {article.updated_at}")
                print(f"  WIP: {article.wip}")
                print(f"  URL: {article.url}")
                print(f"  本文（最初の100文字）: {article.body_md[:100] if article.body_md else 'なし'}...")
                print(f"  処理済みテキスト（最初の100文字）: {article.processed_text[:100] if article.processed_text else 'なし'}...")
                print(f"  要約: {article.summary[:100] if article.summary else 'なし'}...")
                print(f"  埋め込みベクトル: {'あり' if article.embedding else 'なし'}")
                
        return len(articles)
        
    except Exception as e:
        print(f"❌ 記事データ確認エラー: {e}")
        return 0
    finally:
        db_session.close()


def check_members():
    """メンバーデータの確認"""
    print("\n👥 メンバーデータを確認中...")
    
    db_session = SessionLocal()
    try:
        member_repo = MemberRepository(db=db_session)
        members = member_repo.get_all()
        
        print(f"📈 総メンバー数: {len(members)}件")
        
        if members:
            print("\n👤 最初の3件のメンバー:")
            for i, member in enumerate(members[:3]):
                print(f"\nメンバー {i+1}:")
                print(f"  ID: {member.id}")
                print(f"  スクリーンネーム: {member.screen_name}")
                print(f"  名前: {member.name}")
                print(f"  ロール: {member.role}")
                print(f"  投稿数: {member.posts_count}")
                print(f"  参加日: {member.joined_at}")
                
        return len(members)
        
    except Exception as e:
        print(f"❌ メンバーデータ確認エラー: {e}")
        return 0
    finally:
        db_session.close()


def check_vector_db():
    """ベクトルDBの確認"""
    print("\n🔍 ベクトルデータベースを確認中...")
    
    try:
        from src.services.search_service import SearchService
        search_service = SearchService()
        
        # ベクトルDBの統計情報を取得
        stats = search_service.collection.count()
        print(f"📈 ベクトルDB内の記事数: {stats}件")
        
        # 簡単な検索テスト
        if stats > 0:
            print("\n🔎 検索テスト（'研究'で検索）:")
            results = search_service.semantic_search("研究", limit=3)
            for i, result in enumerate(results):
                print(f"\n検索結果 {i+1}:")
                print(f"  記事番号: {result.article.number}")
                print(f"  タイトル: {result.article.name}")
                print(f"  スコア: {result.score:.4f}")
                print(f"  マッチしたテキスト: {result.matched_text[:100]}...")
        
        return stats
        
    except Exception as e:
        print(f"❌ ベクトルDB確認エラー: {e}")
        return 0


def main():
    """メイン処理"""
    print("=== 研究室 esa.io RAGシステム データ確認 ===")
    print()
    
    # 記事データ確認
    article_count = check_articles()
    
    # メンバーデータ確認
    member_count = check_members()
    
    # ベクトルDB確認
    vector_count = check_vector_db()
    
    print("\n" + "="*50)
    print("📊 データ確認結果:")
    print(f"📝 記事: {article_count}件")
    print(f"👥 メンバー: {member_count}件")
    print(f"🔍 ベクトル: {vector_count}件")
    print("="*50)


if __name__ == "__main__":
    main()
