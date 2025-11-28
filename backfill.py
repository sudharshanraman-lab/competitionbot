"""
Backfill Script - Import historical messages from Slack
Run this once to import existing competitor intel from #topic-competition
"""

import os
import time
from datetime import datetime

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize clients
slack_client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
supabase = create_client(
    os.environ.get("SUPABASE_URL", ""),
    os.environ.get("SUPABASE_KEY", "")
)

CHANNEL_NAME = os.environ.get("SLACK_CHANNEL_NAME", "topic-competition")

# Import helpers from main app
from app import (
    extract_domain,
    domain_to_company,
    get_company_name,
    detect_category,
    extract_urls,
    check_duplicate_url,
    build_slack_link
)


def get_channel_id(channel_name: str) -> str | None:
    """Find channel ID by name"""
    try:
        # Search both public and private channels with pagination
        cursor = None
        while True:
            result = slack_client.conversations_list(
                types="public_channel,private_channel",
                limit=200,
                cursor=cursor
            )
            for channel in result["channels"]:
                if channel["name"] == channel_name:
                    return channel["id"]

            # Check for more pages
            cursor = result.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
    except SlackApiError as e:
        print(f"Error finding channel: {e}")
        print(f"Needed scope: {e.response.get('needed', 'unknown')}")
        print(f"Provided scopes: {e.response.get('provided', 'unknown')}")
    return None


def get_user_name(user_id: str) -> str:
    """Get user's real name from ID"""
    try:
        result = slack_client.users_info(user=user_id)
        return result["user"]["real_name"]
    except Exception:
        return f"<@{user_id}>"


def backfill_channel(start_date: str = "2025-01-01"):
    """Fetch and process historical messages from channel."""

    print(f"\n{'='*60}")
    print(f"CompetitionBot Backfill Script")
    print(f"{'='*60}")

    # Find channel ID
    channel_id = get_channel_id(CHANNEL_NAME)
    if not channel_id:
        print(f"ERROR: Could not find channel #{CHANNEL_NAME}")
        return

    print(f"Found channel #{CHANNEL_NAME} (ID: {channel_id})")

    # Convert start date to timestamp
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    oldest_ts = str(start_dt.timestamp())

    print(f"Fetching messages since {start_date}...")

    # Fetch messages with pagination
    all_messages = []
    cursor = None

    while True:
        try:
            result = slack_client.conversations_history(
                channel=channel_id,
                oldest=oldest_ts,
                limit=200,
                cursor=cursor
            )

            messages = result.get("messages", [])
            all_messages.extend(messages)
            print(f"  Fetched {len(messages)} messages (total: {len(all_messages)})")

            if result.get("has_more"):
                cursor = result["response_metadata"]["next_cursor"]
                time.sleep(1)
            else:
                break

        except SlackApiError as e:
            print(f"ERROR fetching messages: {e}")
            break

    print(f"\nTotal messages fetched: {len(all_messages)}")

    # Filter messages with URLs
    url_messages = [
        msg for msg in all_messages
        if "http" in msg.get("text", "").lower()
        and not msg.get("bot_id")
    ]

    print(f"Messages containing URLs: {len(url_messages)}")

    # Process each message
    processed = 0
    duplicates = 0
    errors = 0

    print(f"\nProcessing messages...")

    for i, msg in enumerate(url_messages):
        text = msg.get("text", "")
        urls = extract_urls(text)

        if not urls:
            continue

        user_id = msg.get("user", "Unknown")
        user_name = get_user_name(user_id)

        ts = msg.get("ts", "")
        try:
            msg_date = datetime.fromtimestamp(float(ts)).strftime("%Y-%m-%d")
        except Exception:
            msg_date = datetime.now().strftime("%Y-%m-%d")

        for url in urls:
            if check_duplicate_url(url):
                duplicates += 1
                continue

            # Smart company detection - handles social media/news links
            company, source_type = get_company_name(url, text)
            category = detect_category(text)
            slack_link = build_slack_link(channel_id, ts)

            try:
                supabase.table("competitor_intel").insert({
                    "competitor": company,
                    "url": url,
                    "category": category,
                    "summary": text[:2000],
                    "shared_by": user_name,
                    "date_added": msg_date,
                    "slack_link": slack_link,
                }).execute()
                processed += 1
            except Exception as e:
                errors += 1
                print(f"  Error saving {company}: {e}")

        if (i + 1) % 10 == 0:
            print(f"  Progress: {i + 1}/{len(url_messages)} messages")

        time.sleep(0.3)

    print(f"\n{'='*60}")
    print(f"BACKFILL COMPLETE")
    print(f"{'='*60}")
    print(f"  Entries created: {processed}")
    print(f"  Duplicates skipped: {duplicates}")
    print(f"  Errors: {errors}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    import sys
    start_date = sys.argv[1] if len(sys.argv) > 1 else "2025-01-01"

    print(f"Starting backfill from {start_date}")
    print("Press Ctrl+C to cancel\n")

    try:
        backfill_channel(start_date=start_date)
    except KeyboardInterrupt:
        print("\nBackfill cancelled by user")
