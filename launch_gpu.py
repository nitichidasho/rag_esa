"""
GPU対応RAGシステム起動スクリプト
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# プロジェクトルートの設定
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import torch
    from src.config.settings import settings
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


def check_gpu_environment():
    """GPU環境をチェック"""
    print("🔍 GPU環境をチェック中...")
    
    if not TORCH_AVAILABLE:
        print("❌ PyTorchがインストールされていません")
        return False
    
    print(f"✅ PyTorch version: {torch.__version__}")
    print(f"✅ CUDA available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        device_count = torch.cuda.device_count()
        print(f"✅ CUDA device count: {device_count}")
        
        for i in range(device_count):
            device_name = torch.cuda.get_device_name(i)
            memory_total = torch.cuda.get_device_properties(i).total_memory / 1024**3
            print(f"   GPU {i}: {device_name} ({memory_total:.1f}GB)")
            
            # メモリ推奨事項
            if memory_total >= 12:
                print(f"   💚 推奨: 大型モデル対応可能")
            elif memory_total >= 6:
                print(f"   💛 推奨: 中型モデル使用を推奨") 
            else:
                print(f"   🔴 注意: 小型モデルのみ使用可能")
        
        return True
    else:
        print("ℹ️  CPUモードで実行されます")
        return False


def install_dependencies():
    """GPU対応の依存関係をインストール"""
    print("📦 依存関係をインストール中...")
    
    try:
        # CPU版PyTorchの場合
        subprocess.run([
            "uv", "add", "torch", "torchvision", "torchaudio", 
            "--index", "https://download.pytorch.org/whl/cpu"
        ], check=True)
        
        # transformersとその他の依存関係
        subprocess.run([
            "uv", "add", "transformers", "accelerate", "bitsandbytes"
        ], check=True)
        
        print("✅ 依存関係のインストールが完了しました")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 依存関係のインストールに失敗: {e}")
        return False
    
    return True


def main():
    parser = argparse.ArgumentParser(description="GPU対応RAGシステム起動")
    parser.add_argument("--install-deps", action="store_true", help="依存関係をインストール")
    parser.add_argument("--force-cpu", action="store_true", help="強制的にCPUを使用")
    parser.add_argument("--check-only", action="store_true", help="環境チェックのみ実行")
    parser.add_argument("--port", type=int, default=8000, help="APIサーバーのポート")
    parser.add_argument("--frontend", action="store_true", help="フロントエンドも起動")
    
    args = parser.parse_args()
    
    print("🚀 GPU対応RAGシステム起動スクリプト")
    print("=" * 50)
    
    # 依存関係インストール
    if args.install_deps:
        if not install_dependencies():
            sys.exit(1)
    
    # GPU環境チェック
    gpu_available = check_gpu_environment()
    
    if args.check_only:
        print("✅ 環境チェック完了")
        sys.exit(0)
    
    # 設定適用
    if args.force_cpu:
        os.environ["FORCE_CPU"] = "true"
        print("💻 強制CPUモードが設定されました")
    elif gpu_available:
        print("🚀 GPU加速モードで起動します")
    else:
        print("💻 CPUモードで起動します")
    
    # RAGマネージャーを使用してシステム起動
    cmd = [
        "uv", "run", "python", "scripts/rag_manager.py", 
        "serve", "--port", str(args.port)
    ]
    
    if args.frontend:
        cmd.append("--frontend")
    
    print(f"🎯 実行コマンド: {' '.join(cmd)}")
    print("=" * 50)
    
    try:
        subprocess.run(cmd, cwd=project_root)
    except KeyboardInterrupt:
        print("\n👋 シャットダウン中...")
    except Exception as e:
        print(f"❌ 起動エラー: {e}")


if __name__ == "__main__":
    main()
