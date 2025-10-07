#!/usr/bin/env python3
"""
esa.io データエクスポートスクリプト
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from dateutil import parser as date_parser

# プロジェクトルートを sys.path に追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.esa_api_service import EsaAPIClient
from src.database.repositories.article_repository import ArticleRepository
from src.database.repositories.member_repository import MemberRepository
from src.services.embedding_service import EmbeddingService
from src.services.search_service import SearchService
from src.utils.text_processing import TextProcessor
from src.config.settings import settings


def export_members(api_client: EsaAPIClient, member_repo: MemberRepository):
    """メンバー情報のエクスポート"""
    print("📥 メンバー情報をエクスポート中...")
    
    try:
        members_response = api_client.get_members()
        members = members_response.get("members", [])
        
        for i, member_data in enumerate(members):
            try:
                # デバッグ: メンバーデータの構造を確認
                if i < 3:  # 最初の3件だけデバッグ情報を表示
                    print(f"メンバー {i+1} のデータ構造:")
                    print(f"  データ: {member_data}")
                
                # 既存メンバーをチェックしてからupsert
                screen_name = member_data["screen_name"]
                
                member_info = {
                    "id": hash(member_data["screen_name"]) % (2**31),  # 32bit整数に制限
                    "screen_name": member_data["screen_name"],
                    "name": member_data["name"],
                    "icon": member_data.get("icon", ""),
                    "role": member_data.get("role", "member"),
                    "posts_count": member_data.get("posts_count", 0),
                    "joined_at": date_parser.parse(member_data["joined_at"]) if member_data.get("joined_at") else None
                }
                
                # upsert_memberメソッドを使用（作成または更新）
                member_repo.upsert_member(member_info)
                    
            except Exception as e:
                print(f"⚠️ メンバー {i+1} ({member_data.get('screen_name', 'unknown')}) の処理でエラー: {e}")
                # セッションのロールバック（正しいセッションアクセス）
                try:
                    session = member_repo.get_session()
                    session.rollback()
                except Exception as rollback_error:
                    print(f"   ロールバックエラー: {rollback_error}")
                continue
        
        print(f"✅ {len(members)}人のメンバー情報をエクスポートしました")
        return len(members)
        
    except Exception as e:
        print(f"❌ メンバー情報エクスポートエラー: {e}")
        import traceback
        print(f"   詳細: {traceback.format_exc()}")
        return 0


def export_articles(api_client: EsaAPIClient, article_repo: ArticleRepository):
    """記事情報のエクスポート"""
    print("📥 記事情報をエクスポート中...")
    
    try:
        posts = api_client.export_all_posts()
        text_processor = TextProcessor()
        
        success_count = 0
        for i, post_data in enumerate(posts):
            try:
                # デバッグ: 記事データの構造を確認
                if i < 3:  # 最初の3件だけデバッグ情報を表示
                    print(f"記事 {post_data.get('number')} のデータ構造:")
                    print(f"  created_by: {post_data.get('created_by')} (type: {type(post_data.get('created_by'))})")
                    print(f"  updated_by: {post_data.get('updated_by')} (type: {type(post_data.get('updated_by'))})")
                
                # テキスト前処理
                processed_text = text_processor.clean_markdown(post_data["body_md"])
                summary = text_processor.create_summary(processed_text)
                
                # 作成者・更新者IDを安全に取得
                created_by_id = None
                if post_data.get("created_by"):
                    created_by = post_data["created_by"]
                    if isinstance(created_by, dict):
                        # screen_nameをハッシュ化してIDとして使用（メンバーテーブルと一致させる）
                        if "screen_name" in created_by:
                            created_by_id = hash(created_by["screen_name"])
                        elif "id" in created_by:
                            created_by_id = created_by["id"]
                    elif isinstance(created_by, (int, str)):
                        created_by_id = created_by
                
                updated_by_id = None
                if post_data.get("updated_by"):
                    updated_by = post_data["updated_by"]
                    if isinstance(updated_by, dict):
                        # screen_nameをハッシュ化してIDとして使用（メンバーテーブルと一致させる）
                        if "screen_name" in updated_by:
                            updated_by_id = hash(updated_by["screen_name"])
                        elif "id" in updated_by:
                            updated_by_id = updated_by["id"]
                    elif isinstance(updated_by, (int, str)):
                        updated_by_id = updated_by
                
                # 日時文字列をdatetimeオブジェクトに変換
                created_at = date_parser.parse(post_data["created_at"]) if post_data.get("created_at") else None
                updated_at = date_parser.parse(post_data["updated_at"]) if post_data.get("updated_at") else None
                
                article_data = {
                    "number": post_data["number"],
                    "name": post_data["name"],
                    "full_name": post_data["full_name"],
                    "wip": post_data["wip"],
                    "body_md": post_data["body_md"],
                    "body_html": post_data["body_html"],
                    "created_at": created_at,
                    "updated_at": updated_at,
                    "url": post_data["url"],
                    "tags": post_data.get("tags", []),
                    "category": post_data.get("category", ""),
                    "created_by_id": created_by_id,
                    "updated_by_id": updated_by_id,
                    "processed_text": processed_text,
                    "summary": summary
                }
                
                article_repo.upsert_article(article_data)
                success_count += 1
                
                # 10件ごとにコミットしてメモリとコネクションを開放
                if (i + 1) % 10 == 0:
                    try:
                        article_repo.db.commit()
                        print(f"  進捗: {i + 1}/{len(posts)} 記事を処理...")
                    except Exception as commit_error:
                        print(f"⚠️ コミットエラー (記事 {i+1}): {commit_error}")
                        article_repo.db.rollback()
                
            except Exception as e:
                print(f"⚠️ 記事 {post_data.get('number')} の処理でエラー: {e}")
                import traceback
                print(f"   詳細: {traceback.format_exc()}")
                # セッションのロールバック
                try:
                    article_repo.db.rollback()
                except:
                    pass
                continue
        
        # 最終コミット
        try:
            article_repo.db.commit()
            print(f"✅ {success_count}件の記事をエクスポートしました")
        except Exception as final_commit_error:
            print(f"⚠️ 最終コミットエラー: {final_commit_error}")
            article_repo.db.rollback()
        
        return success_count
        
    except Exception as e:
        print(f"❌ 記事エクスポートエラー: {e}")
        return 0


def generate_embeddings(article_repo: ArticleRepository, search_service: SearchService, skip_existing: bool = True):
    """埋め込みベクトルの生成（すべての記事を対象）"""
    print("🔄 埋め込みベクトルを生成中...")
    
    try:
        articles = article_repo.get_all(limit=None)  # 制限なしで全記事を取得
        embedding_service = EmbeddingService()
        
        print(f"📊 総記事数: {len(articles)}件")
        
        if skip_existing:
            # 未ベクトル化記事を特定
            articles_to_process = [a for a in articles if a.embedding is None]
            articles_with_embeddings = [a for a in articles if a.embedding is not None]
            
            print(f"📊 ベクトル化済み: {len(articles_with_embeddings)}件")
            print(f"📊 未ベクトル化: {len(articles_to_process)}件")
            
            if len(articles_to_process) == 0:
                print("🎉 すべての記事が既にベクトル化済みです！")
                return len(articles_with_embeddings)
        else:
            # すべての記事を再ベクトル化
            articles_to_process = articles
            articles_with_embeddings = []
            print(f"🔄 全記事を再ベクトル化します...")
        
        print(f"🔄 {len(articles_to_process)}件の記事をベクトル化します...")
        print()
        
        success_count = 0
        error_count = 0
        
        for i, article in enumerate(articles_to_process):
            try:
                # テキストが空でないかチェック
                text_for_embedding = f"{article.name} {article.processed_text}"
                if not text_for_embedding.strip():
                    print(f"⚠️ 記事 {article.number} のテキストが空です - スキップ")
                    error_count += 1
                    continue
                
                # 埋め込みベクトル生成
                embedding = embedding_service.generate_embedding(text_for_embedding)
                
                if embedding:
                    # データベースを更新
                    article_repo.update(article.number, {"embedding": embedding})
                    
                    # 記事をArticleオブジェクトに変換してベクトルDBに追加
                    from src.models.esa_models import Article
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
                else:
                    print(f"⚠️ 記事 {article.number} のベクトル生成に失敗")
                    error_count += 1
                
                # 進捗表示とコミット（50件ごと）
                if (i + 1) % 50 == 0 or (i + 1) == len(articles_to_process):
                    print(f"  進捗: {i + 1}/{len(articles_to_process)} 記事を処理... (成功: {success_count}, エラー: {error_count})")
                    
                    # 50件ごとにコミットしてメモリとコネクションを開放
                    try:
                        article_repo.db.commit()
                    except Exception as commit_error:
                        print(f"⚠️ コミットエラー: {commit_error}")
                        article_repo.db.rollback()
                    
            except Exception as e:
                print(f"⚠️ 記事 {article.number} のベクトル生成でエラー: {e}")
                error_count += 1
                # セッションのロールバック
                try:
                    article_repo.db.rollback()
                except:
                    pass
                continue
        
        # 最終コミット
        try:
            article_repo.db.commit()
        except Exception as final_commit_error:
            print(f"⚠️ 最終コミットエラー: {final_commit_error}")
            article_repo.db.rollback()
        
        total_vectorized = len(articles_with_embeddings) + success_count
        print(f"✅ {success_count}件の記事のベクトルを生成しました")
        print(f"📊 総ベクトル化記事数: {total_vectorized}件")
        if error_count > 0:
            print(f"⚠️ エラー件数: {error_count}件")
        
        return total_vectorized
        
    except Exception as e:
        print(f"❌ ベクトル生成エラー: {e}")
        import traceback
        print(f"詳細: {traceback.format_exc()}")
        return 0


def main():
    """メイン処理"""
    import argparse
    
    # コマンドライン引数の設定
    parser = argparse.ArgumentParser(description="esa.io データエクスポートスクリプト")
    parser.add_argument("--members-only", action="store_true", help="メンバー情報のみエクスポート")
    parser.add_argument("--articles-only", action="store_true", help="記事情報のみエクスポート")
    parser.add_argument("--vectorize-only", action="store_true", help="ベクトル化のみ実行")
    parser.add_argument("--force-vectorize", action="store_true", help="既存ベクトルも再生成")
    parser.add_argument("--skip-vectorize", action="store_true", help="ベクトル化をスキップ")
    
    args = parser.parse_args()
    
    print("=== 研究室 esa.io RAGシステム データエクスポート ===")
    print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 設定確認（ベクトル化のみの場合は不要）
    if not args.vectorize_only:
        if not settings.esa_api_token or not settings.esa_team_name:
            print("❌ ESA_API_TOKEN と ESA_TEAM_NAME を .env ファイルに設定してください")
            sys.exit(1)
        
        print(f"🔧 チーム: {settings.esa_team_name}")
        print(f"🔧 APIトークン: {'設定済み' if settings.esa_api_token else '未設定'}")
        print()
    
    try:
        # サービス初期化
        print("🔧 サービスを初期化中...")
        if not args.vectorize_only:
            api_client = EsaAPIClient()
        
        # データベースセッションを明示的に作成して管理
        from src.database.connection import SessionLocal
        db_session = SessionLocal()
        
        try:
            article_repo = ArticleRepository(db=db_session)
            member_repo = MemberRepository(db=db_session)
            search_service = SearchService()
            print("✅ サービス初期化完了")
            print()
            
            member_count = 0
            article_count = 0
            vector_count = 0
            
            # メンバー情報エクスポート
            if not args.articles_only and not args.vectorize_only:
                member_count = export_members(api_client, member_repo)
                print()
            
            # 記事情報エクスポート
            if not args.members_only and not args.vectorize_only:
                article_count = export_articles(api_client, article_repo)
                print()
            
            # 埋め込みベクトル生成
            if not args.skip_vectorize:
                skip_existing = not args.force_vectorize
                vector_count = generate_embeddings(article_repo, search_service, skip_existing)
                print()
            
        finally:
            # セッションを確実に閉じる
            db_session.close()
        
        # 結果表示
        print("🎉 処理が完了しました！")
        if member_count > 0:
            print(f"📊 メンバー: {member_count}人")
        if article_count > 0:
            print(f"📊 記事: {article_count}件")
        if vector_count > 0:
            print(f"📊 ベクトル化記事: {vector_count}件")
        print(f"完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 最終確認
        if vector_count > 0 and article_count > 0:
            print()
            print("🔍 ベクトル化結果の確認:")
            print(f"  - 総記事数に対するベクトル化率: {vector_count}/{article_count} ({vector_count/article_count*100:.1f}%)")
            if vector_count == article_count:
                print("  ✅ すべての記事がベクトル化されました！")
            else:
                print(f"  ⚠️ {article_count - vector_count}件の記事がベクトル化されていません")
        
    except Exception as e:
        print(f"❌ エクスポートエラー: {e}")
        sys.exit(1)


def generate_embeddings_enhanced(article_repo: ArticleRepository, search_service: SearchService, 
                                skip_existing: bool = True, use_enhanced_mode: bool = True):
    """強化された埋め込みベクトルの生成"""
    print("🔄 強化埋め込みベクトルを生成中...")
    if use_enhanced_mode:
        print("   ✨ チャンク分割による高精度処理")
        print("   ✨ 情報損失を最小化")
        print("   ✨ 長いテキストの適切な処理")
    
    try:
        articles = article_repo.get_all(limit=None)
        embedding_service = EmbeddingService()
        
        print(f"📊 総記事数: {len(articles)}件")
        
        if skip_existing:
            articles_to_process = [a for a in articles if a.embedding is None]
            articles_with_embeddings = [a for a in articles if a.embedding is not None]
            
            print(f"📊 ベクトル化済み: {len(articles_with_embeddings)}件")
            print(f"📊 未ベクトル化: {len(articles_to_process)}件")
            
            if len(articles_to_process) == 0:
                print("🎉 すべての記事が既にベクトル化済みです！")
                return len(articles_with_embeddings)
        else:
            articles_to_process = articles
            articles_with_embeddings = []
            print(f"🔄 全記事を強化モードで再ベクトル化します...")
        
        print(f"🔄 {len(articles_to_process)}件の記事を強化ベクトル化します...")
        print()
        
        success_count = 0
        error_count = 0
        enhanced_count = 0  # 強化処理が適用された記事数
        
        for i, article in enumerate(articles_to_process):
            try:
                # 進捗表示
                if (i + 1) % 50 == 0 or i == 0:
                    print(f"🔄 進捗: {i + 1}/{len(articles_to_process)} ({(i + 1)/len(articles_to_process)*100:.1f}%)")
                
                # テキストの構築
                title_text = article.name or ""
                content_text = article.processed_text or article.body_md or ""
                
                # タイトルと本文を組み合わせ（タイトルに重みを付ける）
                full_text = f"{title_text} {title_text} {content_text}".strip()
                
                if not full_text:
                    print(f"⚠️ 記事 {article.number} のテキストが空です - スキップ")
                    error_count += 1
                    continue
                
                # 強化モードでベクトル生成
                embedding = embedding_service.generate_embedding(
                    full_text, 
                    use_chunking=use_enhanced_mode
                )
                
                # 長いテキストの場合は強化処理が適用される
                if use_enhanced_mode and len(full_text) > 400:
                    enhanced_count += 1
                
                if embedding:
                    # データベース更新
                    article_repo.update(article.number, {"embedding": embedding})
                    
                    # ベクトルDBに追加
                    from src.models.esa_models import Article
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
                    
                    # ベクトルDBに保存
                    try:
                        search_service.add_article(article_obj)
                        success_count += 1
                    except Exception as vector_error:
                        print(f"⚠️ 記事 {article.number} のベクトルDB保存でエラー: {vector_error}")
                        success_count += 1  # データベースには保存されているのでカウント
                
                else:
                    print(f"❌ 記事 {article.number} のベクトル生成に失敗")
                    error_count += 1
                    
            except Exception as e:
                print(f"❌ 記事 {article.number} の処理中にエラー: {e}")
                error_count += 1
        
        print()
        print(f"✅ 強化ベクトル化完了!")
        print(f"📊 成功: {success_count}件")
        if enhanced_count > 0:
            print(f"📊 強化処理適用: {enhanced_count}件")
        if error_count > 0:
            print(f"📊 エラー: {error_count}件")
        
        # 最終的なベクトル化済み記事数を返す
        return success_count + len(articles_with_embeddings)
        
    except Exception as e:
        print(f"❌ 強化ベクトル化エラー: {e}")
        import traceback
        print(f"詳細: {traceback.format_exc()}")
        return 0


if __name__ == "__main__":
    main()
