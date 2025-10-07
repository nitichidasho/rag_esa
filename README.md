# 研究室RAGシステム

## プロジェクトの説明

このプロジェクトは、研究室のesa.ioに投稿されている研究活動に関する記事をデータベース化し、無料LLMモデルを活用したRAG（Retrieval-Augmented Generation）システムです。

### 主要機能
- esa.io APIを使用した記事の自動収集・更新
- ベクトル化による記事の効率的な検索・分類
- 自然言語処理による高精度な質問応答システム
- Web UIによる直感的なユーザーインターフェース
- **🚀 GPU対応**: CUDA環境での高速推論をサポート

### Webアプリケーション機能
- **記事検索**: 自然言語での記事検索
- **記事一覧**: カテゴリ別記事表示
- **記事詳細**: 記事内容の表示
- **統計情報**: データベース統計
- **RESTful API**: プログラムからのアクセス
- **Swagger UI**: API仕様書とテスト画面

## 実行手順

### 1. APIサーバーのみ起動
```bash
cd research-rag-system
uv run python scripts/rag_manager.py serve
```

### 2. フロントエンド付きで起動
```bash
cd research-rag-system
uv run python scripts/rag_manager.py serve --frontend
```

### 3. カスタムポートで起動
```bash
cd research-rag-system
uv run python scripts/rag_manager.py serve --port 8080 --frontend
```

### 4. GPU対応起動（推奨）
```bash
# GPU環境チェック
python launch_gpu.py --check-only

# 依存関係インストール
python launch_gpu.py --install-deps

# フロントエンド付きで起動
python launch_gpu.py --frontend --port 8000
```

### 主要な使用方法
1. **記事検索**: フロントエンドにアクセスし、検索ボックスに自然言語で質問入力
   - 例: "機械学習の手法について"
   - 例: "Pythonのコード例"
   - 例: "研究室の活動"
2. **記事閲覧**: 検索結果から記事を選択して詳細内容を表示
3. **API利用**: プログラムからRESTful APIを使用

## その他

### システム要件

#### CPU環境
- Python 3.8以上
- RAM 8GB以上推奨

#### GPU環境（推奨）
- NVIDIA GPU (CUDA対応)
- GPU メモリ 6GB以上推奨
- CUDA 11.8以上

### 従来のセットアップ方法

#### 1. 環境変数設定
```bash
cp .env.example .env
# .envファイルを編集してAPIトークンを設定
```

#### 2. 依存関係のインストール
```bash
pip install -e .
```

#### 3. データベース初期化
```bash
python scripts/setup_db.py
```

#### 4. データエクスポート実行
```bash
python scripts/export_esa_data.py
```

### 従来の起動方法

#### 1. バックエンドAPI起動
```bash
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

#### 2. フロントエンド起動
```bash
streamlit run src/frontend/app.py
```

### 開発者向け機能

#### Swagger UI
- アクセス先: http://localhost:8000/docs
- 全APIエンドポイントの確認
- インタラクティブなAPI試験
- レスポンス形式の確認

#### 管理機能
```bash
# データ状況確認
uv run python scripts/rag_manager.py check

# 新しい記事の追加ベクトル化
uv run python scripts/rag_manager.py vectorize

# 記事検索テスト
uv run python scripts/rag_manager.py search "検索語"
```

#### API利用例
```python
import requests

# 記事検索
response = requests.get("http://localhost:8000/api/search", 
                       params={"query": "機械学習", "limit": 5})
results = response.json()

# 特定記事取得
response = requests.get("http://localhost:8000/api/articles/123")
article = response.json()
```

### 対応データ
- **記事数**: 1,176件
- **メンバー**: 20人
- **検索方式**: セマンティック検索 + キーワード検索
- **言語**: 日本語対応
- **更新**: リアルタイム更新可能

### 設定ファイル
環境変数での設定カスタマイズ:
```env
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_PORT=8501
LOG_LEVEL=INFO
```

### 活用例

#### 研究室メンバー向け
- 過去の研究記録検索
- 技術ノウハウの共有
- 進捗報告の参照

#### 外部ユーザー向け
- 研究室活動の紹介
- 技術情報の提供
- FAQ的な使用

### トラブルシューティング

#### 起動エラー
```bash
# データ状況確認
uv run python scripts/rag_manager.py check

# 依存関係確認
uv sync
```

#### 検索結果が表示されない
```bash
# ベクトル化状況確認
uv run python scripts/rag_manager.py check --detailed

# 再ベクトル化
uv run python scripts/export_esa_data.py --vectorize-only
```

#### ポート競合
```bash
# 別ポートで起動
uv run python scripts/rag_manager.py serve --port 9000
```

### 開発

#### テスト実行
```bash
pytest
```

#### コードフォーマット
```bash
black .
flake8 .
```

### 技術スタック
- **フロントエンド**: Streamlit
- **バックエンド**: FastAPI
- **ベクトルDB**: ChromaDB
- **メタデータDB**: SQLite
- **埋め込みモデル**: sentence-transformers/all-MiniLM-L6-v2
- **LLMモデル**: google/flan-t5-base

## ライセンス

このプロジェクトは [MIT License](LICENSE) の下で公開されています。
