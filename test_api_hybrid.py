#!/usr/bin/env python3
"""
ハイブリッド検索API機能のテスト
"""

import sys
import asyncio
import json
from pathlib import Path

# プロジェクトルートをsys.pathに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.api.routes.search import search_articles, SearchRequest


async def test_hybrid_search_api():
    """ハイブリッド検索APIのテスト"""
    print("🔍 ハイブリッド検索API機能テスト")
    print("=" * 50)
    
    # テストクエリ
    test_queries = [
        {
            "query": "Ubuntuのインストール方法を教えてください",
            "search_type": "hybrid",
            "description": "自然言語質問 + ハイブリッド検索"
        },
        {
            "query": "Ubuntu インストール",
            "search_type": "semantic",
            "description": "キーワード + セマンティック検索"
        },
        {
            "query": "ROS エラー 解決",
            "search_type": "hybrid",
            "sparse_weight": 0.7,
            "dense_weight": 0.3,
            "description": "技術用語 + カスタム重み付きハイブリッド"
        }
    ]
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n=== テストケース {i}: {test_case['description']} ===")
        print(f"クエリ: {test_case['query']}")
        print(f"検索タイプ: {test_case['search_type']}")
        
        # リクエスト作成
        request = SearchRequest(
            query=test_case['query'],
            limit=3,
            search_type=test_case['search_type'],
            sparse_weight=test_case.get('sparse_weight'),
            dense_weight=test_case.get('dense_weight')
        )
        
        try:
            # API呼び出し
            response = await search_articles(request)
            
            print(f"✅ 検索成功: {response['total']}件")
            print(f"検索タイプ: {response.get('search_type', 'N/A')}")
            
            # 結果表示
            for j, result in enumerate(response['results'], 1):
                article = result['article']
                print(f"\n{j}. {article['name']}")
                print(f"   スコア: {result['score']:.3f}")
                
                if test_case['search_type'] == 'hybrid':
                    print(f"   Sparse: {result.get('sparse_score', 'N/A'):.3f} | Dense: {result.get('dense_score', 'N/A'):.3f}")
                    print(f"   検索タイプ: {result.get('search_type', 'N/A')}")
                
                print(f"   マッチ: {result['matched_text'][:100]}...")
        
        except Exception as e:
            print(f"❌ エラー: {e}")
            import traceback
            traceback.print_exc()
        
        print("-" * 40)


async def test_performance_comparison():
    """性能比較テスト"""
    print("\n🆚 検索手法性能比較")
    print("=" * 30)
    
    import time
    
    query = "Ubuntuのインストール方法を教えてください"
    
    # セマンティック検索
    print("1. セマンティック検索")
    start_time = time.time()
    semantic_request = SearchRequest(query=query, search_type="semantic", limit=5)
    semantic_result = await search_articles(semantic_request)
    semantic_time = time.time() - start_time
    
    print(f"   結果: {semantic_result['total']}件")
    print(f"   時間: {semantic_time:.3f}秒")
    
    # ハイブリッド検索
    print("\n2. ハイブリッド検索")
    start_time = time.time()
    hybrid_request = SearchRequest(query=query, search_type="hybrid", limit=5)
    hybrid_result = await search_articles(hybrid_request)
    hybrid_time = time.time() - start_time
    
    print(f"   結果: {hybrid_result['total']}件")
    print(f"   時間: {hybrid_time:.3f}秒")
    
    # 比較
    print(f"\n📊 比較結果:")
    print(f"セマンティック: {semantic_result['total']}件 / {semantic_time:.3f}秒")
    print(f"ハイブリッド: {hybrid_result['total']}件 / {hybrid_time:.3f}秒")
    
    if hybrid_result['total'] >= semantic_result['total']:
        print("✅ ハイブリッド検索の方が多くの結果を取得")
    else:
        print("⚠️ セマンティック検索の方が多くの結果を取得")


async def main():
    """メインテスト"""
    try:
        await test_hybrid_search_api()
        await test_performance_comparison()
        
        print("\n✅ 全APIテスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
