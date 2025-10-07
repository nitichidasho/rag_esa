#!/usr/bin/env python3
"""
Ubuntu検索問題の詳細調査スクリプト
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from src.services.search_service import SearchService
from src.services.embedding_service import EmbeddingService
import chromadb
import numpy as np
from loguru import logger

def analyze_ubuntu_search():
    """Ubuntu検索の問題を詳細分析"""
    
    print("=== Ubuntu検索問題の調査開始 ===\n")
    
    # 1. 検索サービス初期化
    try:
        search_service = SearchService()
        print("✅ 検索サービス初期化成功")
    except Exception as e:
        print(f"❌ 検索サービス初期化失敗: {e}")
        return
    
    # 2. データベース統計
    try:
        collection = search_service.collection
        count = collection.count()
        print(f"📊 総記事数: {count}")
        
        # 全記事のタイトルを確認
        all_results = collection.get(include=["metadatas"])
        titles = [meta.get('name', '') for meta in all_results['metadatas']]
        
        # Ubuntu関連記事の存在チェック
        ubuntu_titles = [title for title in titles if 'ubuntu' in title.lower()]
        linux_titles = [title for title in titles if 'linux' in title.lower()]
        container_titles = [title for title in titles if 'コンテナ' in title.lower()]
        
        print(f"🔍 'Ubuntu'を含むタイトル: {len(ubuntu_titles)}")
        for title in ubuntu_titles[:5]:
            print(f"   - {title}")
        
        print(f"🔍 'Linux'を含むタイトル: {len(linux_titles)}")
        for title in linux_titles[:5]:
            print(f"   - {title}")
            
        print(f"🔍 'コンテナ'を含むタイトル: {len(container_titles)}")
        for title in container_titles[:3]:
            print(f"   - {title}")
            
    except Exception as e:
        print(f"❌ データベース統計取得失敗: {e}")
        return
    
    # 3. 埋め込みベクトルのテスト
    print(f"\n=== 埋め込みベクトルテスト ===")
    embedding_service = EmbeddingService()
    
    test_queries = [
        "Ubuntu",
        "Ubuntuのインストール方法",
        "Linux",
        "OS インストール",
        "システム セットアップ"
    ]
    
    query_embeddings = {}
    for query in test_queries:
        try:
            embedding = embedding_service.generate_embedding(query)
            query_embeddings[query] = embedding
            print(f"✅ '{query}' 埋め込み成功 (次元: {len(embedding)})")
        except Exception as e:
            print(f"❌ '{query}' 埋め込み失敗: {e}")
    
    # 4. 実際の検索結果詳細分析
    print(f"\n=== Ubuntu検索結果詳細分析 ===")
    
    try:
        # デバッグモードで検索実行
        results = search_service.semantic_search("Ubuntu", limit=10, debug_mode=True)
        
        print(f"検索結果数: {len(results)}")
        
        if results:
            print("\n📋 検索結果詳細:")
            for i, result in enumerate(results):
                print(f"\n{i+1}. 記事 {result.article.number}: {result.article.name}")
                print(f"   スコア: {result.score:.6f}")
                print(f"   カテゴリ: {result.article.category}")
                print(f"   タグ: {', '.join(result.article.tags) if result.article.tags else 'なし'}")
                print(f"   マッチテキスト: {result.matched_text[:150]}...")
                
                # 本文にUbuntuが含まれているかチェック
                ubuntu_in_content = 'ubuntu' in result.article.body_md.lower()
                linux_in_content = 'linux' in result.article.body_md.lower()
                print(f"   内容に'Ubuntu'含む: {ubuntu_in_content}")
                print(f"   内容に'Linux'含む: {linux_in_content}")
        else:
            print("❌ 検索結果がありません")
            
    except Exception as e:
        print(f"❌ 検索実行失敗: {e}")
    
    # 5. 直接ChromaDB検索で比較
    print(f"\n=== 直接ChromaDB検索比較 ===")
    
    try:
        query_embedding = embedding_service.generate_embedding("Ubuntu")
        direct_results = collection.query(
            query_embeddings=[query_embedding],
            n_results=10,
            include=["metadatas", "documents", "distances"]
        )
        
        print(f"直接検索結果数: {len(direct_results['ids'][0])}")
        
        for i in range(min(5, len(direct_results['ids'][0]))):
            article_id = direct_results['ids'][0][i]
            distance = direct_results['distances'][0][i]
            similarity = 1.0 - distance
            title = direct_results['metadatas'][0][i].get('name', '')
            
            print(f"{i+1}. 記事{article_id}: {title}")
            print(f"   距離: {distance:.6f}, 類似度: {similarity:.6f}")
            
            # 内容チェック
            document = direct_results['documents'][0][i]
            ubuntu_count = document.lower().count('ubuntu')
            linux_count = document.lower().count('linux')
            print(f"   'Ubuntu'出現回数: {ubuntu_count}, 'Linux'出現回数: {linux_count}")
            
    except Exception as e:
        print(f"❌ 直接検索失敗: {e}")
    
    # 6. 閾値テスト
    print(f"\n=== 類似度閾値テスト ===")
    
    thresholds = [0.1, 0.2, 0.3, 0.4, 0.5]
    for threshold in thresholds:
        try:
            # 一時的に閾値を変更してテスト
            results = search_service.semantic_search("Ubuntu", limit=5)
            filtered_count = sum(1 for r in results if (1.0 - 0) >= threshold)  # 仮の計算
            print(f"閾値 {threshold}: 結果数 {len(results)}")
        except Exception as e:
            print(f"閾値 {threshold} テスト失敗: {e}")

if __name__ == "__main__":
    analyze_ubuntu_search()
