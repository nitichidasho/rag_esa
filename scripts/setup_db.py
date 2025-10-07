#!/usr/bin/env python3
"""
データベースセットアップスクリプト
"""

import sys
import os
from pathlib import Path

# プロジェクトルートを sys.path に追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.connection import init_db, engine
from src.config.settings import settings
# モデルクラスをインポートしてテーブル作成を有効にする
from src.database.repositories.article_repository import ArticleORM
from src.database.repositories.member_repository import MemberORM


def setup_database():
    """データベースの初期化"""
    print("データベースを初期化中...")
    
    try:
        # データディレクトリの作成
        db_path = Path(settings.database_url.replace("sqlite:///", ""))
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # データベースの初期化
        init_db()
        
        print(f"✅ データベースが正常に初期化されました: {db_path}")
        print(f"✅ データベースURL: {settings.database_url}")
        
        # テーブル一覧を表示
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"✅ 作成されたテーブル: {tables}")
        
    except Exception as e:
        print(f"❌ データベース初期化エラー: {e}")
        sys.exit(1)


def create_directories():
    """必要なディレクトリを作成"""
    directories = [
        "data",
        "data/exports",
        "data/csv_uploads",
        "data/articles", 
        "data/vectors",
        "data/models"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ ディレクトリを作成: {directory}")


def main():
    """メイン処理"""
    print("=== 研究室 esa.io RAGシステム データベースセットアップ ===")
    print()
    
    # ディレクトリ作成
    create_directories()
    print()
    
    # データベース初期化
    setup_database()
    print()
    
    print("🎉 セットアップが完了しました！")
    print()
    print("次のステップ:")
    print("1. .env ファイルを設定してください")
    print("2. python scripts/export_esa_data.py でデータをエクスポートしてください")
    print("3. python main.py でAPIサーバーを起動してください")
    print("4. streamlit run src/frontend/app.py でWebUIを起動してください")


if __name__ == "__main__":
    main()
