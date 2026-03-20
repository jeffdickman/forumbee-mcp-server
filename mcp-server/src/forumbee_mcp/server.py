from mcp.server.fastmcp import FastMCP

from forumbee_mcp.client import ForumbeeClient

mcp = FastMCP("forumbee")


def _client() -> ForumbeeClient:
    return ForumbeeClient()


@mcp.tool()
async def search_posts(
    query: str,
    category: str | None = None,
    post_type: str | None = None,
    limit: int = 25,
) -> dict:
    """Search community posts by keyword.

    Args:
        query: Search query string.
        category: Optional category link to filter by.
        post_type: Optional post type filter (topics, replies, discussions, questions, ideas, issues, articles, events).
        limit: Max results to return (default 25, max 1000).
    """
    return await _client().search_posts(query, category, post_type, limit)


@mcp.tool()
async def list_categories() -> dict:
    """List all forum categories with topic counts and activity info."""
    return await _client().list_categories()


@mcp.tool()
async def get_category(category_link: str) -> dict:
    """Get details for a specific category.

    Args:
        category_link: The category URL slug (e.g. 'general-discussion').
    """
    return await _client().get_category(category_link)


@mcp.tool()
async def list_posts_in_category(
    category: str,
    sort: str = "active",
    limit: int = 25,
) -> dict:
    """List topics in a specific category.

    Args:
        category: Category link/slug to list posts from.
        sort: Sort order - one of: posted, active, updated, likes, replies, views, follows, alpha, manual.
        limit: Max results to return (default 25, max 1000).
    """
    return await _client().list_posts_in_category(category, sort, limit)


@mcp.tool()
async def get_post(post_key: str) -> dict:
    """Get full details for a post and its replies.

    Args:
        post_key: The unique post key identifier.
    """
    return await _client().get_post(post_key)


@mcp.tool()
async def get_metrics(
    metric_type: str,
    period: str = "30d",
    interval: str | None = None,
    limit: int = 25,
) -> dict:
    """Get community analytics metrics.

    Args:
        metric_type: Type of metrics - one of: users, searches, topics, categories, pageviews.
        period: Time period (e.g. '30d', '7d', '1m', '1y', or absolute like '2024-01-01--2024-01-31').
        interval: Optional grouping interval (h=hourly, d=daily, w=weekly, m=monthly, y=yearly).
        limit: Max results to return (default 25, max 1000).
    """
    return await _client().get_metrics(metric_type, period, interval, limit)


@mcp.tool()
async def list_users(
    search: str | None = None,
    sort: str = "joined",
    limit: int = 25,
) -> dict:
    """List community members.

    Args:
        search: Optional search query to filter users by name, handle, or email.
        sort: Sort order - one of: joined, accessed, name, posts, followers. Prefix with '-' to reverse.
        limit: Max results to return (default 25, max 1000).
    """
    return await _client().list_users(search, sort, limit)


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
