"""
RAGシステム設定管理
"""

import os
from pathlib import Path
from typing import Optional


def load_env_file(env_path: Path):
    """手動で.envファイルを読み込み"""
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()


class RAGConfig:
    """RAGシステム設定クラス"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / "data"
        
        # .envファイルを読み込み
        env_file = self.project_root / ".env"
        load_env_file(env_file)
        
        self.load_environment()
    
    def load_environment(self):
        """環境変数の読み込み"""
        # esa.io設定
        self.esa_api_token = os.getenv("ESA_API_TOKEN")
        self.esa_team_name = os.getenv("ESA_TEAM_NAME")
        
        # データベース設定
        self.database_url = os.getenv("DATABASE_URL", f"sqlite:///{self.data_dir}/research_rag.db")
        
        # ベクトルDB設定
        self.vector_db_path = os.getenv("VECTOR_DB_PATH", str(self.data_dir / "vectors"))
        
        # 埋め込みモデル設定
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        
        # API設定
        self.api_host = os.getenv("API_HOST", "0.0.0.0")
        self.api_port = int(os.getenv("API_PORT", "8000"))
        
        # フロントエンド設定
        self.frontend_port = int(os.getenv("FRONTEND_PORT", "8501"))
        
        # ログ設定
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
    
    def validate(self) -> tuple[bool, list[str]]:
        """設定の検証"""
        errors = []
        
        # 必須設定の確認
        if not self.esa_api_token:
            errors.append("ESA_API_TOKEN が設定されていません")
        
        if not self.esa_team_name:
            errors.append("ESA_TEAM_NAME が設定されていません")
        
        # ディレクトリの確認
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True, exist_ok=True)
        
        vector_db_dir = Path(self.vector_db_path)
        if not vector_db_dir.exists():
            vector_db_dir.mkdir(parents=True, exist_ok=True)
        
        return len(errors) == 0, errors
    
    def get_status(self) -> dict:
        """現在の設定状況を取得"""
        is_valid, errors = self.validate()
        
        return {
            "valid": is_valid,
            "errors": errors,
            "esa_configured": bool(self.esa_api_token and self.esa_team_name),
            "database_path": self.database_url,
            "vector_db_path": self.vector_db_path,
            "embedding_model": self.embedding_model,
            "api_endpoint": f"http://{self.api_host}:{self.api_port}",
            "frontend_endpoint": f"http://localhost:{self.frontend_port}"
        }


# グローバル設定インスタンス
config = RAGConfig()
