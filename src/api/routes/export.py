"""
データエクスポートAPI
"""

import asyncio
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
import csv
import io

from ...services.esa_api_service import EsaAPIClient
from ...database.repositories.article_repository import ArticleRepository
from ...database.repositories.member_repository import MemberRepository

router = APIRouter()


class ExportStatus(BaseModel):
    """エクスポート状況"""
    status: str
    progress: int
    total: int
    message: str


# グローバル変数でエクスポート状況を管理（実際の運用では Redis などを使用）
export_status = {
    "status": "idle",
    "progress": 0,
    "total": 0,
    "message": "待機中"
}


@router.post("/")
async def start_export():
    """esa.io データのエクスポートを開始"""
    global export_status
    
    if export_status["status"] == "running":
        raise HTTPException(status_code=409, detail="既にエクスポートが実行中です")
    
    # バックグラウンドでエクスポートを実行
    asyncio.create_task(run_export())
    
    return {"message": "エクスポートを開始しました"}


@router.get("/status")
async def get_export_status():
    """エクスポート進捗の確認"""
    return export_status


async def run_export():
    """バックグラウンドエクスポート処理"""
    global export_status
    
    try:
        export_status["status"] = "running"
        export_status["message"] = "esa.io APIからデータを取得中..."
        
        # esa.io APIクライアント初期化
        api_client = EsaAPIClient()
        
        # メンバー情報を取得
        export_status["message"] = "メンバー情報を取得中..."
        members_response = api_client.get_members()
        members = members_response.get("members", [])
        
        # メンバー情報をデータベースに保存
        member_repo = MemberRepository()
        for member_data in members:
            member_repo.upsert_member({
                "id": member_data["id"],
                "screen_name": member_data["screen_name"],
                "name": member_data["name"],
                "icon": member_data.get("icon", ""),
                "role": member_data.get("role", "member"),
                "posts_count": member_data.get("posts_count", 0),
                "joined_at": member_data.get("joined_at")
            })
        
        # 記事情報を取得
        export_status["message"] = "記事情報を取得中..."
        posts = api_client.export_all_posts()
        export_status["total"] = len(posts)
        
        # 記事をデータベースに保存
        article_repo = ArticleRepository()
        for i, post_data in enumerate(posts):
            try:
                article_repo.upsert_article({
                    "number": post_data["number"],
                    "name": post_data["name"],
                    "full_name": post_data["full_name"],
                    "wip": post_data["wip"],
                    "body_md": post_data["body_md"],
                    "body_html": post_data["body_html"],
                    "created_at": post_data["created_at"],
                    "updated_at": post_data["updated_at"],
                    "url": post_data["url"],
                    "tags": post_data.get("tags", []),
                    "category": post_data.get("category", ""),
                    "created_by_id": post_data["created_by"]["id"],
                    "updated_by_id": post_data["updated_by"]["id"],
                    "processed_text": post_data["body_md"]  # 簡単な前処理
                })
                
                export_status["progress"] = i + 1
                export_status["message"] = f"記事を処理中... ({i + 1}/{len(posts)})"
                
            except Exception as e:
                print(f"記事 {post_data.get('number')} の処理でエラー: {e}")
                continue
        
        export_status["status"] = "completed"
        export_status["message"] = f"エクスポート完了。{len(posts)}件の記事を処理しました。"
        
    except Exception as e:
        export_status["status"] = "error"
        export_status["message"] = f"エラーが発生しました: {str(e)}"


@router.post("/upload/csv")
async def upload_csv_data(file: UploadFile = File(...)):
    """手動CSVアップロード"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="CSVファイルが必要です")
    
    try:
        content = await file.read()
        csv_data = csv.DictReader(io.StringIO(content.decode('utf-8')))
        
        article_repo = ArticleRepository()
        articles_count = 0
        
        for row in csv_data:
            # CSVの列をArticleフィールドにマッピング
            article_data = {
                "number": int(row.get("number", 0)),
                "name": row.get("name", ""),
                "full_name": row.get("full_name", ""),
                "wip": row.get("wip", "false").lower() == "true",
                "body_md": row.get("body_md", ""),
                "body_html": row.get("body_html", ""),
                "created_at": row.get("created_at"),
                "updated_at": row.get("updated_at"),
                "url": row.get("url", ""),
                "tags": row.get("tags", "").split(",") if row.get("tags") else [],
                "category": row.get("category", ""),
                "created_by_id": int(row.get("created_by_id", 1)),
                "updated_by_id": int(row.get("updated_by_id", 1)),
                "processed_text": row.get("body_md", "")
            }
            
            article_repo.upsert_article(article_data)
            articles_count += 1
        
        return {"message": f"{articles_count}件の記事をアップロードしました"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSVアップロードエラー: {str(e)}")


@router.post("/sync")
async def sync_recent_articles(hours: int = 24):
    """差分データの同期更新"""
    try:
        api_client = EsaAPIClient()
        recent_posts = api_client.get_recent_posts(hours=hours)
        
        article_repo = ArticleRepository()
        updated_count = 0
        
        for post_data in recent_posts:
            article_repo.upsert_article({
                "number": post_data["number"],
                "name": post_data["name"],
                "full_name": post_data["full_name"],
                "wip": post_data["wip"],
                "body_md": post_data["body_md"],
                "body_html": post_data["body_html"],
                "created_at": post_data["created_at"],
                "updated_at": post_data["updated_at"],
                "url": post_data["url"],
                "tags": post_data.get("tags", []),
                "category": post_data.get("category", ""),
                "created_by_id": post_data["created_by"]["id"],
                "updated_by_id": post_data["updated_by"]["id"],
                "processed_text": post_data["body_md"]
            })
            updated_count += 1
        
        return {
            "message": f"過去{hours}時間以内の{updated_count}件の記事を同期しました",
            "updated_count": updated_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"同期エラー: {str(e)}")
