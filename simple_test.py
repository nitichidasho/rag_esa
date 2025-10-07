#!/usr/bin/env python3
"""
ハイブリッド検索の簡単なテスト
"""

import sys
import asyncio
from pathlib import Path

# プロジェクトルートをsys.pathに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from src.services.hybrid_search_service import HybridSearchService
    print("✅ HybridSearchService のインポート成功")
except Exception as e:
    print(f"❌ インポートエラー: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


async def simple_test():
    """シンプルなテスト"""
    print("🔍 ハイブリッド検索の基本テスト開始")
    
    try:
        print("Step 1: HybridSearchService初期化中...")
        hybrid_service = HybridSearchService()
        print("✅ HybridSearchService の初期化成功")
        
        # 簡単なクエリでテスト
        query = "Ubuntu インストール"
        print(f"Step 2: テストクエリ実行: {query}")
        
        results = await hybrid_service.hybrid_search(query, limit=3)
        print(f"✅ 検索成功: {len(results)}件の結果")
        
        print("Step 3: 結果表示:")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result.title}")
            print(f"   ハイブリッドスコア: {result.hybrid_score:.3f}")
            print(f"   Sparse: {result.sparse_score:.3f} | Dense: {result.dense_score:.3f}")
            print(f"   検索タイプ: {result.search_type}")
            print()
        
        print("✅ 全テスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(simple_test())
