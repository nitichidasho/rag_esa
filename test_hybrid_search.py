#!/usr/bin/env python3
"""
ハイブリッド検索システムのテストと評価
"""

import sys
import asyncio
from pathlib import Path

# プロジェクトルートをsys.pathに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.services.hybrid_search_service import HybridSearchService


async def test_hybrid_search():
    """ハイブリッド検索の基本テスト"""
    print("🔍 ハイブリッド検索システムのテスト開始\n")
    
    hybrid_service = HybridSearchService()
    
    # テストクエリ
    test_queries = [
        "Ubuntuのインストール方法を教えてください",
        "Python 機械学習",
        "ROS エラー 解決",
        "ラズパイ セットアップ",
        "Docker コンテナ 設定"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"=== テストケース {i}: {query} ===")
        
        try:
            # ハイブリッド検索実行
            results = await hybrid_service.hybrid_search(query, limit=5)
            
            print(f"検索結果: {len(results)}件")
            for j, result in enumerate(results[:3], 1):
                print(f"  {j}. {result.title}")
                print(f"     ハイブリッドスコア: {result.hybrid_score:.3f}")
                print(f"     Sparse: {result.sparse_score:.3f}, Dense: {result.dense_score:.3f}")
                print(f"     検索タイプ: {result.search_type}")
                print()
            
        except Exception as e:
            print(f"❌ エラー: {e}")
        
        print("-" * 50)


async def compare_search_methods():
    """検索手法の比較評価"""
    print("\n🆚 検索手法比較テスト\n")
    
    hybrid_service = HybridSearchService()
    test_query = "Ubuntuのインストール方法を教えてください"
    
    print(f"テストクエリ: {test_query}\n")
    
    try:
        # 各検索手法で実行
        print("1️⃣ ハイブリッド検索（Sparse + Dense）")
        hybrid_results = await hybrid_service.hybrid_search(
            test_query, limit=5, sparse_weight=0.6, dense_weight=0.4
        )
        
        print("2️⃣ Sparse検索のみ（BM25ベース）")
        sparse_results = await hybrid_service.hybrid_search(
            test_query, limit=5, sparse_weight=1.0, dense_weight=0.0
        )
        
        print("3️⃣ Dense検索のみ（Vector類似度）")
        dense_results = await hybrid_service.hybrid_search(
            test_query, limit=5, sparse_weight=0.0, dense_weight=1.0
        )
        
        # 結果比較
        print("\n📊 結果比較:")
        print(f"ハイブリッド: {len(hybrid_results)}件")
        print(f"Sparse のみ: {len(sparse_results)}件") 
        print(f"Dense のみ: {len(dense_results)}件")
        
        # トップ3の比較
        print("\n🏆 トップ3記事の比較:")
        
        methods = [
            ("ハイブリッド", hybrid_results),
            ("Sparse", sparse_results), 
            ("Dense", dense_results)
        ]
        
        for method_name, results in methods:
            print(f"\n{method_name}検索 トップ3:")
            for i, result in enumerate(results[:3], 1):
                if method_name == "ハイブリッド":
                    score = result.hybrid_score
                elif method_name == "Sparse":
                    score = result.sparse_score
                else:
                    score = result.dense_score
                
                print(f"  {i}. {result.title} (スコア: {score:.3f})")
        
    except Exception as e:
        print(f"❌ 比較テストエラー: {e}")


def test_query_processing_integration():
    """クエリ処理との統合テスト"""
    print("\n🔧 クエリ処理統合テスト\n")
    
    hybrid_service = HybridSearchService()
    
    test_cases = [
        {
            "query": "Ubuntuのインストール方法を教えてください",
            "expected_keywords": ["Ubuntu", "インストール"]
        },
        {
            "query": "Python で機械学習を始めたい",
            "expected_keywords": ["Python", "機械学習"]
        },
        {
            "query": "ROS のエラーを解決したい",
            "expected_keywords": ["ROS", "エラー"]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"--- テストケース {i} ---")
        print(f"質問: {test_case['query']}")
        
        # クエリ処理の確認
        processed = hybrid_service.query_processor.process_query(test_case['query'])
        print(f"抽出キーワード: {processed['keywords']}")
        print(f"技術用語: {processed['technical_terms']}")
        print(f"推奨クエリ: {processed['recommended_query']}")
        
        # 期待するキーワードが含まれているかチェック
        extracted_keywords = processed['keywords']
        expected_keywords = test_case['expected_keywords']
        
        success = all(
            any(expected.lower() in extracted.lower() for extracted in extracted_keywords)
            for expected in expected_keywords
        )
        
        if success:
            print("✅ キーワード抽出成功")
        else:
            print("⚠️ 期待するキーワードが不足")
        
        print()


async def performance_test():
    """パフォーマンステスト"""
    print("\n⚡ パフォーマンステスト\n")
    
    import time
    
    hybrid_service = HybridSearchService()
    test_query = "Ubuntu インストール"
    
    # 複数回実行して平均時間を測定
    times = []
    runs = 5
    
    for i in range(runs):
        start_time = time.time()
        
        try:
            results = await hybrid_service.hybrid_search(test_query, limit=10)
            end_time = time.time()
            execution_time = end_time - start_time
            times.append(execution_time)
            
            print(f"実行 {i+1}: {execution_time:.3f}秒 ({len(results)}件)")
            
        except Exception as e:
            print(f"実行 {i+1}: エラー - {e}")
    
    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"\n📈 パフォーマンス統計:")
        print(f"平均実行時間: {avg_time:.3f}秒")
        print(f"最短時間: {min_time:.3f}秒") 
        print(f"最長時間: {max_time:.3f}秒")
        print(f"実行成功率: {len(times)}/{runs} ({len(times)/runs*100:.1f}%)")


async def main():
    """メインテスト実行"""
    print("🚀 ハイブリッド検索システム 総合テスト")
    print("=" * 60)
    
    try:
        # 基本機能テスト
        await test_hybrid_search()
        
        # 検索手法比較
        await compare_search_methods()
        
        # クエリ処理統合テスト
        test_query_processing_integration()
        
        # パフォーマンステスト
        await performance_test()
        
        print("\n✅ 全テスト完了")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ テストが中断されました")
    except Exception as e:
        print(f"\n❌ テストエラー: {e}")
        import traceback
        print(f"詳細: {traceback.format_exc()}")


if __name__ == "__main__":
    asyncio.run(main())
