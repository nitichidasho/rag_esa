#!/usr/bin/env python3
"""
研究室RAGシステム 統合管理コマンド
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# プロジェクトルートを sys.path に追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import settings


def setup_argument_parser():
    """コマンドライン引数の設定"""
    parser = argparse.ArgumentParser(
        description="研究室RAGシステム 統合管理コマンド",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python rag_manager.py export           # esa.io からデータをエクスポート
  python rag_manager.py vectorize        # 記事をベクトル化
  python rag_manager.py vectorize --enhanced  # 強化ベクトル化（高精度）
  python rag_manager.py vectorize --force --enhanced  # 全記事を強化再ベクトル化
  python rag_manager.py vectorize --model intfloat/multilingual-e5-base  # カスタムモデル使用
  python rag_manager.py check           # データ状況を確認
  python rag_manager.py check --detailed --verify-vectors  # ベクトルデータ整合性確認
  python rag_manager.py search "検索語"  # 記事を検索
  python rag_manager.py search "筋電" --find-article 818  # 特定記事の検索対象確認
  python rag_manager.py search "Ubuntu インストール" --hybrid  # ハイブリッド検索
  python rag_manager.py search "ROS エラー" --hybrid --explain  # ハイブリッド検索（詳細表示）
  python rag_manager.py search "機械学習" --hybrid --sparse-weight 0.8 --dense-weight 0.2  # 重み調整
  python rag_manager.py serve           # Webアプリを起動
  python rag_manager.py full            # 全体処理（エクスポート+ベクトル化）
  python rag_manager.py full --enhanced # 全体処理（強化ベクトル化）
  python rag_manager.py full --skip-export --enhanced --force  # ベクトル化のみ強化モード
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='実行するコマンド')
    
    # エクスポートコマンド
    export_parser = subparsers.add_parser('export', help='esa.io からデータをエクスポート')
    export_parser.add_argument('--members-only', action='store_true', help='メンバー情報のみエクスポート')
    export_parser.add_argument('--articles-only', action='store_true', help='記事情報のみエクスポート')
    
    # ベクトル化コマンド
    vectorize_parser = subparsers.add_parser('vectorize', help='記事をベクトル化')
    vectorize_parser.add_argument('--force', action='store_true', help='既存ベクトルも再生成')
    vectorize_parser.add_argument('--enhanced', action='store_true', help='強化されたベクトル化（チャンク分割・高精度）')
    vectorize_parser.add_argument('--model', type=str, help='使用するembeddingモデル名')
    
    # データ確認コマンド
    check_parser = subparsers.add_parser('check', help='データ状況を確認')
    check_parser.add_argument('--detailed', action='store_true', help='詳細情報を表示')
    check_parser.add_argument('--verify-vectors', action='store_true', help='ベクトルデータの整合性を確認')
    
    # 検索コマンド
    search_parser = subparsers.add_parser('search', help='記事を検索')
    search_parser.add_argument('query', help='検索クエリ')
    search_parser.add_argument('--limit', type=int, default=5, help='表示件数（デフォルト: 5）')
    search_parser.add_argument('--find-article', type=int, help='特定の記事番号を検索対象に含めて確認')
    search_parser.add_argument('--hybrid', action='store_true', help='ハイブリッド検索を使用（BM25 + ベクトル検索）')
    search_parser.add_argument('--sparse-weight', type=float, default=0.7, help='スパース検索（BM25）の重み（デフォルト: 0.7）')
    search_parser.add_argument('--dense-weight', type=float, default=0.3, help='密ベクトル検索の重み（デフォルト: 0.3）')
    search_parser.add_argument('--explain', action='store_true', help='検索結果の詳細スコア情報を表示')
    
    # Webアプリ起動コマンド
    serve_parser = subparsers.add_parser('serve', help='Webアプリを起動')
    serve_parser.add_argument('--port', type=int, default=8000, help='ポート番号（デフォルト: 8000）')
    serve_parser.add_argument('--frontend', action='store_true', help='フロントエンドも起動')
    
    # 全体処理コマンド
    full_parser = subparsers.add_parser('full', help='全体処理（エクスポート+ベクトル化）')
    full_parser.add_argument('--skip-export', action='store_true', help='エクスポートをスキップ')
    full_parser.add_argument('--enhanced', action='store_true', help='強化されたベクトル化（チャンク分割・高精度）')
    full_parser.add_argument('--force', action='store_true', help='既存ベクトルも再生成')
    full_parser.add_argument('--model', type=str, help='使用するembeddingモデル名')
    
    return parser


def export_data(args):
    """データエクスポート処理"""
    print("🔄 データエクスポート処理を開始...")
    
    # export_esa_data.pyの機能を直接実行
    try:
        import sys
        from pathlib import Path
        from datetime import datetime
        
        # プロジェクトルートを sys.path に追加
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        
        from src.services.esa_api_service import EsaAPIClient
        from src.database.repositories.article_repository import ArticleRepository
        from src.database.repositories.member_repository import MemberRepository
        from src.services.search_service import SearchService
        from src.services.embedding_service import EmbeddingService
        from src.database.connection import SessionLocal
        
        # サービス初期化
        print("🔧 サービスを初期化中...")
        
        # 埋め込みサービスとSearchServiceを先に初期化
        embedding_service = EmbeddingService()
        search_service = SearchService()
        print("✅ サービス初期化完了")
        
        api_client = EsaAPIClient()
        db_session = SessionLocal()
        
        try:
            article_repo = ArticleRepository(db=db_session)
            member_repo = MemberRepository(db=db_session)
            
            # メンバー情報エクスポート（オプション引数チェック）
            if not getattr(args, 'articles_only', False):
                from scripts.export_esa_data import export_members
                member_count = export_members(api_client, member_repo)
            else:
                member_count = 0
                print("⏭️ メンバー情報エクスポートをスキップ")
            
            # 記事情報エクスポート（オプション引数チェック）
            if not getattr(args, 'members_only', False):
                from scripts.export_esa_data import export_articles
                article_count = export_articles(api_client, article_repo)
            else:
                article_count = 0
                print("⏭️ 記事情報エクスポートをスキップ")
            
            print(f"✅ データエクスポートが完了しました")
            if member_count > 0:
                print(f"   メンバー: {member_count}人")
            if article_count > 0:
                print(f"   記事: {article_count}件")
            
        finally:
            db_session.close()
            
    except Exception as e:
        print(f"❌ データエクスポートエラー: {e}")
        import traceback
        print(f"   詳細: {traceback.format_exc()}")
        sys.exit(1)


def vectorize_articles(args):
    """記事ベクトル化処理（改良版）"""
    enhanced_mode = getattr(args, 'enhanced', False)
    custom_model = getattr(args, 'model', None)
    
    if enhanced_mode:
        print("🔄 強化ベクトル化処理を開始...")
        print("   ✨ チャンク分割による高精度処理")
        print("   ✨ 情報損失を最小化")
    else:
        print("🔄 記事ベクトル化処理を開始...")
    
    if custom_model:
        print(f"   🎯 カスタムモデル: {custom_model}")
    
    try:
        import sys
        from pathlib import Path
        
        # プロジェクトルートを sys.path に追加
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        
        from src.database.repositories.article_repository import ArticleRepository
        from src.services.search_service import SearchService
        from src.services.embedding_service import EmbeddingService
        from src.database.connection import SessionLocal
        
        # データベースセッション作成
        db_session = SessionLocal()
        
        try:
            article_repo = ArticleRepository(db=db_session)
            
            # カスタムモデル指定の場合は一時的に設定変更
            if custom_model:
                from src.config.settings import settings
                original_model = settings.hf_model_name
                settings.hf_model_name = custom_model
                print(f"   📝 モデルを一時変更: {original_model} → {custom_model}")
            
            # 埋め込みサービスとSearchServiceを初期化
            embedding_service = EmbeddingService()
            search_service = SearchService()
            
            # ベクトル化実行
            force_regenerate = getattr(args, 'force', False)
            
            from scripts.export_esa_data import generate_embeddings_enhanced
            vector_count = generate_embeddings_enhanced(
                article_repo, 
                search_service, 
                skip_existing=not force_regenerate,
                use_enhanced_mode=enhanced_mode
            )
            
            # モデル設定を元に戻す
            if custom_model:
                settings.hf_model_name = original_model
                print(f"   📝 モデル設定を復元: {custom_model} → {original_model}")
            
            print(f"✅ ベクトル化が完了しました")
            print(f"   ベクトル化記事数: {vector_count}件")
            if enhanced_mode:
                print(f"   🎯 強化モードによる高精度処理完了")
            
        finally:
            db_session.close()
            
    except Exception as e:
        print(f"❌ ベクトル化エラー: {e}")
        import traceback
        print(f"   詳細: {traceback.format_exc()}")
        sys.exit(1)


def check_data(args):
    """データ状況確認"""
    print("📊 データ状況を確認中...")
    
    try:
        import sys
        from pathlib import Path
        
        # プロジェクトルートを sys.path に追加
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        
        from src.database.repositories.article_repository import ArticleRepository
        from src.database.repositories.member_repository import MemberRepository
        from src.database.connection import SessionLocal
        
        # データベースセッション作成
        db_session = SessionLocal()
        
        try:
            article_repo = ArticleRepository(db=db_session)
            member_repo = MemberRepository(db=db_session)
            
            # データ状況確認
            articles = article_repo.get_all(limit=None)
            members = member_repo.get_all()
            
            vectorized_articles = [a for a in articles if a.embedding is not None]
            unvectorized_articles = [a for a in articles if a.embedding is None]
            
            print(f"✅ データ状況:")
            print(f"   メンバー数: {len(members)}人")
            print(f"   総記事数: {len(articles)}件")
            print(f"   ベクトル化済み: {len(vectorized_articles)}件")
            print(f"   未ベクトル化: {len(unvectorized_articles)}件")
            
            if len(articles) > 0:
                vectorization_rate = len(vectorized_articles) / len(articles) * 100
                print(f"   ベクトル化率: {vectorization_rate:.1f}%")
            
            # 詳細情報の表示
            detailed = getattr(args, 'detailed', False)
            if detailed:
                print(f"\n📋 詳細情報:")
                
                # 最新記事の確認
                if articles:
                    recent_articles = sorted(articles, key=lambda x: x.updated_at or x.created_at, reverse=True)[:5]
                    print(f"\n最新記事（上位5件）:")
                    for i, article in enumerate(recent_articles, 1):
                        print(f"  {i}. 記事{article.number}: {article.name}")
                        print(f"     更新日: {article.updated_at}")
                        print(f"     カテゴリ: {article.category}")
                        print(f"     ベクトル化: {'✅' if article.embedding else '❌'}")
                        print(f"     テキスト長: {len(article.processed_text or article.body_md or '') if article.processed_text or article.body_md else 0}文字")
                        print()
                
                # カテゴリ別統計
                categories = {}
                for article in articles:
                    cat = article.category or "未分類"
                    categories[cat] = categories.get(cat, 0) + 1
                
                print(f"📂 カテゴリ別記事数:")
                for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10]:
                    print(f"   {cat}: {count}件")
                
                # ベクトルデータベースの確認
                try:
                    from src.services.search_service import SearchService
                    search_service = SearchService()
                    
                    # ChromaDBから直接データを確認
                    collection = search_service.collection
                    chroma_count = collection.count()
                    print(f"\n🔍 ChromaDBの状況:")
                    print(f"   ベクトルDB内記事数: {chroma_count}件")
                    
                    if chroma_count != len(vectorized_articles):
                        print(f"   ⚠️ データベースとベクトルDBの件数が一致しません")
                        print(f"   データベース: {len(vectorized_articles)}件")
                        print(f"   ベクトルDB: {chroma_count}件")
                    
                    # ベクトル整合性確認
                    verify_vectors = getattr(args, 'verify_vectors', False)
                    if verify_vectors:
                        print(f"\n🔍 ベクトルデータ整合性確認:")
                        
                        # サンプル記事で確認
                        sample_articles = vectorized_articles[:5]  # 最初の5件をサンプル
                        for article in sample_articles:
                            try:
                                # SQLiteからベクトル取得
                                sqlite_embedding = article.embedding
                                
                                # ChromaDBからベクトル取得
                                chroma_result = collection.get(
                                    ids=[str(article.number)],
                                    include=["embeddings"]
                                )
                                
                                if chroma_result["embeddings"]:
                                    chroma_embedding = chroma_result["embeddings"][0]
                                    
                                    # ベクトルサイズ確認
                                    sqlite_size = len(sqlite_embedding) if sqlite_embedding else 0
                                    chroma_size = len(chroma_embedding) if chroma_embedding else 0
                                    
                                    if sqlite_size == chroma_size and sqlite_size > 0:
                                        # 最初の3要素を比較（完全一致は計算誤差もあるので近似比較）
                                        import numpy as np
                                        sqlite_vec = np.array(sqlite_embedding[:3])
                                        chroma_vec = np.array(chroma_embedding[:3])
                                        similarity = np.dot(sqlite_vec, chroma_vec)
                                        
                                        if similarity > 0.99:  # 非常に高い類似度
                                            status = "✅"
                                        else:
                                            status = "⚠️"
                                        
                                        print(f"   記事{article.number}: {status} SQLite({sqlite_size}) ↔ Chroma({chroma_size}) 類似度:{similarity:.4f}")
                                    else:
                                        print(f"   記事{article.number}: ❌ サイズ不一致 SQLite({sqlite_size}) ↔ Chroma({chroma_size})")
                                else:
                                    print(f"   記事{article.number}: ❌ ChromaDBにベクトルなし")
                                    
                            except Exception as verify_error:
                                print(f"   記事{article.number}: ❌ 確認エラー: {verify_error}")
                        
                        print(f"\n📊 ベクトルデータの説明:")
                        print(f"   SQLite: JSONフィールドとして記事テーブルに保存")
                        print(f"   ChromaDB: 専用ベクトルDBで高速検索に最適化")
                        print(f"   データ同期: ベクトル化時に両方に同じデータを保存")
                    
                except Exception as search_error:
                    print(f"   ❌ ベクトルDB確認エラー: {search_error}")
            
        finally:
            db_session.close()
            
    except Exception as e:
        print(f"❌ データ確認エラー: {e}")
        import traceback
        print(f"   詳細: {traceback.format_exc()}")
        sys.exit(1)


def search_articles(args):
    """記事検索（ハイブリッド検索対応版）"""
    search_type = "ハイブリッド" if args.hybrid else "セマンティック"
    print(f"🔍 '{args.query}' で記事を{search_type}検索中...")
    
    if args.hybrid:
        print(f"   ⚖️  スパース重み: {args.sparse_weight:.1f}, 密ベクトル重み: {args.dense_weight:.1f}")
    
    # 特定記事確認オプション
    find_article_num = getattr(args, 'find_article', None)
    if find_article_num:
        print(f"   🎯 記事{find_article_num}の検索対象確認も実行")
    
    try:
        if args.hybrid:
            # ハイブリッド検索を使用
            from src.services.hybrid_search_service import HybridSearchService
            search_service = HybridSearchService()
        else:
            # 従来のセマンティック検索を使用
            from src.services.search_service import SearchService
            search_service = SearchService()
        
        from src.database.repositories.article_repository import ArticleRepository
        from src.database.connection import SessionLocal
        
        # 特定記事の確認
        if find_article_num:
            print(f"\n🔍 記事{find_article_num}の確認:")
            
            # データベースから記事を取得
            db_session = SessionLocal()
            try:
                article_repo = ArticleRepository(db=db_session)
                target_article = article_repo.get_by_number(find_article_num)
                
                if target_article:
                    print(f"   ✅ データベース内に存在:")
                    print(f"      タイトル: {target_article.name}")
                    print(f"      カテゴリ: {target_article.category}")
                    print(f"      ベクトル化: {'✅' if target_article.embedding else '❌'}")
                    print(f"      テキスト長: {len(target_article.processed_text or '') if target_article.processed_text else 0}文字")
                    
                    # ChromaDBでの確認
                    try:
                        if args.hybrid:
                            # ハイブリッド検索サービスの場合
                            collection = search_service.search_service.collection
                        else:
                            collection = search_service.collection
                            
                        chroma_result = collection.get(
                            ids=[str(find_article_num)],
                            include=["metadatas", "documents"]
                        )
                        
                        if chroma_result["ids"]:
                            print(f"   ✅ ChromaDB内に存在")
                            chroma_title = chroma_result["metadatas"][0].get("name", "")
                            print(f"      ChromaDBタイトル: {chroma_title}")
                        else:
                            print(f"   ❌ ChromaDB内に存在しません")
                            
                    except Exception as chroma_error:
                        print(f"   ❌ ChromaDB確認エラー: {chroma_error}")
                        
                else:
                    print(f"   ❌ 記事{find_article_num}はデータベース内に存在しません")
                    
            finally:
                db_session.close()
            
            print()
        
        # 検索実行
        if args.hybrid:
            # ハイブリッド検索
            import asyncio
            results = asyncio.run(search_service.hybrid_search(
                query=args.query,
                limit=args.limit,
                sparse_weight=args.sparse_weight,
                dense_weight=args.dense_weight
            ))
            
            # 詳細説明が要求された場合
            if args.explain and results:
                print(f"\n📊 検索詳細情報:")
                explain_results = search_service.explain_search(
                    query=args.query,
                    limit=3  # 上位3件のみ説明
                )
                
                # 説明結果を整形して表示
                print(f"クエリ処理:")
                print(f"  元クエリ: {explain_results['original_query']}")
                print(f"  正規化: {explain_results['query_processing']['normalized']}")
                print(f"  キーワード: {explain_results['query_processing']['keywords']}")
                print(f"  推奨クエリ: {explain_results['query_processing']['recommended']}")
                print(f"検索重み:")
                print(f"  スパース: {explain_results['search_weights']['sparse_weight']}")
                print(f"  密ベクトル: {explain_results['search_weights']['dense_weight']}")
                print(f"結果詳細:")
                for i, result_detail in enumerate(explain_results['results'][:3], 1):
                    print(f"  {i}. {result_detail['title']}")
                    print(f"     最終スコア: {result_detail['hybrid_score']:.3f}")
                    print(f"     スパース: {result_detail['sparse_score']:.3f}")
                    print(f"     密ベクトル: {result_detail['dense_score']:.3f}")
                    print(f"     検索タイプ: {result_detail['search_type']}")
                
                # 結果分布も表示
                distribution = explain_results['result_distribution']
                print(f"検索タイプ分布:")
                print(f"  スパース専用: {distribution['sparse_only']}件")
                print(f"  密ベクトル専用: {distribution['dense_only']}件")  
                print(f"  ハイブリッド: {distribution['hybrid']}件")
                print()
        else:
            # 従来のセマンティック検索
            results = search_service.semantic_search(args.query, limit=args.limit)
        
        if results:
            print(f"✅ {len(results)}件の検索結果:")
            for i, result in enumerate(results, 1):
                if args.hybrid:
                    # ハイブリッド検索結果の表示
                    print(f"\n{i}. 記事{result.article_id}: {result.title}")
                    print(f"   ハイブリッドスコア: {result.hybrid_score:.4f}")
                    print(f"   スパースBM25: {result.sparse_score:.4f}")
                    print(f"   密ベクトル: {result.dense_score:.4f}")
                    print(f"   検索タイプ: {result.search_type}")
                    
                    # テキスト内容の一部表示
                    if result.content:
                        content_preview = result.content[:150] + "..." if len(result.content) > 150 else result.content
                        print(f"   内容: {content_preview}")
                        print(f"   テキスト長: {len(result.content)}文字")
                    
                    # 特定記事がヒットしたかチェック
                    if find_article_num and result.article_id == find_article_num:
                        print(f"   🎯 探していた記事{find_article_num}が検索結果に含まれました！")
                else:
                    # 従来のセマンティック検索結果の表示
                    print(f"\n{i}. 記事{result.article.number}: {result.article.name}")
                    print(f"   スコア: {result.score:.4f}")
                    print(f"   カテゴリ: {result.article.category or '未分類'}")
                    print(f"   更新日: {result.article.updated_at}")
                    print(f"   URL: {result.article.url}")
                    if result.matched_text:
                        print(f"   マッチ: {result.matched_text[:150]}...")
                    
                    # テキスト内容の確認
                    content_length = len(result.article.processed_text or result.article.body_md or '')
                    print(f"   テキスト長: {content_length}文字")
                    
                    # 特定記事がヒットしたかチェック
                    if find_article_num and result.article.number == find_article_num:
                        print(f"   🎯 探していた記事{find_article_num}が検索結果に含まれました！")
        else:
            print("❌ 検索結果が見つかりませんでした")
            
            # デバッグ情報を表示
            print("\n🔍 デバッグ情報:")
            try:
                if args.hybrid:
                    collection = search_service.search_service.collection
                else:
                    collection = search_service.collection
                    
                total_count = collection.count()
                print(f"   ベクトルDB内記事数: {total_count}件")
                
                if total_count == 0:
                    print("   ⚠️ ベクトルDBが空です。ベクトル化を実行してください。")
                else:
                    # サンプル検索で動作確認
                    if args.hybrid:
                        import asyncio
                        sample_results = asyncio.run(search_service.hybrid_search("研究", limit=3))
                    else:
                        sample_results = search_service.semantic_search("研究", limit=3)
                    print(f"   サンプル検索('研究'): {len(sample_results)}件")
                    
            except Exception as debug_error:
                print(f"   ❌ デバッグ情報取得エラー: {debug_error}")
            
    except Exception as e:
        print(f"❌ 検索エラー: {e}")
        import traceback
        print(f"   詳細: {traceback.format_exc()}")
        sys.exit(1)


def serve_app(args):
    """Webアプリ起動"""
    print(f"🚀 Webアプリをポート{args.port}で起動中...")
    
    try:
        import subprocess
        import os
        
        # APIサーバー起動
        api_cmd = [
            sys.executable, "-m", "uvicorn",
            "src.api.main:app",
            "--host", "0.0.0.0",
            "--port", str(args.port),
            "--reload"
        ]
        
        print(f"📡 APIサーバーを起動: http://localhost:{args.port}")
        
        if args.frontend:
            # 環境変数でAPIポートをフロントエンドに伝達
            frontend_env = os.environ.copy()
            frontend_env["API_PORT"] = str(args.port)
            
            # フロントエンド起動（別プロセス）
            frontend_cmd = [
                sys.executable, "-m", "streamlit", "run",
                "src/frontend/app.py",
                "--server.port", str(args.port + 1),
                "--server.address", "0.0.0.0",  # 外部アクセス許可
                "--server.headless", "true",
                "--browser.gatherUsageStats", "false"
            ]
            
            print(f"🖥️ フロントエンドを起動: http://0.0.0.0:{args.port + 1}")
            print(f"   API接続先: http://localhost:{args.port}")
            
            # フロントエンドを別プロセスで起動（環境変数を渡す）
            frontend_process = subprocess.Popen(frontend_cmd, env=frontend_env)
            
            # APIサーバーをメインプロセスで起動（ブロッキング）
            try:
                subprocess.run(api_cmd)
            finally:
                # 終了時にフロントエンドプロセスも終了
                frontend_process.terminate()
                frontend_process.wait()
        else:
            subprocess.run(api_cmd)
            
    except Exception as e:
        print(f"❌ Webアプリ起動エラー: {e}")
        sys.exit(1)


def full_process(args):
    """全体処理（強化オプション対応）"""
    enhanced_mode = getattr(args, 'enhanced', False)
    skip_export = getattr(args, 'skip_export', False)
    
    if enhanced_mode:
        print("🔄 全体処理を開始（強化モード）...")
        print("   ✨ 強化ベクトル化を含む完全処理")
    else:
        print("🔄 全体処理を開始...")
    
    if not skip_export:
        print("\n=== ステップ1: データエクスポート ===")
        export_data(args)
    else:
        print("\n=== ステップ1: データエクスポート（スキップ） ===")
    
    print("\n=== ステップ2: ベクトル化 ===")
    if enhanced_mode:
        print("🎯 強化ベクトル化モードで実行")
    vectorize_articles(args)
    
    print("\n=== ステップ3: データ確認 ===")
    check_data(args)
    
    if enhanced_mode:
        print("\n🎉 全体処理が完了しました（強化モード）！")
        print("   ✨ 高精度ベクトル化による検索品質向上を実現")
    else:
        print("\n🎉 全体処理が完了しました！")


def main():
    """メイン処理"""
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # 設定確認
    if args.command in ['export', 'full'] and not getattr(args, 'skip_export', False):
        if not settings.esa_api_token or not settings.esa_team_name:
            print("❌ ESA_API_TOKEN と ESA_TEAM_NAME を .env ファイルに設定してください")
            sys.exit(1)
    
    print(f"=== 研究室RAGシステム - {args.command} ===")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # コマンド実行
    command_functions = {
        'export': export_data,
        'vectorize': vectorize_articles,
        'check': check_data,
        'search': search_articles,
        'serve': serve_app,
        'full': full_process
    }
    
    if args.command in command_functions:
        command_functions[args.command](args)
    else:
        print(f"❌ 不明なコマンド: {args.command}")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
