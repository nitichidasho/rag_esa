#!/usr/bin/env python3
"""
記事818の検索問題をデバッグするスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config.settings import Settings
from src.services.search_service import SearchService
from src.services.embedding_service import EmbeddingService
import chromadb
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_article_818():
    """記事818の検索問題を詳細にデバッグ"""
    
    print("=== 記事818の検索デバッグ開始 ===")
    
    settings = Settings()
    
    # ChromaDBクライアント初期化
    client = chromadb.PersistentClient(path=str(settings.vector_db_path))
    
    # 利用可能なコレクションを確認
    print("利用可能なコレクション:")
    collections = client.list_collections()
    for col in collections:
        print(f"  - {col.name}")
    
    if not collections:
        print("  ✗ コレクションが存在しません")
        return
    
    # 最初のコレクションを使用
    collection = collections[0]
    collection_name = collection.name
    print(f"使用するコレクション: {collection_name}")
    
    # コレクションを取得
    collection = client.get_collection(name=collection_name)
    
    # 記事818がChromatDBに存在するか確認
    print("\n1. ChromaDBでの記事818の存在確認:")
    try:
        result = collection.get(ids=["818"])
        if result['ids']:
            print(f"   ✓ 記事818はChromatDBに存在します")
            metadata = result['metadatas'][0]
            document = result['documents'][0]
            print(f"   タイトル: {metadata['name']}")
            print(f"   カテゴリ: {metadata['category']}")
            print(f"   テキスト長: {len(document)}")
            print(f"   テキスト内容: {document[:200]}...")
            
            # 記事817と比較
            result_817 = collection.get(ids=["817"])
            if result_817['ids']:
                metadata_817 = result_817['metadatas'][0]
                document_817 = result_817['documents'][0]
                print(f"\n   比較用記事817:")
                print(f"   タイトル: {metadata_817['name']}")
                print(f"   テキスト長: {len(document_817)}")
                print(f"   テキスト内容: {document_817[:200]}...")
        else:
            print("   ✗ 記事818はChromatDBに存在しません")
            return
    except Exception as e:
        print(f"   エラー: {e}")
        return
    
    # EmbeddingServiceとSearchServiceを初期化
    search_service = SearchService()
    
    # "筋電"クエリで類似度検索（デバッグモード）
    print("\n2. '筋電'クエリでのセマンティック検索（デバッグモード）:")
    try:
        results = search_service.semantic_search("筋電", limit=20, debug_mode=True)
        
        print(f"\n   検索結果数: {len(results)}")
        article_818_found = False
        
        for i, result in enumerate(results):
            print(f"   {i+1}. 記事{result.article.number}: {result.article.name} (スコア: {result.score:.6f})")
            if result.article.number == 818:
                article_818_found = True
                print("      ★ 記事818が見つかりました！")
        
        if not article_818_found:
            print("   ✗ 記事818は検索結果に含まれていません")
    except Exception as e:
        print(f"   エラー: {e}")
    
    # 直接ChromaDBクエリで確認
    print("\n3. 直接ChromaDBクエリでの類似度確認:")
    try:
        query_embedding = search_service.embedding_service.generate_embedding("筋電")
        chroma_results = collection.query(
            query_embeddings=[query_embedding],
            n_results=100,  # さらに多くの結果を取得
            include=["metadatas", "documents", "distances"]
        )
        
        print(f"   ChromaDB検索結果数: {len(chroma_results['ids'][0])}")
        
        # 記事818の順位を探す
        for i, article_id in enumerate(chroma_results['ids'][0]):
            if article_id == "818":
                distance = chroma_results['distances'][0][i]
                similarity = 1.0 - distance
                title = chroma_results['metadatas'][0][i]['name']
                print(f"   記事818の順位: {i+1}/{len(chroma_results['ids'][0])}")
                print(f"   類似度スコア: {similarity:.6f}")
                print(f"   距離: {distance:.6f}")
                print(f"   タイトル: {title}")
                break
        else:
            print("   ✗ 記事818は上位100位にも含まれていません")
            
            # 記事818のベクトルを直接取得して類似度計算
            print("\n   直接ベクトル類似度計算:")
            result_818 = collection.get(ids=["818"], include=["embeddings"])
            if result_818['embeddings'] and result_818['embeddings'][0]:
                import numpy as np
                
                # コサイン類似度を計算
                vec_818 = np.array(result_818['embeddings'][0])
                vec_query = np.array(query_embedding)
                
                # ベクトルの正規化
                vec_818_norm = vec_818 / np.linalg.norm(vec_818)
                vec_query_norm = vec_query / np.linalg.norm(vec_query)
                
                # コサイン類似度
                cosine_similarity = np.dot(vec_818_norm, vec_query_norm)
                print(f"   記事818とクエリのコサイン類似度: {cosine_similarity:.6f}")
                print(f"   ChromaDB距離換算: {1.0 - cosine_similarity:.6f}")
            else:
                print("   記事818の埋め込みベクトルが取得できませんでした")
            
    except Exception as e:
        print(f"   エラー: {e}")
    
    # タイトルに「筋電」を含む記事を検索
    print("\n4. タイトルに'筋電'を含む記事の検索:")
    try:
        all_results = collection.get(
            include=["metadatas"]
        )
        
        kindenki_articles = []
        for i, metadata in enumerate(all_results['metadatas']):
            if '筋電' in metadata['name']:
                article_id = all_results['ids'][i]
                kindenki_articles.append((article_id, metadata['name']))
        
        print(f"   '筋電'を含む記事数: {len(kindenki_articles)}")
        for article_id, title in kindenki_articles:
            print(f"   記事{article_id}: {title}")
    except Exception as e:
        print(f"   エラー: {e}")
    
    print("\n=== デバッグ終了 ===")

if __name__ == "__main__":
    debug_article_818()
