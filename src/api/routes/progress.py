"""
進捗追跡とリアルタイム通知のためのエンドポイント
"""

import json
import time
import asyncio
from typing import Dict, Any
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from loguru import logger
import uuid

router = APIRouter()

# 進捗状況を保存するためのグローバル辞書
progress_store: Dict[str, Dict[str, Any]] = {}

class ProgressTracker:
    """進捗追跡クラス"""
    
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.progress_store = progress_store
        self.progress_store[task_id] = {
            "status": "started",
            "progress": 0,
            "message": "処理を開始しています...",
            "details": {},
            "created_at": time.time()
        }
    
    def update(self, progress: int, message: str, details: Dict[str, Any] = None):
        """進捗を更新"""
        if self.task_id in self.progress_store:
            self.progress_store[self.task_id].update({
                "progress": progress,
                "message": message,
                "details": details or {},
                "updated_at": time.time()
            })
            logger.info(f"Progress {self.task_id}: {progress}% - {message}")
    
    def complete(self, message: str = "処理が完了しました", result: Any = None):
        """処理完了"""
        if self.task_id in self.progress_store:
            self.progress_store[self.task_id].update({
                "status": "completed",
                "progress": 100,
                "message": message,
                "result": result,
                "completed_at": time.time()
            })
    
    def error(self, error_message: str):
        """エラー状態"""
        if self.task_id in self.progress_store:
            self.progress_store[self.task_id].update({
                "status": "error",
                "message": f"エラー: {error_message}",
                "error_at": time.time()
            })

@router.get("/progress/{task_id}")
async def get_progress(task_id: str):
    """特定のタスクの進捗状況を取得"""
    if task_id in progress_store:
        return progress_store[task_id]
    else:
        return {"error": "Task not found"}

@router.get("/progress/stream/{task_id}")
async def stream_progress(task_id: str, request: Request):
    """Server-Sent Events を使用した進捗ストリーミング"""
    
    async def event_generator():
        try:
            while True:
                # クライアントの接続状況をチェック
                if await request.is_disconnected():
                    logger.info(f"Client disconnected from progress stream {task_id}")
                    break
                
                # 進捗状況を取得
                if task_id in progress_store:
                    progress_data = progress_store[task_id]
                    
                    # SSE形式でデータを送信
                    yield f"data: {json.dumps(progress_data, ensure_ascii=False)}\n\n"
                    
                    # 完了またはエラーの場合は終了
                    if progress_data.get("status") in ["completed", "error"]:
                        yield f"data: {json.dumps({'status': 'stream_ended'})}\n\n"
                        break
                else:
                    yield f"data: {json.dumps({'error': 'Task not found'})}\n\n"
                    break
                
                # 1秒待機
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in progress stream: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )

@router.delete("/progress/{task_id}")
async def cleanup_progress(task_id: str):
    """進捗データをクリーンアップ"""
    if task_id in progress_store:
        del progress_store[task_id]
        return {"message": "Progress data cleaned up"}
    else:
        return {"error": "Task not found"}

def create_progress_tracker() -> tuple[str, ProgressTracker]:
    """新しい進捗追跡を作成"""
    task_id = str(uuid.uuid4())
    tracker = ProgressTracker(task_id)
    return task_id, tracker

def get_progress_tracker(task_id: str) -> ProgressTracker:
    """既存の進捗追跡を取得"""
    return ProgressTracker(task_id)
