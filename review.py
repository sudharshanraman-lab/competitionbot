"""
Review Script - Analyze competitor data and identify entries needing review
"""

import os
from collections import Counter
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.environ.get("SUPABASE_URL", ""),
    os.environ.get("SUPABASE_KEY", "")
)


def get_all_entries():
    """Fetch all entries from database"""
    result = supabase.table("competitor_intel").select("*").order("competitor").execute()
    return result.data


def analyze_data():
    """Analyze and categorize entries for review"""
    entries = get_all_entries()

    print(f"\n{'='*70}")
    print(f"COMPETITOR DATA REVIEW")
    print(f"{'='*70}")
    print(f"\nTotal entries: {len(entries)}")

    # Categorize entries
    needs_review = []  # [Source: X] entries
    verified = []      # Direct company links

    for entry in entries:
        competitor = entry.get("competitor", "")
        if competitor.startswith("[Source:"):
            needs_review.append(entry)
        else:
            verified.append(entry)

    print(f"Verified entries: {len(verified)}")
    print(f"Needs review: {len(needs_review)}")

    # Show unique competitors (verified)
    print(f"\n{'='*70}")
    print("VERIFIED COMPETITORS (appear correct)")
    print(f"{'='*70}")

    verified_counts = Counter(e["competitor"] for e in verified)
    for company, count in sorted(verified_counts.items(), key=lambda x: -x[1]):
        print(f"  {company}: {count} entries")

    # Show entries needing review
    print(f"\n{'='*70}")
    print("NEEDS REVIEW (source links - company not auto-detected)")
    print(f"{'='*70}")

    review_counts = Counter(e["competitor"] for e in needs_review)
    for source, count in sorted(review_counts.items(), key=lambda x: -x[1]):
        print(f"  {source}: {count} entries")

    # Show sample entries needing review with their summaries
    print(f"\n{'='*70}")
    print("SAMPLE ENTRIES NEEDING REVIEW (showing message text)")
    print(f"{'='*70}")

    for entry in needs_review[:20]:  # Show first 20
        competitor = entry.get("competitor", "")
        summary = entry.get("summary", "")[:150]
        url = entry.get("url", "")
        entry_id = entry.get("id", "")
        print(f"\n  ID: {entry_id}")
        print(f"  Current: {competitor}")
        print(f"  URL: {url[:60]}...")
        print(f"  Message: {summary}...")
        print(f"  ---")

    return entries, needs_review, verified


def update_competitor(entry_id: int, new_competitor: str):
    """Update a single entry's competitor name"""
    try:
        supabase.table("competitor_intel").update({
            "competitor": new_competitor
        }).eq("id", entry_id).execute()
        print(f"Updated ID {entry_id} -> {new_competitor}")
        return True
    except Exception as e:
        print(f"Error updating: {e}")
        return False


def bulk_update_by_source(source_name: str, new_competitor: str):
    """Update all entries with a specific source to a new competitor name"""
    try:
        result = supabase.table("competitor_intel").update({
            "competitor": new_competitor
        }).eq("competitor", source_name).execute()
        print(f"Updated all '{source_name}' -> '{new_competitor}'")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1:
        # Just analyze
        analyze_data()
        print(f"\n{'='*70}")
        print("TO UPDATE ENTRIES:")
        print("  Single:  python review.py update <id> <new_competitor>")
        print("  Bulk:    python review.py bulk '[Source: X]' 'ActualCompany'")
        print(f"{'='*70}\n")

    elif sys.argv[1] == "update" and len(sys.argv) == 4:
        # Update single entry
        entry_id = int(sys.argv[2])
        new_name = sys.argv[3]
        update_competitor(entry_id, new_name)

    elif sys.argv[1] == "bulk" and len(sys.argv) == 4:
        # Bulk update by source
        source = sys.argv[2]
        new_name = sys.argv[3]
        bulk_update_by_source(source, new_name)

    else:
        print("Usage:")
        print("  python review.py                           # Analyze data")
        print("  python review.py update <id> <name>        # Update single")
        print("  python review.py bulk '<source>' '<name>'  # Bulk update")
