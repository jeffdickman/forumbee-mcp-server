# Forumbee MCP Server Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python MCP server that exposes Forumbee community forum data as tools for Claude Code and Claude Desktop.

**Architecture:** A FastMCP-based Python server with 4 tools (search, browse, get_post, metrics). An async httpx client handles Forumbee REST API v2 calls. Configuration via .env file with domain and token.

**Tech Stack:** Python 3.10+, `mcp[cli]` (FastMCP), `httpx`, `python-dotenv`, `uv` for project management.

---

### Task 1: Project Scaffolding

**Files:**
- Create: `mcp-server/pyproject.toml`
- Create: `mcp-server/src/forumbee_mcp/__init__.py`
- Create: `mcp-server/src/forumbee_mcp/server.py` (stub)
- Create: `mcp-server/src/forumbee_mcp/client.py` (stub)
- Create: `mcp-server/.env.example`
- Create: `.env` (from example, with real values — gitignored)
- Modify: `.gitignore`

**Step 1: Install uv**

Run: `curl -LsSf https://astral.sh/uv/install.sh | sh`
Then restart shell or `source ~/.zshrc`

**Step 2: Initialize the project**

Run:
```bash
cd /Users/jeffdickman/repos/personal/board-forum
mkdir -p mcp-server/src/forumbee_mcp
```

**Step 3: Create pyproject.toml**

Create `mcp-server/pyproject.toml`:
```toml
[project]
name = "forumbee-mcp"
version = "0.1.0"
description = "MCP server for Forumbee community forums"
requires-python = ">=3.10"
dependencies = [
    "mcp[cli]",
    "httpx",
    "python-dotenv",
]

[project.scripts]
forumbee-mcp = "forumbee_mcp.server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**Step 4: Create .env.example**

Create `mcp-server/.env.example`:
```
FORUMBEE_DOMAIN=your-community.forumbee.com
FORUMBEE_API_TOKEN=your_token_here
```

**Step 5: Create .gitignore**

Create `.gitignore` (or append to existing):
```
.env
__pycache__/
*.pyc
.venv/
```

**Step 6: Create .env with real values**

Create `.env` at project root:
```
FORUMBEE_DOMAIN=thepondhoa.forumbee.com
FORUMBEE_API_TOKEN=<your actual token>
```

**Step 7: Create __init__.py**

Create `mcp-server/src/forumbee_mcp/__init__.py`:
```python
"""Forumbee MCP Server - MCP tools for Forumbee community forums."""
```

**Step 8: Create stub server.py**

Create `mcp-server/src/forumbee_mcp/server.py`:
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("forumbee")


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
```

**Step 9: Create stub client.py**

Create `mcp-server/src/forumbee_mcp/client.py`:
```python
"""Forumbee API client."""
```

**Step 10: Install dependencies and verify server starts**

Run:
```bash
cd /Users/jeffdickman/repos/personal/board-forum/mcp-server
uv sync
```

Then verify the server can at least import and start:
```bash
cd /Users/jeffdickman/repos/personal/board-forum/mcp-server
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1.0"}}}' | uv run forumbee-mcp
```
Expected: JSON response with server capabilities (may include error output after, since stdin closes).

**Step 11: Commit**

```bash
git init  # if not already a repo
git add mcp-server/ .gitignore
git commit -m "feat: scaffold forumbee MCP server project"
```

---

### Task 2: Forumbee API Client

**Files:**
- Create: `mcp-server/src/forumbee_mcp/client.py`

**Step 1: Implement the ForumbeeClient class**

Create `mcp-server/src/forumbee_mcp/client.py`:
```python
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
        env_path = Path(__file__).resolve().parent.parent.parent / ".env.example"
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
```

**Step 2: Verify it imports**

Run:
```bash
cd /Users/jeffdickman/repos/personal/board-forum/mcp-server
uv run python -c "from forumbee_mcp.client import ForumbeeClient; print('OK')"
```
Expected: `OK`

**Step 3: Commit**

```bash
git add mcp-server/src/forumbee_mcp/client.py
git commit -m "feat: add Forumbee API client"
```

---

### Task 3: Implement MCP Tools

**Files:**
- Modify: `mcp-server/src/forumbee_mcp/server.py`

**Step 1: Implement all 4 tools in server.py**

Replace `mcp-server/src/forumbee_mcp/server.py` with:
```python
"""Forumbee MCP Server — exposes Forumbee community data as MCP tools."""

import json
import sys

from mcp.server.fastmcp import FastMCP

from .client import ForumbeeClient, ForumbeeConfigError

mcp = FastMCP("forumbee")

try:
    client = ForumbeeClient()
except ForumbeeConfigError as e:
    print(f"Forumbee MCP: {e}", file=sys.stderr)
    client = None


def _error(msg: str) -> str:
    return json.dumps({"error": msg})


@mcp.tool()
async def forumbee_search(
    query: str,
    category: str | None = None,
    post_type: str | None = None,
    limit: int = 25,
) -> str:
    """Search the Forumbee community forum for posts matching a query.

    Args:
        query: Search terms to find matching posts.
        category: Optional category link/key to filter results (e.g. "announcements").
        post_type: Optional post type filter. One of: topics, replies, questions, ideas, articles, events.
        limit: Maximum number of results to return (default 25, max 1000).
    """
    if not client:
        return _error("Forumbee not configured. Set FORUMBEE_DOMAIN and FORUMBEE_API_TOKEN in .env")
    try:
        data = await client.search_posts(query, category, post_type, limit)
        return json.dumps(data, indent=2, default=str)
    except Exception as e:
        return _error(str(e))


@mcp.tool()
async def forumbee_browse_category(
    category: str | None = None,
    sort: str = "active",
    limit: int = 25,
) -> str:
    """Browse Forumbee community categories or list topics within a category.

    If no category is specified, returns the list of all categories.
    If a category is specified, returns topics in that category.

    Args:
        category: Optional category link/key. Omit to list all categories.
        sort: Sort order for topics: posted, active, likes, replies, views (default: active).
        limit: Maximum number of results to return (default 25, max 1000).
    """
    if not client:
        return _error("Forumbee not configured. Set FORUMBEE_DOMAIN and FORUMBEE_API_TOKEN in .env")
    try:
        if category:
            data = await client.list_posts_in_category(category, sort, limit)
        else:
            data = await client.list_categories()
        return json.dumps(data, indent=2, default=str)
    except Exception as e:
        return _error(str(e))


@mcp.tool()
async def forumbee_get_post(post_key: str) -> str:
    """Get the full content of a specific Forumbee post and its replies.

    Args:
        post_key: The unique post key identifier.
    """
    if not client:
        return _error("Forumbee not configured. Set FORUMBEE_DOMAIN and FORUMBEE_API_TOKEN in .env")
    try:
        data = await client.get_post(post_key)
        return json.dumps(data, indent=2, default=str)
    except Exception as e:
        return _error(str(e))


@mcp.tool()
async def forumbee_metrics(
    metric_type: str,
    period: str = "30d",
    interval: str | None = None,
    limit: int = 25,
) -> str:
    """Get community analytics and metrics from Forumbee.

    Args:
        metric_type: Type of metrics to retrieve. One of: users, searches, topics.
        period: Time period for the analysis (default "30d"). Examples: 7d, 90d, 2025-01, 2025-jan-01--2025-mar-01.
        interval: Optional grouping interval: h (hourly), d (daily), w (weekly), m (monthly), y (yearly).
        limit: Maximum number of results to return (default 25, max 1000).
    """
    if not client:
        return _error("Forumbee not configured. Set FORUMBEE_DOMAIN and FORUMBEE_API_TOKEN in .env")
    try:
        data = await client.get_metrics(metric_type, period, interval, limit)
        return json.dumps(data, indent=2, default=str)
    except Exception as e:
        return _error(str(e))


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
```

**Step 2: Verify server starts with tools registered**

Run:
```bash
cd /Users/jeffdickman/repos/personal/board-forum/mcp-server
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1.0"}}}' | uv run forumbee-mcp
```
Expected: JSON response containing server info.

**Step 3: Commit**

```bash
git add mcp-server/src/forumbee_mcp/server.py
git commit -m "feat: implement forumbee MCP tools (search, browse, get_post, metrics)"
```

---

### Task 4: Live API Test

**Step 1: Create .env with real credentials**

Ensure `/Users/jeffdickman/repos/personal/board-forum/.env` exists with:
```
FORUMBEE_DOMAIN=thepondhoa.forumbee.com
FORUMBEE_API_TOKEN=<real token>
```

**Step 2: Test search_posts via a quick Python script**

Run:
```bash
cd /Users/jeffdickman/repos/personal/board-forum/mcp-server
uv run python -c "
import asyncio
from forumbee_mcp.client import ForumbeeClient

async def test():
    c = ForumbeeClient()
    result = await c.list_categories()
    import json
    print(json.dumps(result, indent=2, default=str)[:500])

asyncio.run(test())
"
```
Expected: JSON with category data from thepondhoa.forumbee.com.

**Step 3: Test search**

Run:
```bash
cd /Users/jeffdickman/repos/personal/board-forum/mcp-server
uv run python -c "
import asyncio
from forumbee_mcp.client import ForumbeeClient

async def test():
    c = ForumbeeClient()
    result = await c.search_posts('pool')
    import json
    print(json.dumps(result, indent=2, default=str)[:500])

asyncio.run(test())
"
```
Expected: JSON with posts matching "pool" (or whatever term is relevant).

**Step 4: Fix any issues discovered during testing**

If API responses differ from expected structure, adjust field names in client.py accordingly.

---

### Task 5: Configure MCP Server for Claude

**Step 1: Add MCP server config for Claude Code**

The user needs to add to their Claude Code MCP settings (via `claude mcp add` or editing config):

```bash
claude mcp add forumbee -- uv --directory /Users/jeffdickman/repos/personal/board-forum/mcp-server run forumbee-mcp
```

**Step 2: Verify the tools appear**

Restart Claude Code and verify the 4 forumbee tools are available.

**Step 3: Test a tool invocation through Claude**

Ask Claude: "Search the Forumbee forum for posts about pool" and verify it calls forumbee_search.

**Step 4: Commit any final adjustments**

```bash
git add -A
git commit -m "feat: finalize forumbee MCP server configuration"
```

---

### Task 6: Documentation

**Files:**
- Create: `mcp-server/README.md`

**Step 1: Write README**

Create `mcp-server/README.md` with:
- What the server does
- Setup instructions (uv, .env, MCP config)
- Available tools with descriptions
- Example usage

**Step 2: Commit**

```bash
git add mcp-server/README.md
git commit -m "docs: add README for forumbee MCP server"
```
