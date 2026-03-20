"""Forumbee REST API v2 client."""

import os
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv


class ForumbeeConfigError(Exception):
    """Raised when Forumbee configuration is missing or invalid."""


class ForumbeeClient:
    """Async client for the Forumbee REST API v2.

    'Async' means the client can wait for network responses without freezing
    everything else. You'll see 'async' and 'await' used throughout — just
    think of them as Python's way of saying 'go do this network thing, and
    come back when it's done'.
    """

    def __init__(self) -> None:
        # Look for a .env file in two possible locations: the mcp-server
        # directory itself, or the project root one level up. We try both
        # because the working directory can vary depending on how you run it.
        for candidate in [
            Path(__file__).resolve().parent.parent.parent / ".env",
            Path(__file__).resolve().parent.parent.parent.parent / ".env",
        ]:
            if candidate.exists():
                load_dotenv(candidate)
                break

        # Read credentials from environment variables (set in .env or the shell)
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

        # All API calls will be made to this base URL
        self.base_url = f"https://{self.domain}/api/2"

    async def _request(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make an authenticated GET request to the Forumbee API.

        The leading underscore in '_request' is a Python convention meaning
        'this is an internal helper — other code should use the public methods
        below rather than calling this directly'.
        """
        url = f"{self.base_url}/{endpoint}"
        # 'Bearer token' is a standard way to prove your identity to an API —
        # it's like showing a keycard on every request.
        headers = {"Authorization": f"Bearer {self.token}"}
        async with httpx.AsyncClient() as http:
            response = await http.get(url, headers=headers, params=params, timeout=30.0)
            if response.status_code == 401:
                raise ForumbeeConfigError("Invalid or expired API token. Check FORUMBEE_API_TOKEN in .env")
            response.raise_for_status()  # Raises an error for any other non-200 HTTP status
            return response.json()  # Parse the response body as JSON and return it as a dict

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
            "textFormat": "plain-truncate-200",  # Return plain text, truncated to 200 chars
            "search": query,
            "sort": "best",
            "limit": min(limit, 1000),  # Cap at 1000 — the API won't return more than that
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
            "textFormat": "plain-truncate-200",  # Return plain text, truncated to 200 chars
            "categoryLink": category,
            "postType": "topics",  # Only return top-level posts, not replies
            "sort": sort,
            "limit": min(limit, 1000),  # Cap at 1000 — the API won't return more than that
        }
        return await self._request("posts", params)

    async def get_post(self, post_key: str) -> dict[str, Any]:
        """Get full details for a specific post and its replies."""
        params: dict[str, Any] = {
            "fields": "postKey,parentKey,title,text,typeLabel,category.name,author.name,author.handle,posted,active,url,replyCount,likeCount,viewCount,followCount",
            "textFormat": "html",  # Return full HTML so attachments and formatting are preserved
            "topicKey": post_key,  # Fetch the topic and all its replies in one call
            "limit": 100,          # Return up to 100 replies
        }
        return await self._request("posts", params)

    async def get_metrics(
        self,
        metric_type: str,
        period: str = "30d",
        interval: str | None = None,
        limit: int = 25,
    ) -> dict[str, Any]:
        """Get community metrics (users, searches, topics, categories, pageviews)."""
        # Each metric type has a different set of fields available from the API.
        # This lookup table maps the metric name to the fields we want back,
        # so we don't have to use a long if/elif chain.
        fields_map = {
            "users": "date,period,users,page_views,joined,topic_posts,reply_posts,all_posts",
            "searches": "query,search_count,top_clicked_url",
            "topics": "topicKey,topicTitle,topicUrl,replies,likes,views,category",
            "categories": "categoryName,categoryType,categoryLink,topic_views,topic_likes,reply_posts,all_posts",
            "pageviews": "date,period,area,page_views",
        }
        if metric_type not in fields_map:
            raise ValueError(f"metric_type must be one of: {', '.join(fields_map.keys())}")

        params: dict[str, Any] = {
            "fields": fields_map[metric_type],
            "period": period,
            "limit": min(limit, 1000),  # Cap at 1000 — the API won't return more than that
        }
        if interval:
            params["interval"] = interval
        return await self._request(f"metrics/{metric_type}", params)

    async def list_users(
        self,
        search: str | None = None,
        sort: str = "joined",
        limit: int = 25,
    ) -> dict[str, Any]:
        """List community users."""
        params: dict[str, Any] = {
            "fields": "userKey,name,handle,email,role,label,joined,accessed,topics,replies,posts,likes,likesReceived,followers",
            "sort": sort,
            "limit": min(limit, 1000),  # Cap at 1000 — the API won't return more than that
        }
        if search:
            params["search"] = search
        return await self._request("users", params)

    async def get_category(self, category_link: str) -> dict[str, Any]:
        """Get details for a specific category."""
        return await self._request(f"category/{category_link}")

    async def list_category_followers(
        self,
        category_link: str,
        sort: str = "joined",
        limit: int = 25,
    ) -> dict[str, Any]:
        """List users who follow a category."""
        params: dict[str, Any] = {
            "fields": "userKey,name,handle,email,role,label,joined,accessed",
            "sort": sort,
            "limit": min(limit, 1000),  # Cap at 1000 — the API won't return more than that
        }
        return await self._request(f"categories/{category_link}/followers", params)

    async def list_category_security_users(
        self,
        category_link: str,
        sort: str = "joined",
        limit: int = 25,
    ) -> dict[str, Any]:
        """List users who have permission to access a category."""
        params: dict[str, Any] = {
            "fields": "userKey,name,handle,email,role,label,joined,accessed",
            "sort": sort,
            "limit": min(limit, 1000),  # Cap at 1000 — the API won't return more than that
        }
        return await self._request(f"categories/{category_link}/security/users", params)

    async def list_groups(self) -> dict[str, Any]:
        """List all security groups."""
        params = {
            "fields": "groupKey,groupName,groupType,role,userCount,userJoined,accessDomains",
        }
        return await self._request("groups", params)

    async def list_group_users(
        self,
        group_key: str,
        sort: str = "joined",
        limit: int = 25,
    ) -> dict[str, Any]:
        """List users in a security group."""
        params: dict[str, Any] = {
            "fields": "userKey,name,handle,email,role,label,joined,accessed,status",
            "sort": sort,
            "limit": min(limit, 1000),  # Cap at 1000 — the API won't return more than that
        }
        return await self._request(f"groups/{group_key}/users", params)
