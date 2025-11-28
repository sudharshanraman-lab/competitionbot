"""
Monthly Report Generator - Creates competitor intel summary
Outputs to Slack (copy/paste to Notion)
"""

import os
from datetime import datetime, timedelta
from collections import Counter

from slack_sdk import WebClient
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Initialize clients
slack_client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
supabase = create_client(
    os.environ.get("SUPABASE_URL", ""),
    os.environ.get("SUPABASE_KEY", "")
)

CHANNEL_NAME = os.environ.get("SLACK_CHANNEL_NAME", "topic-competition")


def get_channel_id(channel_name: str) -> str | None:
    """Find channel ID by name"""
    try:
        result = slack_client.conversations_list(types="public_channel,private_channel")
        for channel in result["channels"]:
            if channel["name"] == channel_name:
                return channel["id"]
    except Exception:
        pass
    return None


def generate_monthly_report(year: int = None, month: int = None) -> str:
    """Generate a monthly competitor intel report."""

    # Default to last month
    if year is None or month is None:
        today = datetime.now()
        first_of_month = today.replace(day=1)
        last_month = first_of_month - timedelta(days=1)
        year = last_month.year
        month = last_month.month

    # Date range for the month
    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{month + 1:02d}-01"

    month_name = datetime(year, month, 1).strftime("%B %Y")

    # Fetch ALL entries (for total count)
    try:
        all_result = supabase.table("competitor_intel").select("*").execute()
        all_entries = all_result.data
    except Exception as e:
        return f"Error fetching data: {e}"

    # Fetch THIS MONTH's entries
    try:
        month_result = supabase.table("competitor_intel")\
            .select("*")\
            .gte("date_added", start_date)\
            .lt("date_added", end_date)\
            .order("date_added", desc=True)\
            .execute()
        month_entries = month_result.data
    except Exception as e:
        return f"Error fetching data: {e}"

    # Calculate totals
    total_all_time = len(all_entries)
    total_this_month = len(month_entries)

    # Get all unique competitors (all time)
    all_competitors = set(e["competitor"] for e in all_entries
                         if not e["competitor"].startswith("[")
                         and e["competitor"] not in ["Unknown", "Market Overview"])
    total_competitors_tracked = len(all_competitors)

    # Get NEW competitors this month (first time appearing)
    previous_entries = [e for e in all_entries if e["date_added"] < start_date]
    previous_competitors = set(e["competitor"] for e in previous_entries)
    new_competitors_this_month = [
        e["competitor"] for e in month_entries
        if e["competitor"] not in previous_competitors
        and not e["competitor"].startswith("[")
        and e["competitor"] not in ["Unknown", "Market Overview"]
    ]
    new_competitors_unique = list(set(new_competitors_this_month))

    if not month_entries:
        return f"No competitor intel captured for {month_name}"

    # Count by competitor (this month)
    competitor_counts = Counter(e["competitor"] for e in month_entries
                               if not e["competitor"].startswith("[")
                               and e["competitor"] not in ["Unknown", "Market Overview"])
    top_competitors = competitor_counts.most_common(10)

    # Count by category
    category_counts = Counter(e["category"] for e in month_entries)

    # Group entries by category
    by_category = {}
    for entry in month_entries:
        cat = entry["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(entry)

    # Build report
    lines = [
        f"*Competitor Intelligence Report - {month_name}*",
        "=" * 50,
        "",
        "*Overview*",
        f"• *Total competitors tracked (since Jan 2025):* {total_competitors_tracked}",
        f"• *Total updates (since Jan 2025):* {total_all_time}",
        f"• *Updates this month:* {total_this_month}",
        "",
    ]

    # New competitors this month
    if new_competitors_unique:
        lines.append(f"*:new: New Competitors This Month* ({len(new_competitors_unique)})")
        for comp in new_competitors_unique[:10]:
            lines.append(f"  • {comp}")
        if len(new_competitors_unique) > 10:
            lines.append(f"  _...and {len(new_competitors_unique) - 10} more_")
        lines.append("")

    # Most active competitors this month
    if top_competitors:
        lines.append("*:fire: Most Active Competitors This Month*")
        for company, count in top_competitors[:5]:
            lines.append(f"  • {company}: {count} updates")
        lines.append("")

    # Category breakdown with details
    lines.append("*Updates By Category*")
    category_emojis = {
        "Product Launch": "rocket",
        "Funding": "moneybag",
        "Feature": "sparkles",
        "Acquisition": "handshake",
        "Partnership": "link",
        "Pricing": "chart_with_upwards_trend",
        "News": "newspaper",
        "Other": "file_folder",
    }

    # Sort categories by importance
    category_order = ["Funding", "Acquisition", "Product Launch", "Partnership", "Feature", "Pricing", "News", "Other"]
    sorted_categories = sorted(category_counts.items(),
                               key=lambda x: (category_order.index(x[0]) if x[0] in category_order else 99, -x[1]))

    for category, count in sorted_categories:
        emoji = category_emojis.get(category, "file_folder")
        lines.append(f"\n:{emoji}: *{category}* ({count})")

        # List entries for this category
        category_entries = by_category.get(category, [])[:5]
        for entry in category_entries:
            competitor = entry["competitor"]
            url = entry["url"]
            if not competitor.startswith("[") and competitor not in ["Unknown", "Market Overview"]:
                lines.append(f"  • {competitor}: <{url}|Link>")

        if len(by_category.get(category, [])) > 5:
            remaining = len(by_category[category]) - 5
            lines.append(f"  _...and {remaining} more_")

    # Executive Summary
    lines.append("")
    lines.append("─" * 40)
    lines.append("*Executive Summary*")
    lines.append(f"This month we tracked *{total_this_month} updates* across *{len(competitor_counts)} competitors*.")

    if new_competitors_unique:
        lines.append(f"*{len(new_competitors_unique)} new competitors* appeared on our radar: {', '.join(new_competitors_unique[:5])}{'...' if len(new_competitors_unique) > 5 else ''}.")

    if top_competitors:
        top_3 = [f"{c}" for c, _ in top_competitors[:3]]
        lines.append(f"Most active: *{', '.join(top_3)}*.")

    # Key highlights by category
    highlights = []
    if category_counts.get("Funding", 0) > 0:
        highlights.append(f"{category_counts['Funding']} funding announcements")
    if category_counts.get("Acquisition", 0) > 0:
        highlights.append(f"{category_counts['Acquisition']} acquisitions")
    if category_counts.get("Product Launch", 0) > 0:
        highlights.append(f"{category_counts['Product Launch']} product launches")
    if category_counts.get("Partnership", 0) > 0:
        highlights.append(f"{category_counts['Partnership']} partnerships")

    if highlights:
        lines.append(f"Key activity: {', '.join(highlights)}.")

    lines.append("")
    lines.append("_Generated by CompetitionBot_")

    return "\n".join(lines)


def post_report_to_slack(report: str, channel_id: str = None):
    """Post the report to Slack channel."""

    if channel_id is None:
        channel_id = get_channel_id(CHANNEL_NAME)

    if not channel_id:
        print(f"Could not find channel #{CHANNEL_NAME}")
        return

    try:
        slack_client.chat_postMessage(
            channel=channel_id,
            text=report,
            unfurl_links=False
        )
        print(f"Report posted to #{CHANNEL_NAME}")
    except Exception as e:
        print(f"Error posting to Slack: {e}")


def main():
    """Generate and optionally post monthly report."""
    import sys

    # Parse arguments
    post_to_slack = "--post" in sys.argv

    # Check for specific month (YYYY-MM format)
    year = None
    month = None
    for arg in sys.argv[1:]:
        if "-" in arg and arg != "--post":
            try:
                parts = arg.split("-")
                year = int(parts[0])
                month = int(parts[1])
            except Exception:
                pass

    print("Generating monthly report...")
    report = generate_monthly_report(year, month)

    print("\n" + "=" * 60)
    print(report)
    print("=" * 60 + "\n")

    if post_to_slack:
        print("Posting to Slack...")
        post_report_to_slack(report)
    else:
        print("To post to Slack, run: python report.py --post")
        print("To generate for a specific month: python report.py 2025-01")


if __name__ == "__main__":
    main()
