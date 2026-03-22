#!/usr/bin/env python3
"""
Fetch market breadth from WaveFinder API and post a Market Pulse embed
to the Discord webhook.

Usage:
    python scripts/push_market_pulse.py [--time-label "2:30 PM ET"]
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import requests
from dotenv import load_dotenv

from lib.embeds import format_market_pulse

load_dotenv()

WAVEFINDER_BREADTH_URL = "http://173.230.145.71:8000/api/v1/market-breadth"


def fetch_breadth() -> dict:
    """Fetch breadth data from WaveFinder API."""
    resp = requests.get(WAVEFINDER_BREADTH_URL, timeout=15)
    resp.raise_for_status()
    return resp.json()


def post_webhook(webhook_url: str, payload: dict) -> None:
    """Post JSON payload to a Discord webhook."""
    resp = requests.post(webhook_url, json=payload, timeout=10)
    resp.raise_for_status()


def main() -> None:
    parser = argparse.ArgumentParser(description="Push Market Pulse to Discord")
    parser.add_argument(
        "--time-label",
        default="",
        help='Time label to show in embed, e.g. "2:30 PM ET"',
    )
    args = parser.parse_args()

    webhook_url = os.environ.get("DISCORD_WEBHOOK_MARKET_PULSE")
    if not webhook_url:
        print("ERROR: DISCORD_WEBHOOK_MARKET_PULSE not set", file=sys.stderr)
        sys.exit(1)

    print("Fetching breadth data...")
    data = fetch_breadth()

    payload = format_market_pulse(data, time_label=args.time_label)
    print(f"Posting Market Pulse ({args.time_label or 'no label'})...")
    post_webhook(webhook_url, payload)
    print("Done.")


if __name__ == "__main__":
    main()
