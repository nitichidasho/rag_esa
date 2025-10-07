"""
シンプルサーバー起動スクリプト
"""

import uvicorn
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    print("🚀 シンプルサーバー起動中...")
    print("📡 http://localhost:8500 でAPIサーバーを起動します")
    print("💡 依存関係を利用するには 'uv run python simple_server.py' で起動してください")
    
    # 依存関係チェック
    try:
        import transformers
        import torch
        print("✅ 完全なQAサービスが利用可能です")
    except ImportError as e:
        print(f"⚠️  依存関係が不足: {e}")
        print("   フォールバックサービスで起動します")
    
    try:
        uvicorn.run(
            "src.api.main:app",
            host="0.0.0.0",
            port=8500,
            reload=True
        )
    except Exception as e:
        print(f"❌ サーバー起動エラー: {e}")
        import traceback
        traceback.print_exc()
