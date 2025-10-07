"""
Streamlit メインアプリケーション
"""

import streamlit as st
import requests
from datetime import datetime
import json
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import settings

# ページ設定
st.set_page_config(
    page_title="研究室 esa.io RAGシステム",
    page_icon="🔍",
    layout="wide"
)

# API基本URL（環境変数から動的に設定）
import os
api_port = os.getenv("API_PORT", "8000")  # rag_manager.pyから環境変数で渡される
API_BASE_URL = f"http://localhost:{api_port}/api"

# デバッグ用：実際のAPI URLを表示
print(f"🔗 Frontend connecting to API: {API_BASE_URL}")

# 認証情報
AUTH = (settings.basic_auth_username, settings.basic_auth_password)


def main():
    """メインアプリケーション"""
    st.title("🔍 研究室 esa.io RAGシステム")
    st.markdown("---")
    
    # サイドバーでページ選択
    page = st.sidebar.selectbox(
        "ページを選択",
        ["🔍 検索", "💬 質問応答", "� 進捗表示QA", "�📊 統計情報", "⚙️ 管理"]
    )
    
    if page == "🔍 検索":
        search_page()
    elif page == "💬 質問応答":
        qa_page()
    elif page == "🚀 進捗表示QA":
        progress_qa_page()
        qa_page()
    elif page == "📊 統計情報":
        analytics_page()
    elif page == "⚙️ 管理":
        admin_page()


def search_page():
    """検索ページ"""
    st.header("🔍 記事検索")
    
    # 検索クエリ入力
    query = st.text_input("検索キーワードを入力してください", placeholder="例: 機械学習")
    
    # 検索オプション
    col1, col2 = st.columns(2)
    with col1:
        search_type = st.selectbox("検索タイプ", ["セマンティック検索", "キーワード検索"])
        limit = st.slider("検索結果数", min_value=5, max_value=50, value=10)
    
    with col2:
        category_filter = st.text_input("カテゴリフィルタ", placeholder="例: 研究/2024")
        wip_filter = st.selectbox("WIP記事", ["すべて", "WIPのみ", "WIP以外"])
    
    # 検索実行
    if st.button("🔍 検索実行") and query:
        with st.spinner("検索中..."):
            try:
                if search_type == "セマンティック検索":
                    response = requests.post(
                        f"{API_BASE_URL}/search/",
                        json={
                            "query": query,
                            "limit": limit,
                            "filters": {
                                "category": category_filter if category_filter else None,
                                "wip": None if wip_filter == "すべて" else wip_filter == "WIPのみ"
                            }
                        },
                        auth=AUTH
                    )
                else:
                    response = requests.get(
                        f"{API_BASE_URL}/search/keyword/{query}",
                        params={"limit": limit},
                        auth=AUTH
                    )
                
                if response.status_code == 200:
                    data = response.json()
                    display_search_results(data["results"])
                else:
                    st.error(f"検索エラー: {response.status_code}")
                    
            except Exception as e:
                st.error(f"検索中にエラーが発生しました: {str(e)}")


def display_search_results(results):
    """検索結果を表示"""
    if not results:
        st.info("検索結果が見つかりませんでした。")
        return
    
    st.success(f"🎯 {len(results)}件の記事が見つかりました")
    
    for i, result in enumerate(results):
        article = result["article"]
        
        with st.expander(f"📄 {article['name']} (スコア: {result['score']:.3f})"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**カテゴリ:** {article['category']}")
                if article['tags']:
                    tags = " ".join([f"`{tag}`" for tag in article['tags']])
                    st.markdown(f"**タグ:** {tags}")
                st.markdown(f"**作成日:** {article['created_at'][:10]}")
                st.markdown(f"**更新日:** {article['updated_at'][:10]}")
                
                if "matched_text" in result:
                    st.markdown("**マッチした内容:**")
                    st.text_area(
                        "マッチした内容", 
                        result["matched_text"], 
                        height=100, 
                        key=f"text_{i}",
                        label_visibility="collapsed"
                    )
            
            with col2:
                if article['wip']:
                    st.warning("🚧 WIP")
                st.markdown(f"[📎 記事を開く]({article['url']})")


def qa_page():
    """質問応答ページ"""
    st.header("💬 質問応答")
    
    # サーバー状態チェック
    try:
        status_response = requests.get(f"{API_BASE_URL}/../", auth=AUTH, timeout=5)
        if status_response.status_code == 200:
            status_data = status_response.json()
            qa_status = status_data.get("qa_status", "unknown")
            
            if qa_status == "available":
                st.success("🚀 フル機能QAサービス利用可能")
            elif qa_status == "fallback":
                st.warning("⚠️ フォールバックQAサービス利用中")
                st.info("💡 完全な機能を利用するには依存関係をインストールしてください")
            else:
                st.error("❌ QAサービス利用不可")
        else:
            st.warning("⚠️ サーバー状態を確認できません")
    except:
        st.warning("⚠️ サーバー接続確認中...")
    
    # システム情報の表示
    with st.expander("ℹ️ システム情報"):
        st.markdown("**実装方式:** LangChainベースのRAGシステム")
        st.markdown("**参考実装:** [Zenn RAG tutorial](https://zenn.dev/rounda_blog/articles/080a71cdc54f3f)")
        st.markdown("**特徴:**")
        st.markdown("- 検索フェーズと生成フェーズの分離")
        st.markdown("- 構造化されたプロンプト設計")
        st.markdown("- 複数記事の統合による回答生成")
        st.markdown("- 代替モデルによるMistral-Small-3.1の機能実現")
        st.markdown("- **GPU対応:** 自動的にCPU/GPU環境を検出して最適化")
        
        st.markdown("**🚀 GPU最適化機能:**")
        st.markdown("- GPU メモリに応じた自動バッチサイズ調整")
        st.markdown("- float16精度による高速推論")
        st.markdown("- モデル分散配置（large モデル対応）")
        st.caption("💡 RTX 3060 (6GB) 以上のGPUで大幅な高速化が期待できます")
    
    # 質問入力
    question = st.text_area(
        "質問を入力してください",
        placeholder="例: 機械学習の最新手法について教えてください",
        height=100
    )
    
    # パラメータ設定
    col1, col2 = st.columns(2)
    with col1:
        context_limit = st.slider("参考記事数", min_value=1, max_value=10, value=5)
    with col2:
        st.markdown("**🎯 RAGの仕組み**")
        st.caption("1. 関連記事を検索\n2. コンテキストを構築\n3. LLMで回答生成")
    
    # 質問実行
    if st.button("💬 質問する") and question:
        with st.spinner("回答を生成中..."):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/qa/",
                    json={
                        "question": question,
                        "context_limit": context_limit
                    },
                    auth=AUTH
                )
                
                if response.status_code == 200:
                    data = response.json()
                    display_qa_result(data)
                elif response.status_code == 404:
                    st.error("❌ QAエンドポイントが見つかりません")
                    st.info("💡 サーバーを再起動してください")
                    with st.expander("🔧 トラブルシューティング"):
                        st.markdown("**考えられる原因:**")
                        st.markdown("- QAサービスの依存関係が不足")
                        st.markdown("- transformersライブラリ未インストール")
                        st.markdown("- PyTorchライブラリ未インストール")
                        st.markdown("\n**解決方法:**")
                        st.code("uv add transformers torch", language="bash")
                else:
                    st.error(f"質問応答エラー: {response.status_code}")
                    if response.status_code == 500:
                        try:
                            error_detail = response.json().get("detail", "Unknown error")
                            st.error(f"詳細: {error_detail}")
                        except:
                            st.error("サーバー内部エラーが発生しました")
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ APIサーバーに接続できません")
                st.info(f"💡 {API_BASE_URL} でサーバーが起動していることを確認してください")
            except Exception as e:
                st.error(f"質問応答中にエラーが発生しました: {str(e)}")


def display_qa_result(data):
    """質問応答結果を表示"""
    st.markdown("## 🤖 回答")
    
    # サービス情報の表示
    if "service_used" in data:
        service_info = data["service_used"]
        if service_info == "fallback":
            st.error("⚠️ **フォールバックサービス使用中**")
            st.info("完全な機能を利用するには、依存関係をインストールしてください")
        elif "langchain" in service_info.lower():
            st.success(f"🚀 **使用サービス:** {service_info}")
        elif "fallback" in service_info.lower():
            st.warning(f"⚠️ **使用サービス:** {service_info}")
        else:
            st.info(f"💻 **使用サービス:** {service_info}")
    
    # エラー情報の表示
    if "error" in data:
        st.warning(f"⚠️ **注意:** {data['error']}")
        with st.expander("🔧 解決方法"):
            st.markdown("**必要な依存関係をインストール:**")
            st.code("uv add transformers torch", language="bash")
            st.markdown("**または GPU版PyTorch:**")
            st.code("uv add torch torchvision torchaudio --index https://download.pytorch.org/whl/cu118", language="bash")
    
    # モデル情報の表示（LangChainサービスの場合）
    if "model_info" in data:
        with st.expander("🔧 使用モデル情報"):
            model_info = data["model_info"]
            st.markdown(f"**モデル名:** `{model_info.get('model_name', 'N/A')}`")
            st.markdown(f"**タイプ:** {model_info.get('model_type', 'N/A')}")
            st.markdown(f"**実装ベース:** {model_info.get('implementation_based_on', 'N/A')}")
            
            # GPU情報の表示
            if "device_config" in model_info:
                device_config = model_info["device_config"]
                device_type = device_config.get("device_type", "Unknown")
                
                if device_type.startswith("GPU"):
                    st.success(f"🚀 **実行環境:** {device_type}")
                    if "memory_gb" in device_config:
                        st.markdown(f"**GPU メモリ:** {device_config['memory_gb']:.1f}GB")
                    st.markdown(f"**バッチサイズ:** {device_config.get('batch_size', 'N/A')}")
                    st.markdown(f"**データ型:** {str(device_config.get('dtype', 'N/A')).split('.')[-1]}")
                else:
                    st.info(f"💻 **実行環境:** {device_type}")
                    st.caption("💡 GPU環境では更に高速な処理が可能です")
            
            if model_info.get('capabilities'):
                st.markdown("**機能:**")
                for capability in model_info['capabilities']:
                    st.markdown(f"- {capability}")
    
    st.markdown(f"**信頼度:** {data['confidence']:.1%}")
    st.markdown("---")
    
    # 回答を表示
    st.markdown(data["answer"])
    
    # 参考記事を表示
    if data["sources"]:
        st.markdown("## 📚 参考記事")
        for source in data["sources"]:
            with st.expander(f"📄 {source['name']}"):
                st.markdown(f"**カテゴリ:** {source['category']}")
                if source['tags']:
                    tags = " ".join([f"`{tag}`" for tag in source['tags']])
                    st.markdown(f"**タグ:** {tags}")
                st.markdown(f"[📎 記事を開く]({source['url']})")
    elif "error" in data:
        st.info("💡 フォールバックモードでは記事検索機能は利用できません")


def analytics_page():
    """統計情報ページ"""
    st.header("📊 統計情報")
    
    try:
        # 最近の記事を取得
        response = requests.get(f"{API_BASE_URL}/articles/recent/", auth=AUTH)
        
        if response.status_code == 200:
            data = response.json()
            articles = data["articles"]
            
            st.metric("📄 最近の記事数", len(articles))
            
            # 最近の記事一覧
            st.subheader("📅 最近の記事")
            for article in articles[:10]:
                with st.expander(f"📄 {article['name']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**カテゴリ:** {article['category']}")
                        st.markdown(f"**作成日:** {article['created_at'][:10]}")
                    with col2:
                        st.markdown(f"**更新日:** {article['updated_at'][:10]}")
                        if article['wip']:
                            st.warning("🚧 WIP")
        else:
            st.error("統計情報の取得に失敗しました")
            
    except Exception as e:
        st.error(f"統計情報の取得中にエラーが発生しました: {str(e)}")


def admin_page():
    """管理ページ"""
    st.header("⚙️ システム管理")
    
    # データエクスポート
    st.subheader("📥 データエクスポート")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 フルエクスポート開始"):
            with st.spinner("エクスポートを開始中..."):
                try:
                    response = requests.post(f"{API_BASE_URL}/export/", auth=AUTH)
                    if response.status_code == 200:
                        st.success("エクスポートを開始しました")
                    else:
                        st.error("エクスポート開始に失敗しました")
                except Exception as e:
                    st.error(f"エラー: {str(e)}")
    
    with col2:
        if st.button("📊 エクスポート状況確認"):
            try:
                response = requests.get(f"{API_BASE_URL}/export/status", auth=AUTH)
                if response.status_code == 200:
                    status = response.json()
                    st.json(status)
                else:
                    st.error("状況確認に失敗しました")
            except Exception as e:
                st.error(f"エラー: {str(e)}")
    
    # 差分同期
    st.subheader("🔄 差分同期")
    hours = st.slider("同期対象時間（時間）", min_value=1, max_value=168, value=24)
    
    if st.button("🔄 差分同期実行"):
        with st.spinner("差分同期中..."):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/export/sync",
                    params={"hours": hours},
                    auth=AUTH
                )
                if response.status_code == 200:
                    data = response.json()
                    st.success(data["message"])
                else:
                    st.error("差分同期に失敗しました")
            except Exception as e:
                st.error(f"エラー: {str(e)}")
    
    # CSVアップロード
    st.subheader("📤 CSVアップロード")
    uploaded_file = st.file_uploader("CSVファイルを選択", type="csv")
    
    if uploaded_file and st.button("📤 アップロード"):
        with st.spinner("アップロード中..."):
            try:
                files = {"file": uploaded_file.getvalue()}
                response = requests.post(
                    f"{API_BASE_URL}/export/upload/csv",
                    files=files,
                    auth=AUTH
                )
                if response.status_code == 200:
                    data = response.json()
                    st.success(data["message"])
                else:
                    st.error("アップロードに失敗しました")
            except Exception as e:
                st.error(f"エラー: {str(e)}")


def progress_qa_page():
    """進捗表示機能付き質問応答ページ"""
    try:
        # テンプレートファイルを直接読み込み
        template_path = Path(__file__).parent / "templates" / "progress_qa.py"
        if template_path.exists():
            import importlib.util
            spec = importlib.util.spec_from_file_location("progress_qa", template_path)
            progress_qa_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(progress_qa_module)
            PROGRESS_QA_HTML = progress_qa_module.PROGRESS_QA_HTML
        else:
            # フォールバック: 基本的なHTMLを定義
            PROGRESS_QA_HTML = """
            <h2>進捗表示機能付きQA</h2>
            <p>テンプレートファイルが見つかりません。通常のQAページをご利用ください。</p>
            """
    except Exception as e:
        st.error(f"進捗QAテンプレートの読み込みエラー: {e}")
        PROGRESS_QA_HTML = """
        <h2>進捗表示機能付きQA</h2>
        <p>現在メンテナンス中です。通常のQAページをご利用ください。</p>
        """
    
    st.title("🚀 進捗表示機能付き質問応答")
    st.markdown("---")
    
    st.markdown("""
    このページでは、回答生成の進捗をリアルタイムで確認できます。
    
    **機能:**
    - ✅ リアルタイム進捗表示
    - 📊 処理段階の詳細表示  
    - 🔄 Server-Sent Events (SSE) による更新
    - 📱 レスポンシブデザイン
    """)
    
    # HTMLインターフェースを表示
    try:
        st.components.v1.html(PROGRESS_QA_HTML, height=800, scrolling=True)
    except Exception as e:
        st.error(f"HTMLコンポーネントの表示エラー: {e}")
        st.markdown("**代替手段**: 通常のQAページをご利用ください。")
    
    st.markdown("---")
    st.markdown("""
    **使用方法:**
    1. 質問を入力欄に記入
    2. 「質問する（進捗表示付き）」ボタンをクリック
    3. 進捗バーで処理状況を確認
    4. 完了後、回答と参考記事を確認
    
    **進捗段階:**
    - 5-10%: QAサービス初期化
    - 15-50%: ハイブリッド検索実行
    - 60-70%: 質問分析とプロンプト構築
    - 80-95%: AIモデルによる回答生成
    - 100%: 完了
    """)

    # 追加: 簡易的な進捗QA機能
    st.subheader("📝 簡易質問応答")
    
    question = st.text_area("質問を入力してください:", height=100)
    
    col1, col2 = st.columns(2)
    with col1:
        use_hybrid = st.checkbox("ハイブリッド検索を使用", value=True)
    with col2:
        context_limit = st.slider("参考記事数", 1, 10, 5)
    
    if st.button("質問する", type="primary"):
        if question.strip():
            with st.spinner("回答を生成中..."):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/qa/",
                        json={
                            "question": question,
                            "use_hybrid_search": use_hybrid,
                            "context_limit": context_limit
                        },
                        auth=AUTH
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        st.success("回答生成完了!")
                        
                        # 回答表示
                        st.markdown("### 📝 回答")
                        st.markdown(result.get("answer", "回答を取得できませんでした"))
                        
                        # 参考記事表示
                        if result.get("sources"):
                            st.markdown("### 📚 参考記事")
                            for i, source in enumerate(result["sources"], 1):
                                st.markdown(f"**{i}. {source.get('name', '無題')}**")
                                if source.get('category'):
                                    st.markdown(f"   カテゴリ: {source['category']}")
                        
                        # メタ情報
                        st.markdown("---")
                        st.caption(f"信頼度: {result.get('confidence', 0)*100:.1f}% | サービス: {result.get('service_used', 'Unknown')}")
                        
                    else:
                        st.error(f"エラー: {response.status_code}")
                        
                except Exception as e:
                    st.error(f"API呼び出しエラー: {e}")
        else:
            st.warning("質問を入力してください")

if __name__ == "__main__":
    main()
