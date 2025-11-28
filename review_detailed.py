"""
Detailed Review - Show full message context for every entry
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.environ.get("SUPABASE_URL", ""),
    os.environ.get("SUPABASE_KEY", "")
)


def review_all():
    """Show all entries with full context"""
    result = supabase.table("competitor_intel").select("*").order("id").execute()
    entries = result.data

    print(f"\n{'='*80}")
    print(f"FULL DATA REVIEW - {len(entries)} entries")
    print(f"{'='*80}")

    for entry in entries:
        entry_id = entry.get("id", "")
        competitor = entry.get("competitor", "")
        category = entry.get("category", "")
        url = entry.get("url", "")
        summary = entry.get("summary", "")

        # Flag if it might be a news source mistaken as competitor
        is_news_source = competitor in [
            "Fortune", "Cointelegraph", "Prnewswire", "Businesswire",
            "Ffnews", "Fintechnews", "Coinmarketcap", "Cryptobriefing",
            "Financemagnates", "Thepaypers", "Thecryptobasic", "Blockonomi",
            "Latamlist", "Newsroom", "Finance", "International", "Dune",
            "Coinlaw", "Fintechexpert", "Financialit", "Stableminded"
        ]

        needs_review = competitor.startswith("[Source:") or is_news_source

        if needs_review:
            status = "⚠️  NEEDS REVIEW"
        else:
            status = "✓"

        print(f"\n{'─'*80}")
        print(f"ID: {entry_id} | {status}")
        print(f"Current Competitor: {competitor}")
        print(f"Category: {category}")
        print(f"URL: {url[:70]}...")
        print(f"Message: {summary[:300]}...")

    print(f"\n{'='*80}")
    print(f"Review complete. Total: {len(entries)} entries")
    print(f"{'='*80}\n")


def review_needs_attention():
    """Show only entries that need review"""
    result = supabase.table("competitor_intel").select("*").order("id").execute()
    entries = result.data

    # News/media sources that shouldn't be competitors
    news_sources = {
        "Fortune", "Cointelegraph", "Prnewswire", "Businesswire",
        "Ffnews", "Fintechnews", "Coinmarketcap", "Cryptobriefing",
        "Financemagnates", "Thepaypers", "Thecryptobasic", "Blockonomi",
        "Latamlist", "Newsroom", "Finance", "International", "Dune",
        "Coinlaw", "Fintechexpert", "Financialit", "Stableminded",
        "Blockchain", "Pay", "Swap"
    }

    needs_review = []
    for entry in entries:
        competitor = entry.get("competitor", "")
        if competitor.startswith("[Source:") or competitor in news_sources:
            needs_review.append(entry)

    print(f"\n{'='*80}")
    print(f"ENTRIES NEEDING REVIEW - {len(needs_review)} of {len(entries)}")
    print(f"{'='*80}")

    for entry in needs_review:
        entry_id = entry.get("id", "")
        competitor = entry.get("competitor", "")
        category = entry.get("category", "")
        url = entry.get("url", "")
        summary = entry.get("summary", "")

        print(f"\n{'─'*80}")
        print(f"ID: {entry_id}")
        print(f"Current: {competitor}")
        print(f"Category: {category}")
        print(f"URL: {url}")
        print(f"\nFull Message:")
        print(f"{summary}")
        print(f"\n>>> What company is this ACTUALLY about? <<<")

    # Summary at end
    print(f"\n{'='*80}")
    print(f"SUMMARY OF ENTRIES NEEDING REVIEW:")
    print(f"{'='*80}")

    from collections import Counter
    counts = Counter(e["competitor"] for e in needs_review)
    for name, count in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {name}: {count}")

    print(f"\nTotal needing review: {len(needs_review)}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "all":
        review_all()
    else:
        review_needs_attention()
