# CompetitionBot - Project Reference

## Quick Start for Claude

When resuming work on this project, read this file first to understand the architecture and key references.

---

## Project Overview

**Purpose:** Slack bot that automatically captures competitor intelligence from a Slack channel and stores it in a database, with a web dashboard for viewing/editing.

**Owner:** sudharshanraman-lab

---

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Slack Bot     │────▶│    Supabase     │◀────│   Dashboard     │
│   (Railway)     │     │   (Database)    │     │ (Streamlit Cloud)│
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

| Component | Platform | URL/Location |
|-----------|----------|--------------|
| Slack Bot | Railway | https://railway.com/project/0e2eca49-29ac-4249-8848-82f7a0d09ee9 |
| Database | Supabase | https://nmmxpuxuxeagmaneyukh.supabase.co |
| Dashboard | Streamlit Cloud | https://competitionbot-reap.streamlit.app |
| Source Code | GitHub | https://github.com/sudharshanraman-lab/competitionbot |

---

## Key Files

| File | Purpose |
|------|---------|
| `app.py` | Main Slack bot - monitors channel, extracts competitor info, saves to Supabase |
| `dashboard.py` | Streamlit frontend - view, search, filter, edit, delete entries |
| `report.py` | Generate monthly reports (run with `python report.py --post`) |
| `backfill.py` | Backfill historical Slack messages into database |
| `review.py` | Review and fix competitor mappings |
| `fix_entries.py` | Batch fix/update entries |

---

## Environment Variables

### Required for Slack Bot (Railway)
```
SLACK_BOT_TOKEN=xoxb-...      # Bot OAuth token from Slack API
SLACK_APP_TOKEN=xapp-...      # App-level token for Socket Mode
SUPABASE_URL=https://nmmxpuxuxeagmaneyukh.supabase.co
SUPABASE_KEY=eyJhbGci...      # Supabase anon key
SLACK_CHANNEL_NAME=topic-competition
```

### Required for Dashboard (Streamlit Cloud Secrets)
```toml
SUPABASE_URL = "https://nmmxpuxuxeagmaneyukh.supabase.co"
SUPABASE_KEY = "eyJhbGci..."
```

### Local Development
Copy `.env.example` to `.env` and fill in values.

---

## Database Schema (Supabase)

**Table:** `competitor_intel`

| Column | Type | Description |
|--------|------|-------------|
| id | int8 | Primary key, auto-increment |
| competitor | text | Competitor company name |
| url | text | Source URL |
| category | text | Product Launch, Funding, Feature, etc. |
| summary | text | Brief description |
| date_added | timestamp | When entry was created |
| shared_by | text | Who shared in Slack |
| slack_link | text | Link to original Slack message |

**Categories:** Product Launch, Funding, Feature, Acquisition, Partnership, Pricing, News, Other

---

## Local Development

```bash
cd ~/competitionbot
source venv/bin/activate

# Run Slack bot locally
python app.py

# Run dashboard locally
streamlit run dashboard.py
# Opens at http://localhost:8501
```

---

## Deployment

### Slack Bot (Railway)
```bash
cd ~/competitionbot
railway up
```
- Auto-deploys from local files
- Environment variables must be set in Railway dashboard

### Dashboard (Streamlit Cloud)
- Auto-deploys on git push to `main` branch
- Secrets configured in Streamlit Cloud dashboard
```bash
git add -A && git commit -m "message" && git push
```

---

## Slack App Configuration

**Slack App URL:** https://api.slack.com/apps (look for CompetitionBot)

**Required Scopes (Bot Token):**
- `channels:history` - Read channel messages
- `channels:read` - List channels
- `chat:write` - Post messages
- `users:read` - Get user info

**Socket Mode:** Enabled (uses SLACK_APP_TOKEN)

**Event Subscriptions:**
- `message.channels` - Listen to channel messages

---

## Common Tasks

### Add a new competitor mapping
Edit the `COMPETITOR_MAPPING` dict in `app.py`

### Change monitored channel
Update `SLACK_CHANNEL_NAME` environment variable

### Generate monthly report
```bash
python report.py --post  # Posts to Slack
python report.py         # Just prints locally
```

### Export data
Use the dashboard's Export tab, or:
```python
from supabase import create_client
client = create_client(url, key)
data = client.table("competitor_intel").select("*").execute()
```

---

## Known Issues / Notes

1. **Python 3.14 compatibility:** Local dev uses Python 3.14. Dashboard uses progress bars instead of charts due to altair incompatibility.

2. **Streamlit Cloud uses Python 3.13:** Requirements use `>=` instead of `==` for pandas/streamlit to allow compatible versions.

3. **Private vs Public repo:** Repo is PUBLIC (required for free Streamlit Cloud tier).

---

## Recent Changes (Dec 2024)

- Initial bot deployment to Railway
- Supabase database setup with 128+ entries
- Streamlit dashboard with full CRUD
- Dashboard deployed to Streamlit Cloud

---

## Contact / Resources

- **Supabase Dashboard:** https://supabase.com/dashboard/project/nmmxpuxuxeagmaneyukh
- **Railway Dashboard:** https://railway.com/project/0e2eca49-29ac-4249-8848-82f7a0d09ee9
- **Streamlit Dashboard:** https://share.streamlit.io (manage app)
- **Slack API:** https://api.slack.com/apps
