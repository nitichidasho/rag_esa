"""
システム診断スクリプト
"""

import sys
import traceback
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """インポートテスト"""
    print("🔍 インポートテスト開始...")
    
    try:
        print("  ✅ settings...")
        from src.config.settings import settings
        print(f"     - qa_service_type: {settings.qa_service_type}")
        
        print("  ✅ qa_service...")
        from src.services.qa_service import QAService
        
        print("  ✅ langchain_qa_service...")
        from src.services.langchain_qa_service import LangChainQAService
        
        print("  ✅ qa routes...")
        from src.api.routes.qa import router
        
        print("  ✅ main API...")
        from src.api.main import app
        
        print("🎉 すべてのインポートが成功しました！")
        return True
        
    except Exception as e:
        print(f"❌ インポートエラー: {e}")
        traceback.print_exc()
        return False

def test_qa_service():
    """QAサービステスト"""
    print("\n🧪 QAサービステスト開始...")
    
    try:
        from src.services.qa_service import QAService
        qa_service = QAService()
        print("✅ QAService インスタンス作成成功")
        return True
    except Exception as e:
        print(f"❌ QAService エラー: {e}")
        traceback.print_exc()
        return False

def test_langchain_service():
    """LangChainサービステスト"""
    print("\n🚀 LangChainサービステスト開始...")
    
    try:
        from src.services.langchain_qa_service import LangChainQAService
        langchain_service = LangChainQAService()
        print("✅ LangChainQAService インスタンス作成成功")
        return True
    except Exception as e:
        print(f"❌ LangChainQAService エラー: {e}")
        print("💡 これは正常です（依存関係未インストール）")
        return False

def test_server_startup():
    """サーバー起動テスト"""
    print("\n🖥️ サーバー起動テスト開始...")
    
    try:
        from src.api.main import app
        import uvicorn
        
        print("✅ FastAPIアプリ作成成功")
        print("💡 手動でサーバーを起動してください:")
        print("   uv run python scripts/rag_manager.py serve --port 8500")
        return True
        
    except Exception as e:
        print(f"❌ サーバー起動準備エラー: {e}")
        traceback.print_exc()
        return False

def main():
    print("🩺 RAGシステム診断ツール")
    print("=" * 50)
    
    results = []
    
    # テスト実行
    results.append(("インポート", test_imports()))
    results.append(("QAサービス", test_qa_service()))
    results.append(("LangChainサービス", test_langchain_service()))
    results.append(("サーバー準備", test_server_startup()))
    
    # 結果サマリー
    print("\n📊 診断結果:")
    print("-" * 30)
    for test_name, success in results:
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"{test_name:15} {status}")
    
    successful_tests = sum(1 for _, success in results if success)
    print(f"\n🎯 成功率: {successful_tests}/{len(results)} ({successful_tests/len(results)*100:.1f}%)")
    
    if successful_tests >= 3:
        print("\n🚀 システムは起動可能な状態です！")
        print("次のコマンドでサーバーを起動してください:")
        print("uv run python scripts/rag_manager.py serve --frontend --port 8500")
    else:
        print("\n⚠️ 追加の設定が必要です。")

if __name__ == "__main__":
    main()
