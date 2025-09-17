from __future__ import annotations

import os
import sys
import json
from typing import List, Dict, Any

import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()  # Load .env if present

BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")
DEFAULT_MAX_PAGES = int(os.getenv("X_MAX_PAGES", "1"))

if not BEARER_TOKEN:
    print("Warning: X_BEARER_TOKEN not set. The get_user_tweets tool will fail until you configure it.", file=sys.stderr)

mcp = FastMCP("X Tweets")
@mcp.tool(
    name="get_user_tweets",
    description="Fetch tweets from a user's timeline.",
    tags={"tweets", "fetch"}
)
def get_user_tweets(username: str) -> List[Dict[str, Any]]:
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    base = os.getenv("X_BASE_URL", "https://api.x.com/2")
    params = {
        "max_results": int(os.getenv("X_MAX_RESULTS_PER_PAGE", "5")),
        "tweet.fields": "created_at,public_metrics",
    }
    # 1. Resolve username -> user id
    try:
        r = requests.get(f"{base}/users/by/username/{username}", headers=headers, timeout=10)
        if r.status_code == 404:
            return [{"error": f"User '{username}' not found"}]
        r.raise_for_status()
        user_id = r.json()["data"]["id"]
    except requests.RequestException as e:
        return [{"error": f"Failed to fetch user: {e}"}]
    except KeyError:
        return [{"error": "Unexpected response structure when resolving username"}]

    # 2. Fetch tweets with pagination
    tweets: List[Dict[str, Any]] = []
    next_token: str | None = None
    for _ in range(DEFAULT_MAX_PAGES):
        if next_token:
            params["pagination_token"] = next_token
        try:
            r = requests.get(f"{base}/users/{user_id}/tweets", headers=headers, params=params, timeout=15)
            r.raise_for_status()
            data = r.json()
        except requests.RequestException as e:
            tweets.append({"error": f"Request failed: {e}"})
            break
        except json.JSONDecodeError:
            tweets.append({"error": "Invalid JSON in tweets response"})
            break

        batch = data.get("data", [])
        if not isinstance(batch, list):
            tweets.append({"error": "Unexpected 'data' field shape"})
            break

        # Keep only selected fields
        for t in batch:
            tweets.append({
                "id": t.get("id"),
                "text": t.get("text"),
                "created_at": t.get("created_at")
            })

        meta = data.get("meta", {})
        next_token = meta.get("next_token")
        if not next_token:
            break

    return tweets


if __name__ == "__main__":  # pragma: no cover
    mcp.run(transport='stdio')
