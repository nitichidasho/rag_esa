"""
アプリケーション設定
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """アプリケーション設定"""
    
    # esa.io API設定
    esa_api_token: str = ""
    esa_team_name: str = ""
    
    # データベース設定
    database_url: str = "sqlite:///./data/research_rag.db"
    vector_db_path: str = "./data/vectors/"
    
    # HuggingFace設定
    hf_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    hf_llm_model: str = "google/flan-t5-base"
    
    # QAサービス設定
    qa_service_type: str = "langchain"  # "original", "langchain", "auto"
    use_mistral_alternative: bool = True  # Mistral-Small-3.1の代替モデルを使用
    
    # サービス自動選択設定
    auto_fallback: bool = True  # LangChainサービス失敗時にオリジナルにフォールバック
    performance_mode: str = "balanced"  # "fast", "balanced", "quality"
    
    # GPU設定
    enable_gpu: bool = True  # GPU利用を有効にする
    force_cpu: bool = False  # 強制的にCPUを使用する
    gpu_memory_fraction: float = 0.8  # 使用するGPUメモリの割合
    
    # アプリケーション設定
    app_host: str = "localhost"
    app_port: int = 8000
    log_level: str = "INFO"
    max_search_results: int = 50
    
    # レート制限設定
    esa_api_rate_limit: int = 300
    rate_limit_buffer: float = 0.8
    
    # 認証設定
    basic_auth_username: str = "lab_member"
    basic_auth_password: str = "your_secure_password"
    allowed_ips: str = "192.168.1.0/24,10.0.0.0/8"
    secret_key: str = "your_secret_key_for_sessions"
    session_timeout: int = 3600
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# グローバル設定インスタンス
settings = Settings()

# データディレクトリの作成
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)
(data_dir / "exports").mkdir(exist_ok=True)
(data_dir / "csv_uploads").mkdir(exist_ok=True)
(data_dir / "articles").mkdir(exist_ok=True)
(data_dir / "vectors").mkdir(exist_ok=True)
(data_dir / "models").mkdir(exist_ok=True)
