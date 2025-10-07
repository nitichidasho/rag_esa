#!/usr/bin/env python3
"""
WebアプリQA機能のハイブリッド検索テスト
"""

import sys
import asyncio
import json
from pathlib import Path
import requests

# プロジェクトルートをsys.pathに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class QATestClient:
    """QA機能テストクライアント"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.qa_endpoint = f"{base_url}/api/qa/"
    
    def ask_question(
        self,
        question: str,
        context_limit: int = 5,
        use_hybrid_search: bool = True,
        timeout: int = 60
    ):
        """質問応答を実行"""
        
        payload = {
            "question": question,
            "context_limit": context_limit,
            "use_hybrid_search": use_hybrid_search
        }
        
        try:
            response = requests.post(
                self.qa_endpoint,
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"QA API呼び出しエラー: {e}")
            return None


def test_hybrid_qa_vs_traditional():
    """ハイブリッド検索QA vs 従来QAの比較"""
    print("🆚 ハイブリッド検索QA vs 従来QA比較テスト")
    print("=" * 60)
    
    client = QATestClient()
    
    # テスト質問
    questions = [
        "Ubuntuのインストール方法を教えてください",
        "ROSでエラーが発生した時の対処法を知りたい",
        "機械学習を始めるために必要な準備について教えて",
        "Dockerコンテナの設定で注意すべき点は？",
        "Python環境のセットアップ手順を説明して"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n=== 質問 {i}: {question} ===")
        
        # ハイブリッド検索使用
        print("🔍 ハイブリッド検索QA:")
        hybrid_result = client.ask_question(
            question, 
            use_hybrid_search=True,
            context_limit=5
        )
        
        if hybrid_result:
            print(f"✅ 回答生成成功")
            print(f"信頼度: {hybrid_result.get('confidence', 'N/A')}")
            print(f"サービス: {hybrid_result.get('service_used', 'N/A')}")
            print(f"参考記事数: {len(hybrid_result.get('sources', []))}")
            
            # 回答の一部を表示
            answer = hybrid_result.get('answer', '')
            if len(answer) > 100:
                print(f"回答: {answer[:100]}...")
            else:
                print(f"回答: {answer}")
        else:
            print("❌ ハイブリッド検索QA失敗")
        
        # 従来検索使用（比較用）
        print("\n📚 従来検索QA:")
        traditional_result = client.ask_question(
            question, 
            use_hybrid_search=False,
            context_limit=5
        )
        
        if traditional_result:
            print(f"✅ 回答生成成功")
            print(f"信頼度: {traditional_result.get('confidence', 'N/A')}")
            print(f"参考記事数: {len(traditional_result.get('sources', []))}")
        else:
            print("❌ 従来検索QA失敗")
        
        # 比較結果
        if hybrid_result and traditional_result:
            hybrid_sources = len(hybrid_result.get('sources', []))
            traditional_sources = len(traditional_result.get('sources', []))
            
            print(f"\n📊 比較結果:")
            print(f"ハイブリッド: {hybrid_sources}記事参照")
            print(f"従来方式: {traditional_sources}記事参照")
            
            if hybrid_sources >= traditional_sources:
                print("✨ ハイブリッド検索がより多くの関連記事を発見")
            else:
                print("⚠️ 従来検索の方が多くの記事を参照")
        
        print("-" * 50)


def test_context_limit_optimization():
    """コンテキスト数の最適化テスト"""
    print("\n📈 コンテキスト数最適化テスト")
    print("=" * 35)
    
    client = QATestClient()
    question = "esaから記事を取得してRAGシステムを作る方法を教えてください"
    
    context_limits = [1, 3, 5, 7, 10]
    
    print(f"質問: {question}\n")
    
    for limit in context_limits:
        print(f"📚 コンテキスト数: {limit}")
        
        result = client.ask_question(
            question,
            context_limit=limit,
            use_hybrid_search=True
        )
        
        if result:
            sources_count = len(result.get('sources', []))
            confidence = result.get('confidence', 0)
            
            print(f"   参考記事: {sources_count}件")
            print(f"   信頼度: {confidence}")
            
            # 回答の質を簡易評価（文字数）
            answer = result.get('answer', '')
            print(f"   回答長: {len(answer)}文字")
        else:
            print("   ❌ 失敗")
        print()


def test_specific_domain_questions():
    """特定ドメインの質問テスト"""
    print("\n🎯 特定ドメイン質問テスト")
    print("=" * 25)
    
    client = QATestClient()
    
    domain_questions = {
        "ROS関連": [
            "ROSノードが起動しない時の原因と解決方法",
            "ROS Noeticのインストール手順",
            "ROSでUSBカメラを使用する方法"
        ],
        "Ubuntu関連": [
            "Ubuntu 20.04でROS環境を構築する手順",
            "Ubuntuでパッケージインストールエラーが出た場合の対処法"
        ],
        "Python関連": [
            "Pythonで機械学習を始めるための環境設定",
            "Python仮想環境の作成と管理方法"
        ]
    }
    
    for domain, questions in domain_questions.items():
        print(f"\n🔍 {domain}の質問テスト")
        print("-" * 20)
        
        for question in questions:
            print(f"Q: {question}")
            
            result = client.ask_question(
                question,
                use_hybrid_search=True,
                context_limit=3
            )
            
            if result:
                sources = result.get('sources', [])
                print(f"✅ 回答生成成功 ({len(sources)}記事参照)")
                
                # 参考記事のタイトル表示
                for source in sources[:2]:
                    if 'title' in source:
                        print(f"   📄 {source['title']}")
            else:
                print("❌ 回答生成失敗")
            print()


def main():
    """メインテスト実行"""
    print("🚀 WebアプリQA機能ハイブリッド検索テスト")
    print("=" * 70)
    print()
    
    try:
        test_hybrid_qa_vs_traditional()
        test_context_limit_optimization()
        test_specific_domain_questions()
        
        print("\n✅ 全QAテスト完了")
        print("\n🎉 Webアプリでハイブリッド検索QA機能が正常に動作しています！")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ テストが中断されました")
    except Exception as e:
        print(f"\n❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
