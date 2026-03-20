"""Forumbee REST API v2 client."""

import os
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv


class ForumbeeConfigError(Exception):
    """Raised when Forumbee configuration is missing or invalid."""


class ForumbeeClient:
    """Async client for the Forumbee REST API v2."""

    def __init__(self) -> None:
        # Load .env from mcp-server dir or project root
        for candidate in [
            Path(__file__).resolve().parent.parent.parent / ".env",
            Path(__file__).resolve().parent.parent.parent.parent / ".env",
        ]:
            if candidate.exists():
                load_dotenv(candidate)
                break

        self.domain = os.getenv("FORUMBEE_DOMAIN")
        self.token = os.getenv("FORUMBEE_API_TOKEN")

        if not self.domain:
            raise ForumbeeConfigError(
                "FORUMBEE_DOMAIN not set. Copy .env.example to .env and fill in your community domain."
            )
        if not self.token:
            raise ForumbeeConfigError(
                "FORUMBEE_API_TOKEN not set. Copy .env.example to .env and fill in your API token."
            )

        self.base_url = f"https://{self.domain}/api/2"

    async def _request(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make an authenticated GET request to the Forumbee API."""
        url = f"{self.base_url}/{endpoint}"
        headers = {"Authorization": f"Bearer {self.token}"}
        async with httpx.AsyncClient() as http:
            response = await http.get(url, headers=headers, params=params, timeout=30.0)
            if response.status_code == 401:
                raise ForumbeeConfigError("Invalid or expired API token. Check FORUMBEE_API_TOKEN in .env")
            response.raise_for_status()
            return response.json()

    async def search_posts(
        self,
        query: str,
        category: str | None = None,
        post_type: str | None = None,
        limit: int = 25,
    ) -> dict[str, Any]:
        """Search posts by keyword."""
        params: dict[str, Any] = {
            "fields": "postKey,title,text,category.name,author.name,posted,url,replyCount,likeCount,viewCount",
            "textFormat": "plain-truncate-200",
            "search": query,
            "sort": "best",
            "limit": min(limit, 1000),
        }
        if category:
            params["categoryLink"] = category
        if post_type:
            params["postType"] = post_type
        return await self._request("posts", params)

    async def list_categories(self) -> dict[str, Any]:
        """Get all categories."""
        params = {
            "fields": "link,name,type,categoryKey,parentName,topicCount,lastActiveDate,url,path",
        }
        return await self._request("categories", params)

    async def list_posts_in_category(
        self,
        category: str,
        sort: str = "active",
        limit: int = 25,
    ) -> dict[str, Any]:
        """List topics in a category."""
        params: dict[str, Any] = {
            "fields": "postKey,title,text,author.name,posted,active,url,replyCount,likeCount,viewCount",
            "textFormat": "plain-truncate-200",
            "categoryLink": category,
            "postType": "topics",
            "sort": sort,
            "limit": min(limit, 1000),
        }
        return await self._request("posts", params)

    async def get_post(self, post_key: str) -> dict[str, Any]:
        """Get full details for a specific post and its replies."""
        params: dict[str, Any] = {
            "fields": "postKey,parentKey,title,text,typeLabel,category.name,author.name,author.handle,posted,active,url,replyCount,likeCount,viewCount,followCount",
            "textFormat": "html",
            "topicKey": post_key,
            "limit": 100,
        }
        return await self._request("posts", params)

    async def get_metrics(
        self,
        metric_type: str,
        period: str = "30d",
        interval: str | None = None,
        limit: int = 25,
    ) -> dict[str, Any]:
        """Get community metrics."""
        fields_map = {
            "users": "date,period,users,page_views,joined,topic_posts,reply_posts,all_posts",
            "searches": "query,search_count,top_clicked_url",
            "topics": "topicKey,topicTitle,topicUrl,replies,likes,views,category",
        }
        if metric_type not in fields_map:
            raise ValueError(f"metric_type must be one of: {', '.join(fields_map.keys())}")

        params: dict[str, Any] = {
            "fields": fields_map[metric_type],
            "period": period,
            "limit": min(limit, 1000),
        }
        if interval:
            params["interval"] = interval
        return await self._request(f"metrics/{metric_type}", params)
