# 研究室RAGシステム Webアプリケーション使い方ガイド

## 🚀 アプリケーションの起動方法

### 1. **APIサーバーのみ起動**
```bash
cd research-rag-system
uv run python scripts/rag_manager.py serve
```
- アクセス先: http://localhost:8000
- SwaggerUI: http://localhost:8000/docs

### 2. **フロントエンド付きで起動**
```bash
cd research-rag-system
uv run python scripts/rag_manager.py serve --frontend
```
- API: http://localhost:8000
- フロントエンド: http://localhost:8501

### 3. **カスタムポートで起動**
```bash
cd research-rag-system
uv run python scripts/rag_manager.py serve --port 8080 --frontend
```
- API: http://localhost:8080
- フロントエンド: http://localhost:8081

## 📱 Webアプリケーションの機能

### **1. フロントエンド (Streamlit)**
- **記事検索**: 自然言語での記事検索
- **記事一覧**: カテゴリ別記事表示
- **記事詳細**: 記事内容の表示
- **統計情報**: データベース統計

### **2. API (FastAPI)**
- **RESTful API**: プログラムからのアクセス
- **Swagger UI**: API仕様書とテスト画面
- **検索エンドポイント**: `/api/search`
- **記事取得**: `/api/articles/{id}`

## 🔍 主要な使用方法

### **記事検索**
1. フロントエンドにアクセス
2. 検索ボックスに自然言語で質問入力
   - 例: "機械学習の手法について"
   - 例: "Pythonのコード例"
   - 例: "研究室の活動"
3. 関連記事が類似度順で表示

### **記事閲覧**
1. 検索結果から記事を選択
2. 記事の詳細内容を表示
3. 元のesa.ioへのリンクも利用可能

### **API利用**
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

## 🛠️ 開発者向け機能

### **Swagger UI** (http://localhost:8000/docs)
- 全APIエンドポイントの確認
- インタラクティブなAPI試験
- レスポンス形式の確認

### **管理機能**
```bash
# データ状況確認
uv run python scripts/rag_manager.py check

# 新しい記事の追加ベクトル化
uv run python scripts/rag_manager.py vectorize

# 記事検索テスト
uv run python scripts/rag_manager.py search "検索語"
```

## 📊 対応データ

- **記事数**: 1,176件
- **メンバー**: 20人
- **検索方式**: セマンティック検索 + キーワード検索
- **言語**: 日本語対応
- **更新**: リアルタイム更新可能

## 🔧 設定ファイル

環境変数での設定カスタマイズ:
```env
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_PORT=8501
LOG_LEVEL=INFO
```

## 📚 活用例

### **研究室メンバー向け**
- 過去の研究記録検索
- 技術ノウハウの共有
- 進捗報告の参照

### **外部ユーザー向け**
- 研究室活動の紹介
- 技術情報の提供
- FAQ的な使用

## 🚨 トラブルシューティング

### **起動エラー**
```bash
# データ状況確認
uv run python scripts/rag_manager.py check

# 依存関係確認
uv sync
```

### **検索結果が表示されない**
```bash
# ベクトル化状況確認
uv run python scripts/rag_manager.py check --detailed

# 再ベクトル化
uv run python scripts/export_esa_data.py --vectorize-only
```

### **ポート競合**
```bash
# 別ポートで起動
uv run python scripts/rag_manager.py serve --port 9000
```
