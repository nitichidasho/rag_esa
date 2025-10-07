#!/usr/bin/env python3
"""
ハイブリッド検索API使用サンプル集
実際のAPIを使用した様々なパターンのテスト
"""

import requests
import json
import time
from typing import Dict, List, Optional


class HybridSearchClient:
    """ハイブリッド検索APIクライアント"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.search_endpoint = f"{base_url}/api/search/"
    
    def search(
        self,
        query: str,
        search_type: str = "hybrid",
        limit: int = 5,
        sparse_weight: Optional[float] = None,
        dense_weight: Optional[float] = None,
        timeout: int = 30
    ) -> Optional[Dict]:
        """ハイブリッド検索を実行"""
        
        payload = {
            "query": query,
            "search_type": search_type,
            "limit": limit
        }
        
        if sparse_weight is not None:
            payload["sparse_weight"] = sparse_weight
        if dense_weight is not None:
            payload["dense_weight"] = dense_weight
        
        try:
            response = requests.post(
                self.search_endpoint,
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"API呼び出しエラー: {e}")
            return None
    
    def compare_search_types(self, query: str) -> Dict:
        """セマンティック検索とハイブリッド検索を比較"""
        
        results = {}
        
        # セマンティック検索
        semantic_result = self.search(query, search_type="semantic")
        results["semantic"] = semantic_result
        
        # ハイブリッド検索
        hybrid_result = self.search(query, search_type="hybrid")
        results["hybrid"] = hybrid_result
        
        return results
    
    def test_weight_optimization(self, query: str) -> List[Dict]:
        """異なる重み設定でのテスト"""
        
        weight_configs = [
            {"name": "キーワード重視", "sparse": 0.8, "dense": 0.2},
            {"name": "バランス型", "sparse": 0.6, "dense": 0.4},
            {"name": "意味重視", "sparse": 0.4, "dense": 0.6},
            {"name": "極端意味重視", "sparse": 0.2, "dense": 0.8},
        ]
        
        results = []
        for config in weight_configs:
            result = self.search(
                query,
                sparse_weight=config["sparse"],
                dense_weight=config["dense"]
            )
            if result:
                results.append({
                    "config": config,
                    "result": result
                })
        
        return results


def demo_basic_usage():
    """基本的な使用例"""
    print("🔍 基本的なハイブリッド検索デモ")
    print("=" * 50)
    
    client = HybridSearchClient()
    
    # 自然言語質問
    query = "Ubuntuのインストール方法を教えてください"
    print(f"質問: {query}")
    
    result = client.search(query)
    if result:
        print(f"✅ 検索成功: {result['total']}件")
        for i, article in enumerate(result['results'][:3], 1):
            print(f"{i}. {article['article']['name']}")
            print(f"   スコア: {article['score']:.3f}")
            if 'search_type' in article:
                print(f"   タイプ: {article['search_type']}")
        print()
    else:
        print("❌ 検索失敗\n")


def demo_weight_comparison():
    """重み設定比較デモ"""
    print("⚖️ 重み設定比較デモ")
    print("=" * 30)
    
    client = HybridSearchClient()
    query = "ROSでエラーが発生した時の対処法"
    
    print(f"質問: {query}\n")
    
    weight_tests = client.test_weight_optimization(query)
    
    for test in weight_tests:
        config = test["config"]
        result = test["result"]
        
        print(f"📊 {config['name']} (Sparse:{config['sparse']}, Dense:{config['dense']})")
        print(f"   結果数: {result['total']}件")
        
        if result['results']:
            top_article = result['results'][0]
            print(f"   トップ: {top_article['article']['name']}")
            print(f"   スコア: {top_article['score']:.3f}")
        print()


def demo_search_type_comparison():
    """検索タイプ比較デモ"""
    print("🆚 検索タイプ比較デモ")
    print("=" * 25)
    
    client = HybridSearchClient()
    query = "初心者向けのプログラミング学習方法"
    
    print(f"質問: {query}\n")
    
    comparison = client.compare_search_types(query)
    
    for search_type, result in comparison.items():
        if result:
            print(f"📈 {search_type.upper()}検索")
            print(f"   結果数: {result['total']}件")
            
            for i, article in enumerate(result['results'][:2], 1):
                print(f"   {i}. {article['article']['name']}")
                print(f"      スコア: {article['score']:.3f}")
            print()
        else:
            print(f"❌ {search_type}検索失敗\n")


def demo_performance_test():
    """性能測定デモ"""
    print("⚡ 性能測定デモ")
    print("=" * 20)
    
    client = HybridSearchClient()
    queries = [
        "Ubuntu インストール",
        "Python 機械学習",
        "ROS エラー 解決"
    ]
    
    for query in queries:
        print(f"クエリ: {query}")
        
        # 実行時間測定
        start_time = time.time()
        result = client.search(query)
        end_time = time.time()
        
        if result:
            print(f"✅ 結果: {result['total']}件")
            print(f"⏱️ 実行時間: {end_time - start_time:.3f}秒")
        else:
            print("❌ 検索失敗")
        print()


def demo_error_handling():
    """エラーハンドリングデモ"""
    print("🚨 エラーハンドリングデモ")
    print("=" * 25)
    
    # 無効なURL（サーバーが起動していない場合）
    client = HybridSearchClient(base_url="http://localhost:9999")
    
    print("無効なサーバーURLでのテスト...")
    result = client.search("テストクエリ")
    
    if result is None:
        print("✅ エラーハンドリング成功: 無効なURLの場合")
    else:
        print("⚠️ 予期しない成功")
    
    # 正常なクライアントでの空クエリテスト
    normal_client = HybridSearchClient()
    
    print("\n空クエリでのテスト...")
    result = normal_client.search("")
    
    if result:
        print(f"結果: {result['total']}件（空クエリでも動作）")
    else:
        print("空クエリではエラーが発生")


def main():
    """メインデモ実行"""
    print("🚀 ハイブリッド検索API使用サンプル")
    print("=" * 60)
    print()
    
    try:
        demo_basic_usage()
        demo_weight_comparison()
        demo_search_type_comparison()
        demo_performance_test()
        demo_error_handling()
        
        print("✅ 全デモ完了")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ デモが中断されました")
    except Exception as e:
        print(f"\n❌ デモエラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
