# Forumbee MCP Server

An MCP (Model Context Protocol) server that provides tools for interacting with the [Forumbee](https://forumbee.com) community forum API v2. Gives AI assistants like Claude full read access to your community's posts, categories, users, groups, and analytics.

## Prerequisites

- Python 3.10+
- A Forumbee community with API access
- An API token ([how to generate one](https://community.forumbee.com/t/y72fnn/api-reference))

## Setup

```bash
cd mcp-server

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .
```

### Configuration

Copy the example env file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```
FORUMBEE_DOMAIN=your-community.forumbee.com
FORUMBEE_API_TOKEN=your_token_here
```

## Usage

### With Claude Code

Add to your Claude Code MCP settings (`~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "forumbee": {
      "command": "/path/to/mcp-server/.venv/bin/forumbee-mcp"
    }
  }
}
```

### With Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "forumbee": {
      "command": "/path/to/mcp-server/.venv/bin/forumbee-mcp"
    }
  }
}
```

### Run Directly

```bash
cd mcp-server
source .venv/bin/activate
forumbee-mcp
```

The server communicates over stdio using the MCP protocol.

## Available Tools

### Posts

| Tool | Description |
|---|---|
| `search_posts` | Search posts by keyword, with optional category and post type filters |
| `list_posts_in_category` | List topics in a category, sorted by activity, date, likes, etc. |
| `get_post` | Get full post details and all replies by post key |

### Categories

| Tool | Description |
|---|---|
| `list_categories` | List all forum categories with topic counts and activity info |
| `get_category` | Get details for a specific category by its URL slug |
| `list_category_followers` | List users who follow a category |
| `list_category_security_users` | List users with permission to access a category |

### Users & Groups

| Tool | Description |
|---|---|
| `list_users` | List or search community members |
| `list_groups` | List all security groups (UserGroups and DomainGroups) |
| `list_group_users` | List users in a specific security group |

### Analytics

| Tool | Description |
|---|---|
| `get_metrics` | Get community metrics for users, searches, topics, categories, or pageviews. Supports custom time periods and intervals. |

## Project Structure

```
mcp-server/
  src/forumbee_mcp/
    __init__.py       # Package metadata
    client.py         # Async Forumbee API v2 client
    server.py         # MCP server with tool definitions
  pyproject.toml      # Package config and dependencies
  .env.example        # Environment variable template
```
