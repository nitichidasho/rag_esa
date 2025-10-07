#!/usr/bin/env python3
"""
記事同期スクリプト
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# プロジェクトルートを sys.path に追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.esa_api_service import EsaAPIClient
from src.database.repositories.article_repository import ArticleRepository
from src.services.embedding_service import EmbeddingService
from src.services.search_service import SearchService
from src.utils.text_processing import TextProcessor
from src.config.settings import settings


def sync_recent_articles(hours: int = 24):
    """指定時間以内の更新記事を同期"""
    print(f"📥 過去{hours}時間以内の記事を同期中...")
    
    try:
        # サービス初期化
        api_client = EsaAPIClient()
        article_repo = ArticleRepository()
        search_service = SearchService()
        embedding_service = EmbeddingService()
        text_processor = TextProcessor()
        
        # 最近の記事を取得
        recent_posts = api_client.get_recent_posts(hours=hours)
        
        if not recent_posts:
            print("✅ 同期対象の記事はありませんでした")
            return 0
        
        success_count = 0
        for i, post_data in enumerate(recent_posts):
            try:
                # テキスト前処理
                processed_text = text_processor.clean_markdown(post_data["body_md"])
                summary = text_processor.create_summary(processed_text)
                
                # 埋め込みベクトル生成
                text_for_embedding = f"{post_data['name']} {processed_text}"
                embedding = embedding_service.generate_embedding(text_for_embedding)
                
                article_data = {
                    "number": post_data["number"],
                    "name": post_data["name"],
                    "full_name": post_data["full_name"],
                    "wip": post_data["wip"],
                    "body_md": post_data["body_md"],
                    "body_html": post_data["body_html"],
                    "created_at": post_data["created_at"],
                    "updated_at": post_data["updated_at"],
                    "url": post_data["url"],
                    "tags": post_data.get("tags", []),
                    "category": post_data.get("category", ""),
                    "created_by_id": post_data["created_by"]["id"],
                    "updated_by_id": post_data["updated_by"]["id"],
                    "processed_text": processed_text,
                    "embedding": embedding,
                    "summary": summary
                }
                
                # データベースに保存
                article_repo.upsert_article(article_data)
                
                # 記事をベクトルDBに追加
                if embedding:
                    from src.models.esa_models import Article
                    article_obj = Article(**article_data)
                    search_service.add_article(article_obj)
                
                success_count += 1
                print(f"  同期完了: {post_data['name']}")
                
            except Exception as e:
                print(f"⚠️ 記事 {post_data.get('number')} の同期でエラー: {e}")
                continue
        
        print(f"✅ {success_count}件の記事を同期しました")
        return success_count
        
    except Exception as e:
        print(f"❌ 同期エラー: {e}")
        return 0


def main():
    """メイン処理"""
    import argparse
    
    parser = argparse.ArgumentParser(description="esa.io記事の差分同期")
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="同期対象時間（時間）"
    )
    
    args = parser.parse_args()
    
    print("=== 研究室 esa.io RAGシステム 記事同期 ===")
    print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔧 同期対象: 過去{args.hours}時間")
    print()
    
    # 設定確認
    if not settings.esa_api_token or not settings.esa_team_name:
        print("❌ ESA_API_TOKEN と ESA_TEAM_NAME を .env ファイルに設定してください")
        sys.exit(1)
    
    try:
        # 同期実行
        synced_count = sync_recent_articles(args.hours)
        
        print()
        print("🎉 同期が完了しました！")
        print(f"📊 同期記事数: {synced_count}件")
        print(f"完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ 同期エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
