# research-rag-system 起動方法

## 1. 環境設定

### 依存関係のインストール
```bash
pip install -e .
```

### 環境変数設定
```bash
cp .env.example .env
# .envファイルを編集してAPIトークンを設定
```

## 2. データベースセットアップ

```bash
python scripts/setup_db.py
```

## 3. データエクスポート

```bash
python scripts/export_esa_data.py
```

## 4. アプリケーション起動

### バックエンドAPI
```bash
python main.py
# または
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### フロントエンド
```bash
streamlit run src/frontend/app.py
```

## 5. アクセス

- API: http://localhost:8000
- WebUI: http://localhost:8501
- API文書: http://localhost:8000/docs

## トラブルシューティング

- 依存関係エラー: `pip install -r requirements.txt`
- 権限エラー: 認証情報を.envファイルで確認
- データベースエラー: `python scripts/setup_db.py` を再実行
