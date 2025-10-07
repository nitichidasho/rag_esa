#!/usr/bin/env python3
"""
記事検索 vs QA検索の比較調査スクリプト
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

def compare_search_results():
    """記事検索とQA検索の結果を比較"""
    
    print("=== 記事検索 vs QA検索の比較調査 ===\n")
    
    try:
        from src.services.search_service import SearchService
        from src.services.langchain_qa_service import LangChainQAService
        
        search_service = SearchService()
        qa_service = LangChainQAService()
        
        query = "Ubuntu インストール"
        
        print(f"🔍 検索クエリ: '{query}'\n")
        
        # 1. 通常の記事検索
        print("=== 1. 通常の記事検索 ===")
        normal_results = search_service.semantic_search(
            query=query,
            limit=10,
            debug_mode=True
        )
        
        print(f"記事検索結果: {len(normal_results)}件")
        for i, result in enumerate(normal_results[:5]):
            print(f"  {i+1}. {result.article.name} (スコア: {result.score:.3f})")
        
        print("\n" + "="*50 + "\n")
        
        # 2. QAサービスでの検索（内部処理を確認）
        print("=== 2. QAサービス内での検索 ===")
        
        # QAサービスの内部検索処理を手動実行
        extended_limit = max(5 * 2, 10)
        qa_search_results = search_service.semantic_search(
            query=query,
            limit=extended_limit,
            debug_mode=True
        )
        
        print(f"QA用検索結果: {len(qa_search_results)}件")
        
        # 品質チェック処理を再現
        high_quality_results = []
        for result in qa_search_results:
            if result.score >= 1.5:  # タイトルマッチ（スコア2.0）や高品質な結果
                high_quality_results.append(result)
                print(f"  高品質: {result.article.name} (スコア: {result.score:.3f})")
        
        final_qa_results = high_quality_results[:5] if high_quality_results else qa_search_results[:5]
        
        print(f"\n最終QA用記事: {len(final_qa_results)}件")
        for i, result in enumerate(final_qa_results):
            print(f"  {i+1}. {result.article.name} (スコア: {result.score:.3f})")
        
        print("\n" + "="*50 + "\n")
        
        # 3. スコア分析
        print("=== 3. スコア分析 ===")
        if normal_results:
            normal_scores = [r.score for r in normal_results]
            print(f"通常検索 - 最高スコア: {max(normal_scores):.3f}, 平均: {sum(normal_scores)/len(normal_scores):.3f}")
            print(f"通常検索 - 1.5以上のスコア: {len([s for s in normal_scores if s >= 1.5])}件")
        
        if qa_search_results:
            qa_scores = [r.score for r in qa_search_results]
            print(f"QA検索 - 最高スコア: {max(qa_scores):.3f}, 平均: {sum(qa_scores)/len(qa_scores):.3f}")
            print(f"QA検索 - 1.5以上のスコア: {len([s for s in qa_scores if s >= 1.5])}件")
        
        # 4. 実際のQAサービス呼び出し
        print("\n=== 4. 実際のQAサービス呼び出し ===")
        question = "Ubuntuのインストール方法を教えてください"
        
        try:
            qa_result = qa_service.answer_question(question, context_limit=5)
            print(f"QA回答結果:")
            print(f"  信頼度: {qa_result.confidence:.1%}")
            print(f"  参考記事数: {len(qa_result.source_articles)}")
            print(f"  回答: {qa_result.answer[:100]}...")
            
            if qa_result.source_articles:
                print("  参考記事:")
                for i, article in enumerate(qa_result.source_articles):
                    print(f"    {i+1}. {article.name}")
        except Exception as e:
            print(f"  ❌ QAサービス呼び出し失敗: {e}")
        
    except Exception as e:
        print(f"❌ 調査失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    compare_search_results()
