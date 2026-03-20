# Forumbee MCP Server Design

## Overview

A Python MCP server that exposes Forumbee community forum data as tools usable in Claude Code and Claude Desktop. Configurable for any Forumbee community via environment variables.

## Configuration

`.env` file at project root with:

```
FORUMBEE_DOMAIN=your-community.forumbee.com
FORUMBEE_API_TOKEN=your_token_here
```

A `.env.example` is committed as a template. `.env` is gitignored.

Config is validated at startup (fail fast if missing). No test connection at launch — first tool call validates connectivity.

## Project Structure

```
board-forum/
├── api-docs/                          # Forumbee API reference
├── docs/plans/                        # Design docs
├── mcp-server/
│   ├── pyproject.toml                 # Dependencies: mcp, httpx, python-dotenv
│   ├── src/
│   │   └── forumbee_mcp/
│   │       ├── __init__.py
│   │       ├── server.py              # MCP server definition & tool handlers
│   │       └── client.py              # Forumbee API client (HTTP calls)
│   └── .env.example                   # Template for configuration
├── .env                               # Actual config (gitignored)
├── .gitignore
```

Dependencies: `mcp` (Python MCP SDK), `httpx` (async HTTP), `python-dotenv`.

## Tools

### forumbee_search

Search posts by keyword with optional filters.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| query | string | yes | - | Search terms |
| category | string | no | - | Filter by category link/key |
| post_type | string | no | - | topics, replies, questions, ideas, articles, etc. |
| limit | int | no | 25 | Max results (up to 1000) |

Returns summary list: title, author, category, date, post URL, truncated text (plain-truncate-200). Results sorted by `best` (search relevancy).

### forumbee_browse_category

List categories or topics within a category.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| category | string | no | - | If provided, lists topics in that category. If omitted, lists all categories. |
| sort | string | no | active | posted, active, likes, replies, views |
| limit | int | no | 25 | Max results |

Returns category list (name, type, topic count) OR topic list (title, author, date, reply count, URL).

### forumbee_get_post

Fetch full detail for a specific post.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| post_key | string | yes | The post key to retrieve |

Returns full post content (HTML), author info, reply count, likes, views, URL.

### forumbee_metrics

Community analytics.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| metric_type | string | yes | - | users, searches, or topics |
| period | string | no | 30d | Time period (e.g., 7d, 90d, 2025-01) |
| interval | string | no | - | Group by d, w, m, etc. |
| limit | int | no | 25 | Max results |

Returns metric-specific data (user activity, search queries, topic engagement).

## Error Handling

- **Missing config** - Clear error pointing to .env.example
- **Auth failures (401)** - "Invalid or expired API token"
- **Not found (404)** - "Post/category not found"
- **Rate limiting / server errors** - Pass through status code and error message

No retries or complex recovery.

## Server Configuration

stdio transport, launched via `uv run`:

```json
{
  "mcpServers": {
    "forumbee": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/board-forum/mcp-server", "forumbee-mcp"]
    }
  }
}
```

## Future Work

- `forumbee_reply` tool for posting replies to topics
- User search tool
