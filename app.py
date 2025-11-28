"""
CompetitionBot - Slack bot for tracking competitor intelligence
Monitors #topic-competition channel, extracts URLs, saves to Supabase
"""

import os
import re
from datetime import datetime
from urllib.parse import urlparse

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Slack app
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

# Initialize Supabase client
supabase: Client = create_client(
    os.environ.get("SUPABASE_URL", ""),
    os.environ.get("SUPABASE_KEY", "")
)

# Configuration
CHANNEL_NAME = os.environ.get("SLACK_CHANNEL_NAME", "topic-competition")

# Known company domain mappings (add your competitors here)
COMPANY_MAPPINGS = {
    # Tech giants
    "google.com": "Google",
    "microsoft.com": "Microsoft",
    "apple.com": "Apple",
    "amazon.com": "Amazon",
    "meta.com": "Meta",
    "facebook.com": "Meta",

    # Fintech
    "stripe.com": "Stripe",
    "paypal.com": "PayPal",
    "square.com": "Square",
    "plaid.com": "Plaid",
    "brex.com": "Brex",
    "ramp.com": "Ramp",
    "mercury.com": "Mercury",
    "wise.com": "Wise",
    "airwallex.com": "Airwallex",

    # Productivity
    "notion.so": "Notion",
    "notion.com": "Notion",
    "slack.com": "Slack",
    "figma.com": "Figma",
    "linear.app": "Linear",
    "asana.com": "Asana",
    "monday.com": "Monday.com",
    "airtable.com": "Airtable",

    # Dev tools
    "github.com": "GitHub",
    "gitlab.com": "GitLab",
    "vercel.com": "Vercel",
    "netlify.com": "Netlify",
    "supabase.com": "Supabase",

    # Crypto/Stablecoin companies
    "circle.com": "Circle",
    "bvnk.com": "BVNK",
    "zerohash.com": "ZeroHash",
    "fireblocks.com": "Fireblocks",
    "moonpay.com": "Moonpay",
    "bridge.xyz": "Bridge",
    "anchorage.com": "Anchorage",
    "crypto.com": "Crypto.com",
    "coinbase.com": "Coinbase",
    "exodus.com": "Exodus",
    "crossmint.com": "Crossmint",
    "hashkey.com": "Hashkey",
    "ripple.com": "Ripple",

    # Payments/Fintech
    "revolut.com": "Revolut",
    "adyen.com": "Adyen",
    "visa.com": "Visa",
    "mastercard.com": "Mastercard",
    "paypal.com": "PayPal",
    "klarna.com": "Klarna",
    "wise.com": "Wise",
    "nubank.com.br": "Nubank",
    "marqeta.com": "Marqeta",
    "paysafe.com": "Paysafe",
    "payoneer.com": "Payoneer",
    "shift4.com": "Shift4",
    "moderntreasury.com": "Modern Treasury",
    "finix.com": "Finix",
    "block.xyz": "Square",
    "squareup.com": "Square",
    "thunes.com": "Thunes",
    "terrapay.com": "TerraPay",

    # Regional players
    "rain.xyz": "Rain",
    "raincards.xyz": "Rain",
    "conduit.financial": "Conduit",
    "straitsx.com": "StraitsX",
    "karsa.io": "Karsa",
    "tryjeeves.com": "Jeeves",
    "wirexapp.com": "Wirex",
    "palmpay.com": "PalmPay",
    "felixpago.com": "Felix Pago",
    "dolarapp.com": "DolarApp",
    "m-pesa.com": "M-Pesa",
    "safaricom.co.ke": "M-Pesa",
    "alipay.com": "AliPay",
    "tempo.eu.com": "Tempo",
    "idrx.co": "IDRX",
    "tria.so": "Tria",
    "socgen.com": "Societe Generale",
    "sc.com": "Standard Chartered",
    "walmart.com": "Walmart",

    # Add more as needed...
}

# Source domains - these are NOT competitors, they're where news is shared
# When a URL is from these domains, we try to extract company from message text
SOURCE_DOMAINS = {
    # Social media
    "x.com", "twitter.com", "linkedin.com", "facebook.com", "instagram.com",
    "threads.net", "bsky.app", "mastodon.social",

    # News/Media sites
    "techcrunch.com", "bloomberg.com", "reuters.com", "cnbc.com", "ft.com",
    "wsj.com", "forbes.com", "businessinsider.com", "theverge.com",
    "wired.com", "arstechnica.com", "venturebeat.com", "sifted.eu",
    "scmp.com", "cnn.com", "bbc.com", "nytimes.com",
    "news.bitcoin.com", "coindesk.com", "theblock.co", "decrypt.co",
    "technode.global", "techinasia.com", "e27.co", "dealstreetasia.com",
    "fintechmagazine.com", "finextra.com", "pymnts.com",
    "asianbankingandfinance.net", "ledgerinsights.com",

    # Video platforms
    "youtube.com", "youtu.be", "vimeo.com", "tiktok.com",

    # Other aggregators
    "medium.com", "substack.com", "reddit.com", "news.ycombinator.com",
}

def is_source_domain(domain: str) -> bool:
    """Check if domain is a news/social source (not a competitor)"""
    # Check exact match
    if domain in SOURCE_DOMAINS:
        return True
    # Check if subdomain of a source (e.g., blog.twitter.com)
    for source in SOURCE_DOMAINS:
        if domain.endswith("." + source):
            return True
    return False

def extract_company_from_text(text: str) -> str | None:
    """Try to extract company name from message text using known mappings"""
    text_lower = text.lower()

    # Check if any known company is mentioned in the text
    for domain, company in COMPANY_MAPPINGS.items():
        company_lower = company.lower()
        # Look for company name in text (with word boundaries)
        if company_lower in text_lower:
            return company

    # Also check for common company name patterns in the text
    # (This catches companies not in our mapping)
    return None

# Category detection keywords
CATEGORY_KEYWORDS = {
    "Product Launch": [
        "launch", "launching", "announcing", "introducing",
        "new product", "release", "releasing", "now available", "just shipped",
        "we're excited to announce"
    ],
    "Funding": [
        "funding", "raised", "series a", "series b", "series c", "series d",
        "investment", "valuation", "investor", "funding round", "capital"
    ],
    "Feature": [
        "feature", "update", "improvement", "added", "now supports",
        "new capability", "enhancement", "upgraded"
    ],
    "Acquisition": [
        "acquire", "acquisition", "acquired", "merger", "merge", "buying"
    ],
    "Partnership": [
        "partnership", "partnering", "partner", "collaboration", "integrate",
        "integration"
    ],
    "Pricing": [
        "pricing", "price", "cost", "free tier", "subscription", "plan"
    ],
    "News": [
        "news", "report", "article", "interview", "coverage", "press"
    ],
}


def extract_domain(url: str) -> str:
    """Extract clean domain from URL"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return ""


def domain_to_company(domain: str) -> str:
    """Convert domain to company name using mappings or smart parsing"""
    # Check known mappings first
    if domain in COMPANY_MAPPINGS:
        return COMPANY_MAPPINGS[domain]

    # Handle subdomains (blog.company.com -> company.com)
    parts = domain.split(".")
    if len(parts) > 2:
        base_domain = ".".join(parts[-2:])
        if base_domain in COMPANY_MAPPINGS:
            return COMPANY_MAPPINGS[base_domain]

    # Fallback: capitalize first part of domain
    name = parts[0] if parts else domain
    return name.title()


def get_company_name(url: str, message_text: str) -> tuple[str, str]:
    """
    Intelligently determine company name from URL and message text.
    Returns (company_name, source_type) where source_type is 'direct' or 'inferred'
    """
    domain = extract_domain(url)

    # If it's a source domain (Twitter, LinkedIn, news sites), try to extract from text
    if is_source_domain(domain):
        company_from_text = extract_company_from_text(message_text)
        if company_from_text:
            return (company_from_text, "inferred")
        else:
            # Could not determine company - mark for review
            return (f"[Source: {domain_to_company(domain)}]", "unknown")

    # Direct company URL
    return (domain_to_company(domain), "direct")


def detect_category(text: str) -> str:
    """Detect category from message text using keywords"""
    text_lower = text.lower()

    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return category

    return "Other"


def extract_urls(text: str) -> list[str]:
    """Extract all URLs from message text"""
    # Handle Slack's URL formatting: <https://example.com|label>
    slack_url_pattern = r'<(https?://[^|>]+)(?:\|[^>]*)?>|(?<![<|])(https?://[^\s<>]+)'
    matches = re.findall(slack_url_pattern, text)

    urls = []
    for match in matches:
        url = match[0] if match[0] else match[1]
        if url:
            url = url.rstrip(".,;:!?)")
            urls.append(url)

    return list(set(urls))


def check_duplicate_url(url: str) -> bool:
    """Check if URL already exists in database"""
    try:
        result = supabase.table("competitor_intel").select("id").eq("url", url).execute()
        return len(result.data) > 0
    except Exception as e:
        print(f"Error checking duplicate: {e}")
        return False


def save_to_supabase(
    competitor: str,
    url: str,
    category: str,
    shared_by: str,
    message_text: str,
    slack_link: str,
    date_added: str = None
) -> bool:
    """Save competitor intel to Supabase database"""
    try:
        data = {
            "competitor": competitor,
            "url": url,
            "category": category,
            "summary": message_text[:2000],
            "shared_by": shared_by,
            "date_added": date_added or datetime.now().strftime("%Y-%m-%d"),
            "slack_link": slack_link,
        }
        supabase.table("competitor_intel").insert(data).execute()
        return True
    except Exception as e:
        print(f"Error saving to Supabase: {e}")
        return False


def build_slack_link(channel: str, ts: str) -> str:
    """Build a link to the Slack message"""
    ts_formatted = ts.replace(".", "")
    return f"https://slack.com/archives/{channel}/p{ts_formatted}"


@app.message(re.compile(r"https?://", re.IGNORECASE))
def handle_url_message(message, client, logger):
    """Handle messages containing URLs in the monitored channel"""

    # Get channel info to check if it's our target channel
    try:
        channel_info = client.conversations_info(channel=message["channel"])
        channel_name = channel_info["channel"]["name"]

        if channel_name != CHANNEL_NAME:
            return
    except Exception as e:
        logger.error(f"Error getting channel info: {e}")
        return

    # Don't process bot messages
    if message.get("bot_id") or message.get("subtype") == "bot_message":
        return

    text = message.get("text", "")
    urls = extract_urls(text)

    if not urls:
        return

    # Get user info
    user_id = message.get("user", "Unknown")
    try:
        user_info = client.users_info(user=user_id)
        user_name = user_info["user"]["real_name"]
    except Exception:
        user_name = f"<@{user_id}>"

    # Process each URL
    captured_companies = []

    for url in urls:
        if check_duplicate_url(url):
            continue

        # Smart company detection - handles social media/news links
        company, source_type = get_company_name(url, text)
        category = detect_category(text)
        slack_link = build_slack_link(message["channel"], message["ts"])

        success = save_to_supabase(
            competitor=company,
            url=url,
            category=category,
            shared_by=user_name,
            message_text=text,
            slack_link=slack_link
        )

        if success:
            captured_companies.append((company, category, source_type))

    # Reply in thread if we captured anything
    if captured_companies:
        if len(captured_companies) == 1:
            company, category, source_type = captured_companies[0]
            if source_type == "unknown":
                reply = f"Captured: *{company}* ({category})\n_Could not identify company - please review_"
            else:
                reply = f"Captured: *{company}* ({category})\n_Saved to competitor database_"
        else:
            lines = [f"Captured {len(captured_companies)} competitor updates:"]
            for company, category, source_type in captured_companies:
                if source_type == "unknown":
                    lines.append(f"  *{company}* ({category}) - needs review")
                else:
                    lines.append(f"  *{company}* ({category})")
            lines.append("_Saved to competitor database_")
            reply = "\n".join(lines)

        try:
            client.chat_postMessage(
                channel=message["channel"],
                thread_ts=message["ts"],
                text=reply
            )
        except Exception as e:
            logger.error(f"Error posting reply: {e}")


@app.event("app_mention")
def handle_mention(event, say, logger):
    """Handle when someone @mentions the bot"""
    say(
        text="Hi! I'm CompetitionBot. I automatically track competitor links "
             f"posted in #{CHANNEL_NAME} and save them to our database.\n\n"
             "Just post a link to any competitor news, product launch, or update "
             "and I'll capture it for you!",
        thread_ts=event.get("ts")
    )


@app.event("message")
def handle_other_messages(event, logger):
    """Catch-all for other message events (needed for Socket Mode)"""
    # Debug: print all incoming messages
    print(f"[DEBUG] Received message event: {event.get('text', '')[:100]}")
    print(f"[DEBUG] Channel: {event.get('channel')}, User: {event.get('user')}")


def main():
    """Start the bot"""
    print("=" * 50)
    print("CompetitionBot Starting...")
    print(f"Monitoring channel: #{CHANNEL_NAME}")
    print("=" * 50)

    handler = SocketModeHandler(
        app=app,
        app_token=os.environ.get("SLACK_APP_TOKEN")
    )
    handler.start()


if __name__ == "__main__":
    main()
