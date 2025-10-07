#!/usr/bin/env python3
"""
クエリ前処理機能のテストと検証
"""

import sys
from pathlib import Path

# プロジェクトルートをsys.pathに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.query_processor import QueryProcessor
from src.services.search_service import SearchService
from src.services.langchain_qa_service import LangChainQAService

def test_query_processing():
    """クエリ前処理機能のテスト"""
    print("=== クエリ前処理機能テスト ===\n")
    
    # テストケース
    test_queries = [
        "Ubuntuのインストール方法を教えてください",
        "Pythonでの機械学習の実装について知りたいです",
        "ROSの環境構築はどうやりますか",
        "Docker を使った開発環境の設定手順",
        "ラズパイでAIアプリケーションを動かす方法",
        "深層学習モデルの学習方法について教えて",
        "GPUを使った並列処理の実装方法"
    ]
    
    processor = QueryProcessor()
    
    for i, query in enumerate(test_queries, 1):
        print(f"--- テストケース {i} ---")
        print(f"元の質問: {query}")
        
        # クエリ処理実行
        result = processor.process_query(query)
        
        print(f"正規化クエリ: {result['normalized_query']}")
        print(f"抽出キーワード: {result['keywords']}")
        print(f"技術用語: {result['technical_terms']}")
        print(f"展開キーワード: {result['expanded_keywords']}")
        print(f"検索クエリ候補: {result['search_queries']}")
        print(f"推奨クエリ: {result['recommended_query']}")
        print()

def compare_search_results():
    """検索結果の比較テスト"""
    print("=== 検索結果比較テスト ===\n")
    
    # 問題のあったクエリで検証
    test_query = "Ubuntuのインストール方法を教えてください"
    
    processor = QueryProcessor()
    search_service = SearchService()
    
    # クエリ前処理
    query_result = processor.process_query(test_query)
    optimized_query = query_result['recommended_query']
    
    print(f"元の質問: {test_query}")
    print(f"最適化クエリ: {optimized_query}")
    print()
    
    # 元のクエリで検索
    print("--- 元の質問での検索結果 ---")
    original_results = search_service.semantic_search(test_query, limit=5, debug_mode=True)
    print(f"結果件数: {len(original_results)}")
    for i, result in enumerate(original_results[:3], 1):
        print(f"  {i}. {result.article.name} (スコア: {result.score:.3f})")
    print()
    
    # 最適化クエリで検索
    print("--- 最適化クエリでの検索結果 ---")
    optimized_results = search_service.semantic_search(optimized_query, limit=5, debug_mode=True)
    print(f"結果件数: {len(optimized_results)}")
    for i, result in enumerate(optimized_results[:3], 1):
        print(f"  {i}. {result.article.name} (スコア: {result.score:.3f})")
    print()
    
    # 品質比較
    print("--- 品質比較 ---")
    original_high_quality = len([r for r in original_results if r.score >= 1.5])
    optimized_high_quality = len([r for r in optimized_results if r.score >= 1.5])
    
    print(f"元のクエリ - 高品質結果: {original_high_quality}件")
    print(f"最適化クエリ - 高品質結果: {optimized_high_quality}件")
    
    if optimized_high_quality > original_high_quality:
        print("✅ 最適化により検索品質が向上しました")
    elif optimized_high_quality == original_high_quality:
        print("➡️ 検索品質は同等です")
    else:
        print("⚠️ 最適化による品質改善が見られませんでした")

def test_enhanced_qa_service():
    """強化されたQAサービスのテスト"""
    print("\n=== 強化QAサービステスト ===\n")
    
    test_questions = [
        "Ubuntuのインストール方法を教えてください",
        "ROSの開発環境について知りたいです"
    ]
    
    try:
        qa_service = LangChainQAService()
        
        for question in test_questions:
            print(f"質問: {question}")
            print("回答生成中...")
            
            result = qa_service.answer_question(question)
            
            print(f"信頼度: {result.confidence:.1%}")
            print(f"参考記事数: {len(result.source_articles)}")
            print(f"回答: {result.answer[:200]}...")
            print("-" * 50)
            
    except Exception as e:
        print(f"❌ QAサービステストエラー: {e}")
        print("   モデルの読み込みや依存関係を確認してください")

if __name__ == "__main__":
    print("🔍 クエリ前処理機能の検証開始\n")
    
    try:
        # 1. クエリ前処理のテスト
        test_query_processing()
        
        # 2. 検索結果の比較
        compare_search_results()
        
        # 3. 強化QAサービステスト（オプション）
        print("\nQAサービステストを実行しますか？ (時間がかかる可能性があります)")
        response = input("y/N: ").lower()
        if response == 'y':
            test_enhanced_qa_service()
        
        print("\n✅ 全テスト完了")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ テストが中断されました")
    except Exception as e:
        print(f"\n❌ テストエラー: {e}")
        import traceback
        print(f"詳細: {traceback.format_exc()}")
