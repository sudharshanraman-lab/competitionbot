"""
CompetitionBot Dashboard - Streamlit Frontend
View, search, filter, and edit competitor intelligence data
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from collections import Counter
import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables (for local development)
load_dotenv()

def get_secret(key: str) -> str:
    """Get secret from Streamlit Cloud or local .env"""
    # Try Streamlit secrets first (for Streamlit Cloud)
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        pass
    # Fall back to environment variables (for local dev)
    return os.environ.get(key, "")

# Page config
st.set_page_config(
    page_title="CompetitionBot Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Supabase
@st.cache_resource
def get_supabase():
    return create_client(
        get_secret("SUPABASE_URL"),
        get_secret("SUPABASE_KEY")
    )

supabase = get_supabase()

# Categories
CATEGORIES = ["Product Launch", "Funding", "Feature", "Acquisition", "Partnership", "Pricing", "News", "Other"]

# ----- Data Functions -----

@st.cache_data(ttl=60)  # Cache for 60 seconds
def load_data():
    """Load all competitor data from Supabase"""
    try:
        result = supabase.table("competitor_intel").select("*").order("date_added", desc=True).execute()
        return pd.DataFrame(result.data)
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

def refresh_data():
    """Clear cache and reload data"""
    st.cache_data.clear()

def update_entry(entry_id: int, updates: dict):
    """Update an entry in Supabase"""
    try:
        supabase.table("competitor_intel").update(updates).eq("id", entry_id).execute()
        return True
    except Exception as e:
        st.error(f"Error updating: {e}")
        return False

def delete_entry(entry_id: int):
    """Delete an entry from Supabase"""
    try:
        supabase.table("competitor_intel").delete().eq("id", entry_id).execute()
        return True
    except Exception as e:
        st.error(f"Error deleting: {e}")
        return False

def add_entry(data: dict):
    """Add a new entry to Supabase"""
    try:
        supabase.table("competitor_intel").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Error adding: {e}")
        return False

# ----- UI Components -----

def render_sidebar(df):
    """Render sidebar with filters"""
    st.sidebar.title("🎯 CompetitionBot")
    st.sidebar.markdown("---")

    # Refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        refresh_data()
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.subheader("Filters")

    # Search
    search = st.sidebar.text_input("🔍 Search", placeholder="Search competitors, URLs...")

    # Competitor filter
    competitors = ["All"] + sorted(df["competitor"].unique().tolist()) if not df.empty else ["All"]
    selected_competitor = st.sidebar.selectbox("Company", competitors)

    # Category filter
    categories = ["All"] + CATEGORIES
    selected_category = st.sidebar.selectbox("Category", categories)

    # Date range
    st.sidebar.subheader("Date Range")
    col1, col2 = st.sidebar.columns(2)

    if not df.empty:
        min_date = pd.to_datetime(df["date_added"]).min().date()
        max_date = pd.to_datetime(df["date_added"]).max().date()
    else:
        min_date = datetime.now().date() - timedelta(days=365)
        max_date = datetime.now().date()

    start_date = col1.date_input("From", min_date)
    end_date = col2.date_input("To", max_date)

    return {
        "search": search,
        "competitor": selected_competitor,
        "category": selected_category,
        "start_date": start_date,
        "end_date": end_date
    }

def filter_data(df, filters):
    """Apply filters to dataframe"""
    if df.empty:
        return df

    filtered = df.copy()

    # Search filter
    if filters["search"]:
        search_term = filters["search"].lower()
        filtered = filtered[
            filtered["competitor"].str.lower().str.contains(search_term, na=False) |
            filtered["url"].str.lower().str.contains(search_term, na=False) |
            filtered["summary"].str.lower().str.contains(search_term, na=False)
        ]

    # Competitor filter
    if filters["competitor"] != "All":
        filtered = filtered[filtered["competitor"] == filters["competitor"]]

    # Category filter
    if filters["category"] != "All":
        filtered = filtered[filtered["category"] == filters["category"]]

    # Date filter
    filtered["date_added"] = pd.to_datetime(filtered["date_added"])
    filtered = filtered[
        (filtered["date_added"].dt.date >= filters["start_date"]) &
        (filtered["date_added"].dt.date <= filters["end_date"])
    ]

    return filtered

def render_metrics(df, filtered_df):
    """Render key metrics"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Entries", len(df))

    with col2:
        unique_competitors = df["competitor"].nunique() if not df.empty else 0
        st.metric("Competitors Tracked", unique_competitors)

    with col3:
        st.metric("Filtered Results", len(filtered_df))

    with col4:
        # This month's entries
        if not df.empty:
            df["date_added"] = pd.to_datetime(df["date_added"])
            this_month = df[df["date_added"].dt.month == datetime.now().month]
            st.metric("This Month", len(this_month))
        else:
            st.metric("This Month", 0)

def render_charts(df):
    """Render charts and visualizations"""
    if df.empty:
        st.info("No data to display charts")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Top Competitors")
        competitor_counts = df["competitor"].value_counts().head(10)
        # Display as table instead of chart (Python 3.14 compatibility)
        for comp, count in competitor_counts.items():
            st.write(f"**{comp}**: {count} entries")
            st.progress(count / competitor_counts.max())

    with col2:
        st.subheader("📁 By Category")
        category_counts = df["category"].value_counts()
        for cat, count in category_counts.items():
            st.write(f"**{cat}**: {count} entries")
            st.progress(count / category_counts.max())

    # Timeline as table
    st.subheader("📈 Updates Over Time")
    df_copy = df.copy()
    df_copy["date_added"] = pd.to_datetime(df_copy["date_added"])
    df_copy["month"] = df_copy["date_added"].dt.strftime("%Y-%m")
    timeline = df_copy.groupby("month").size().reset_index(name="count")
    timeline = timeline.sort_values("month")

    cols = st.columns(len(timeline) if len(timeline) <= 6 else 6)
    for i, (_, row) in enumerate(timeline.tail(6).iterrows()):
        with cols[i % 6]:
            st.metric(row["month"], row["count"])

def render_data_table(df):
    """Render data table with edit/delete functionality"""
    if df.empty:
        st.info("No data matches your filters")
        return

    st.subheader(f"📋 Competitor Updates ({len(df)} results)")

    # Add new entry button
    if st.button("➕ Add New Entry"):
        st.session_state.show_add_form = True

    # Add new entry form
    if st.session_state.get("show_add_form", False):
        with st.expander("Add New Entry", expanded=True):
            with st.form("add_entry_form"):
                new_competitor = st.text_input("Competitor Name*")
                new_url = st.text_input("URL*")
                new_category = st.selectbox("Category", CATEGORIES)
                new_summary = st.text_area("Summary/Notes")
                new_date = st.date_input("Date", datetime.now())

                col1, col2 = st.columns(2)
                submit = col1.form_submit_button("Add Entry")
                cancel = col2.form_submit_button("Cancel")

                if submit and new_competitor and new_url:
                    add_entry({
                        "competitor": new_competitor,
                        "url": new_url,
                        "category": new_category,
                        "summary": new_summary,
                        "date_added": str(new_date),
                        "shared_by": "Manual Entry",
                        "slack_link": ""
                    })
                    st.session_state.show_add_form = False
                    refresh_data()
                    st.success("Entry added!")
                    st.rerun()

                if cancel:
                    st.session_state.show_add_form = False
                    st.rerun()

    # Display data
    for idx, row in df.iterrows():
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                # Main info
                competitor = row["competitor"]
                category = row["category"]
                url = row["url"]
                date = row["date_added"]
                summary = row.get("summary", "")[:200] if row.get("summary") else ""

                st.markdown(f"**{competitor}** • `{category}`")
                st.caption(f"📅 {date} | 🔗 [Link]({url})")
                if summary:
                    st.text(summary[:150] + "..." if len(summary) > 150 else summary)

            with col2:
                # Edit button
                if st.button("✏️ Edit", key=f"edit_{row['id']}"):
                    st.session_state[f"editing_{row['id']}"] = True

            with col3:
                # Delete button
                if st.button("🗑️ Delete", key=f"delete_{row['id']}"):
                    st.session_state[f"confirm_delete_{row['id']}"] = True

            # Edit form
            if st.session_state.get(f"editing_{row['id']}", False):
                with st.form(f"edit_form_{row['id']}"):
                    st.markdown("**Edit Entry**")

                    edit_competitor = st.text_input("Competitor", value=row["competitor"])
                    edit_category = st.selectbox("Category", CATEGORIES,
                                                  index=CATEGORIES.index(row["category"]) if row["category"] in CATEGORIES else 0)
                    edit_url = st.text_input("URL", value=row["url"])
                    edit_summary = st.text_area("Summary", value=row.get("summary", ""))

                    col1, col2 = st.columns(2)
                    save = col1.form_submit_button("💾 Save")
                    cancel = col2.form_submit_button("Cancel")

                    if save:
                        update_entry(row["id"], {
                            "competitor": edit_competitor,
                            "category": edit_category,
                            "url": edit_url,
                            "summary": edit_summary
                        })
                        st.session_state[f"editing_{row['id']}"] = False
                        refresh_data()
                        st.success("Updated!")
                        st.rerun()

                    if cancel:
                        st.session_state[f"editing_{row['id']}"] = False
                        st.rerun()

            # Delete confirmation
            if st.session_state.get(f"confirm_delete_{row['id']}", False):
                st.warning(f"Are you sure you want to delete this entry for **{row['competitor']}**?")
                col1, col2 = st.columns(2)
                if col1.button("Yes, Delete", key=f"confirm_yes_{row['id']}"):
                    delete_entry(row["id"])
                    st.session_state[f"confirm_delete_{row['id']}"] = False
                    refresh_data()
                    st.success("Deleted!")
                    st.rerun()
                if col2.button("Cancel", key=f"confirm_no_{row['id']}"):
                    st.session_state[f"confirm_delete_{row['id']}"] = False
                    st.rerun()

            st.markdown("---")

def render_export(df):
    """Render export options"""
    st.subheader("📥 Export Data")

    col1, col2 = st.columns(2)

    with col1:
        # Export filtered data
        if not df.empty:
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"competitor_intel_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

    with col2:
        st.caption(f"{len(df)} rows will be exported")

# ----- Main App -----

def main():
    # Load data
    df = load_data()

    # Sidebar filters
    filters = render_sidebar(df)

    # Filter data
    filtered_df = filter_data(df, filters)

    # Main content
    st.title("🎯 CompetitionBot Dashboard")
    st.markdown("Track and manage competitor intelligence")

    # Tabs
    tab1, tab2, tab3 = st.tabs(["📋 Data", "📊 Analytics", "📥 Export"])

    with tab1:
        render_metrics(df, filtered_df)
        st.markdown("---")
        render_data_table(filtered_df)

    with tab2:
        render_metrics(df, filtered_df)
        st.markdown("---")
        render_charts(filtered_df)

    with tab3:
        render_export(filtered_df)

if __name__ == "__main__":
    main()
