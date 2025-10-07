#!/usr/bin/env python3
"""
検索問題デバッグスクリプト
"""

import sys
from pathlib import Path

# プロジェクトルートを sys.path に追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.search_service import SearchService
from src.services.embedding_service import EmbeddingService
from src.database.repositories.article_repository import ArticleRepository
from src.database.connection import SessionLocal
import numpy as np


def debug_article_818():
    """記事818の詳細デバッグ"""
    print("🔍 記事818の詳細調査を開始...")
    
    # サービス初期化
    search_service = SearchService()
    embedding_service = EmbeddingService()
    
    # データベースから記事818を取得
    db_session = SessionLocal()
    try:
        article_repo = ArticleRepository(db=db_session)
        article_818 = article_repo.get_by_number(818)
        
        if not article_818:
            print("❌ 記事818がデータベースに見つかりません")
            return
        
        print(f"📄 記事818の詳細:")
        print(f"   タイトル: {article_818.name}")
        print(f"   カテゴリ: {article_818.category}")
        print(f"   本文: {article_818.processed_text[:200]}...")
        print(f"   ベクトル長: {len(article_818.embedding) if article_818.embedding else 0}")
        print()
        
        # ChromaDBから記事818を直接取得
        print("🔍 ChromaDBから記事818を確認:")
        collection = search_service.collection
        chroma_result = collection.get(
            ids=["818"],
            include=["metadatas", "documents", "embeddings"]
        )
        
        if chroma_result["ids"]:
            print("✅ ChromaDBに存在:")
            metadata = chroma_result["metadatas"][0]
            document = chroma_result["documents"][0]
            embedding = chroma_result["embeddings"][0]
            
            print(f"   メタデータ: {metadata}")
            print(f"   ドキュメント: {document[:100]}...")
            print(f"   埋め込みベクトル長: {len(embedding)}")
            print()
            
            # 「筋電」クエリのベクトルと記事818のベクトルの類似度を直接計算
            print("🔍 類似度の直接計算:")
            query_embedding = embedding_service.generate_embedding("筋電")
            article_embedding = embedding
            
            # コサイン類似度を計算
            query_vec = np.array(query_embedding)
            article_vec = np.array(article_embedding)
            
            dot_product = np.dot(query_vec, article_vec)
            norm_query = np.linalg.norm(query_vec)
            norm_article = np.linalg.norm(article_vec)
            
            if norm_query > 0 and norm_article > 0:
                cosine_similarity = dot_product / (norm_query * norm_article)
                distance = 1.0 - cosine_similarity
                score = 1.0 - distance
                
                print(f"   コサイン類似度: {cosine_similarity:.6f}")
                print(f"   距離: {distance:.6f}")
                print(f"   スコア: {score:.6f}")
                print()
                
                # ChromaDBの生クエリで確認
                print("🔍 ChromaDBの生検索結果:")
                raw_results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=20,  # 多めに取得
                    include=["metadatas", "documents", "distances"]
                )
                
                # 記事818がどの位置にあるかチェック
                found_818 = False
                for i, (id_str, metadata, distance) in enumerate(zip(
                    raw_results["ids"][0],
                    raw_results["metadatas"][0],
                    raw_results["distances"][0]
                )):
                    if id_str == "818":
                        found_818 = True
                        print(f"   🎯 記事818発見！ 順位: {i+1}/20")
                        print(f"      距離: {distance:.6f}")
                        print(f"      スコア: {1.0 - distance:.6f}")
                        print(f"      タイトル: {metadata.get('name', '')}")
                        break
                
                if not found_818:
                    print("   ❌ 記事818が上位20件に見つかりませんでした")
                    
                    # 全記事での位置を確認
                    print("   🔍 全記事での位置確認...")
                    all_results = collection.query(
                        query_embeddings=[query_embedding],
                        n_results=1000,  # さらに多く取得
                        include=["metadatas", "documents", "distances"]
                    )
                    
                    for i, id_str in enumerate(all_results["ids"][0]):
                        if id_str == "818":
                            print(f"   🎯 記事818の実際の順位: {i+1}/1000")
                            print(f"      距離: {all_results['distances'][0][i]:.6f}")
                            break
                    else:
                        print("   ❌ 記事818が検索結果に全く含まれていません！")
        else:
            print("❌ ChromaDBに記事818が見つかりません")
            
    finally:
        db_session.close()


def debug_search_algorithm():
    """検索アルゴリズムのデバッグ"""
    print("\n🔍 検索アルゴリズムの詳細調査:")
    
    search_service = SearchService()
    
    # デバッグ用に検索処理を詳細に追跡
    query = "筋電"
    query_embedding = search_service.embedding_service.generate_embedding(query)
    
    # ChromaDBの生の結果を取得
    raw_results = search_service.collection.query(
        query_embeddings=[query_embedding],
        n_results=50,
        include=["metadatas", "documents", "distances"]
    )
    
    print(f"📊 生の検索結果（上位10件）:")
    for i in range(min(10, len(raw_results["ids"][0]))):
        id_str = raw_results["ids"][0][i]
        metadata = raw_results["metadatas"][0][i]
        distance = raw_results["distances"][0][i]
        score = 1.0 - distance
        title = metadata.get("name", "")
        category = metadata.get("category", "")
        
        print(f"  {i+1}. 記事{id_str}: {title}")
        print(f"     カテゴリ: {category}")
        print(f"     距離: {distance:.6f}, スコア: {score:.6f}")
        
        if id_str == "818":
            print(f"     🎯 記事818発見！")
        print()


def main():
    """メイン処理"""
    print("=== 検索問題詳細調査 ===")
    debug_article_818()
    debug_search_algorithm()


if __name__ == "__main__":
    main()
