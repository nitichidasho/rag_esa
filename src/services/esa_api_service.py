"""
esa.io REST API クライアント
"""

import requests
import time
from typing import List, Dict, Any, Optional
from ratelimit import limits, sleep_and_retry
from datetime import datetime, timedelta
from loguru import logger

from ..config.settings import settings


class EsaAPIClient:
    """esa.io API クライアント"""
    
    def __init__(self, team: str = None, token: str = None):
        self.team = team or settings.esa_team_name
        self.token = token or settings.esa_api_token
        self.base_url = f"https://api.esa.io/v1/teams/{self.team}"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    @sleep_and_retry
    @limits(calls=int(settings.esa_api_rate_limit * settings.rate_limit_buffer), period=3600)
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """レート制限対応のリクエスト実行"""
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
    
    def get_posts(self, page: int = 1, per_page: int = 20) -> Dict:
        """記事一覧の取得"""
        params = {"page": page, "per_page": per_page}
        return self._make_request("posts", params)
    
    def get_post(self, post_number: int) -> Dict:
        """特定記事の取得"""
        return self._make_request(f"posts/{post_number}")
    
    def get_members(self) -> Dict:
        """メンバー一覧の取得"""
        return self._make_request("members")
    
    def export_all_posts(self) -> List[Dict]:
        """全記事のエクスポート（レート制限対応）"""
        posts = []
        page = 1
        
        logger.info("Starting full posts export...")
        
        while True:
            try:
                response = self.get_posts(page=page, per_page=100)
                batch_posts = response.get("posts", [])
                
                if not batch_posts:
                    break
                    
                posts.extend(batch_posts)
                logger.info(f"Exported page {page}, total posts: {len(posts)}")
                
                page += 1
                # レート制限対応の待機
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error on page {page}: {e}")
                break
        
        logger.info(f"Export completed. Total posts: {len(posts)}")
        return posts
    
    def get_recent_posts(self, hours: int = 24) -> List[Dict]:
        """指定時間以内の更新記事を取得"""
        since = datetime.now() - timedelta(hours=hours)
        all_posts = self.export_all_posts()
        
        recent_posts = []
        for post in all_posts:
            try:
                updated_at = datetime.fromisoformat(post["updated_at"].replace('Z', '+00:00'))
                if updated_at > since:
                    recent_posts.append(post)
            except (KeyError, ValueError) as e:
                logger.warning(f"Error parsing post date: {e}")
                continue
        
        logger.info(f"Found {len(recent_posts)} recent posts in last {hours} hours")
        return recent_posts
