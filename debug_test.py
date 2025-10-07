#!/usr/bin/env python3
"""
ハイブリッド検索の詳細分析テスト
"""

import sys
import asyncio
from pathlib import Path

# プロジェクトルートをsys.pathに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.services.hybrid_search_service import HybridSearchService


async def detailed_analysis():
    """詳細分析テスト"""
    print("🔬 ハイブリッド検索の詳細分析")
    print("=" * 50)
    
    hybrid_service = HybridSearchService()
    
    # テストクエリ
    queries = [
        "Ubuntuのインストール方法を教えてください",  # 自然言語
        "Ubuntu インストール",                      # キーワード
        "ROS エラー"                               # 技術用語
    ]
    
    for query in queries:
        print(f"\n🔍 クエリ: {query}")
        print("-" * 30)
        
        # 各検索手法を個別に実行
        print("1. Sparse検索のみ（BM25重視）")
        sparse_only = await hybrid_service.hybrid_search(
            query, limit=3, sparse_weight=1.0, dense_weight=0.0
        )
        
        print("2. Dense検索のみ（Vector重視）") 
        dense_only = await hybrid_service.hybrid_search(
            query, limit=3, sparse_weight=0.0, dense_weight=1.0
        )
        
        print("3. ハイブリッド検索（Sparse 60% + Dense 40%）")
        hybrid_balanced = await hybrid_service.hybrid_search(
            query, limit=3, sparse_weight=0.6, dense_weight=0.4
        )
        
        # 結果比較
        print(f"\n📊 結果比較:")
        print(f"Sparse のみ: {len(sparse_only)}件")
        print(f"Dense のみ: {len(dense_only)}件")
        print(f"ハイブリッド: {len(hybrid_balanced)}件")
        
        print(f"\n🏆 トップ記事:")
        if sparse_only:
            print(f"Sparse: {sparse_only[0].title} (スコア: {sparse_only[0].hybrid_score:.3f})")
        if dense_only:
            print(f"Dense: {dense_only[0].title} (スコア: {dense_only[0].hybrid_score:.3f})")
        if hybrid_balanced:
            print(f"Hybrid: {hybrid_balanced[0].title} (スコア: {hybrid_balanced[0].hybrid_score:.3f})")
        
        print("\n" + "="*50)


async def vector_search_debug():
    """Vector検索のデバッグ"""
    print("\n🐛 Vector検索デバッグ")
    print("=" * 30)
    
    hybrid_service = HybridSearchService()
    
    # Dense検索を直接テスト
    query = "Ubuntu インストール"
    print(f"テストクエリ: {query}")
    
    try:
        # 内部のDense検索メソッドを直接呼び出し
        dense_results = await hybrid_service._dense_search(query, limit=5)
        
        print(f"✅ Dense検索結果: {len(dense_results)}件")
        for i, result in enumerate(dense_results[:3], 1):
            print(f"{i}. {result.article.name}")
            print(f"   スコア: {result.score:.3f}")
            print(f"   マッチテキスト: {result.matched_text}")
        
    except Exception as e:
        print(f"❌ Dense検索エラー: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """メインテスト"""
    try:
        await detailed_analysis()
        await vector_search_debug()
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
