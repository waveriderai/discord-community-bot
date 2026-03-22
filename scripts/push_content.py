#!/usr/bin/env python3
"""
Monitor WordPress posts and Podcast RSS feed for new content, then post
notifications to Discord.

Tracks last-seen IDs in .content_state.json to avoid duplicate posts.

Usage:
    python scripts/push_content.py
"""

import json
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import requests
from dotenv import load_dotenv

from lib.embeds import format_content_notification

load_dotenv()

WP_API_URL = "https://waverider.ai/wp-json/wp/v2/posts"
PODCAST_RSS_URL = "https://podcast.waverider.ai/feed/"
STATE_FILE = os.path.join(os.path.dirname(__file__), "..", ".content_state.json")


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"last_wp_id": 0, "last_podcast_guid": ""}


def save_state(state: dict) -> None:
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def post_webhook(webhook_url: str, payload: dict) -> None:
    resp = requests.post(webhook_url, json=payload, timeout=10)
    resp.raise_for_status()


def check_wordpress(state: dict) -> dict:
    """Check for new WordPress posts and post notifications."""
    webhook_url = os.environ.get("DISCORD_WEBHOOK_ANALYSIS")
    if not webhook_url:
        print("DISCORD_WEBHOOK_ANALYSIS not set, skipping WP check.")
        return state

    print("Checking WordPress for new posts...")
    try:
        resp = requests.get(
            WP_API_URL,
            params={"per_page": 5, "orderby": "date", "order": "desc"},
            timeout=15,
        )
        resp.raise_for_status()
        posts = resp.json()
    except Exception as e:
        print(f"WordPress fetch failed: {e}", file=sys.stderr)
        return state

    last_id = state.get("last_wp_id", 0)
    new_posts = [p for p in posts if p["id"] > last_id]

    if not new_posts:
        print("No new WordPress posts.")
        return state

    # Post oldest-first so newest is last in channel
    for post in reversed(new_posts):
        title = post.get("title", {}).get("rendered", "Untitled")
        url = post.get("link", "https://waverider.ai")
        payload = format_content_notification("analysis", title, url)
        try:
            post_webhook(webhook_url, payload)
            print(f"  Posted: {title}")
        except Exception as e:
            print(f"  Failed to post '{title}': {e}", file=sys.stderr)

    state["last_wp_id"] = max(p["id"] for p in new_posts)
    return state


def check_podcast(state: dict) -> dict:
    """Check for new podcast episodes from RSS and post notifications."""
    webhook_url = os.environ.get("DISCORD_WEBHOOK_PODCAST")
    if not webhook_url:
        print("DISCORD_WEBHOOK_PODCAST not set, skipping podcast check.")
        return state

    print("Checking Podcast RSS for new episodes...")
    try:
        resp = requests.get(PODCAST_RSS_URL, timeout=15)
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
    except Exception as e:
        print(f"Podcast RSS fetch failed: {e}", file=sys.stderr)
        return state

    items = root.findall(".//item")
    if not items:
        print("No podcast items found.")
        return state

    last_guid = state.get("last_podcast_guid", "")
    new_episodes = []
    for item in items:
        guid_el = item.find("guid")
        guid = guid_el.text if guid_el is not None else ""
        if guid == last_guid:
            break
        new_episodes.append(item)

    if not new_episodes:
        print("No new podcast episodes.")
        return state

    # Post oldest-first
    for item in reversed(new_episodes):
        title_el = item.find("title")
        link_el = item.find("link")
        title = title_el.text if title_el is not None else "New Episode"
        url = link_el.text if link_el is not None else "https://podcast.waverider.ai"
        payload = format_content_notification("podcast", title, url)
        try:
            post_webhook(webhook_url, payload)
            print(f"  Posted: {title}")
        except Exception as e:
            print(f"  Failed to post '{title}': {e}", file=sys.stderr)

    # Update state with newest guid
    newest_guid_el = new_episodes[0].find("guid")
    if newest_guid_el is not None:
        state["last_podcast_guid"] = newest_guid_el.text

    return state


def main() -> None:
    state = load_state()
    state = check_wordpress(state)
    state = check_podcast(state)
    save_state(state)
    print("Content check done.")


if __name__ == "__main__":
    main()
