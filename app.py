"""
MPT-CRM - Metro Point Technology Customer Relationship Management
Main application entry point for Streamlit multi-page app
Connected to Supabase for real-time data
"""
import streamlit as st
import sys
from pathlib import Path

# Add project root to path for shared imports
sys.path.insert(0, str(Path(__file__).parent))
from shared.navigation import render_sidebar, render_sidebar_stats
from services.database import db

st.set_page_config(
    page_title="MPT-CRM",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load real stats from database
@st.cache_data(ttl=60)  # Cache for 60 seconds
def get_dashboard_stats():
    """Get dashboard statistics from database"""
    if db.is_connected:
        try:
            return db.get_dashboard_stats()
        except Exception:
            pass
    # Return placeholder stats if database not available
    return {
        "total_contacts": 0,
        "active_deals": 0,
        "pipeline_value": 0,
        "won_this_month": 0
    }

# Get real stats
stats = get_dashboard_stats()

# Render shared sidebar (includes all styling)
render_sidebar("Dashboard")
render_sidebar_stats({
    "Active Deals": str(stats.get("active_deals", 0)),
    "Pipeline Value": f"${stats.get('pipeline_value', 0):,.0f}",
    "Won This Month": f"${stats.get('won_this_month', 0):,.0f}"
})

# Show database connection status in sidebar
with st.sidebar:
    if db.is_connected:
        st.success("Database connected", icon="✅")
    else:
        st.warning("Using sample data", icon="⚠️")

# Main Dashboard
st.title("📊 MPT-CRM Dashboard")
st.markdown("### Metro Point Technology - Customer Relationship Management")

st.divider()

# Quick Stats Row - Using real data
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Active Deals",
        value=str(stats.get("active_deals", 0)),
        delta=None
    )

with col2:
    st.metric(
        label="Total Contacts",
        value=str(stats.get("total_contacts", 0)),
        delta=None
    )

with col3:
    st.metric(
        label="Pipeline Value",
        value=f"${stats.get('pipeline_value', 0):,.0f}",
        delta=None
    )

with col4:
    st.metric(
        label="Won This Month",
        value=f"${stats.get('won_this_month', 0):,.0f}",
        delta=None
    )

st.divider()

# Navigation Cards
st.markdown("### Quick Navigation")

col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.markdown("### 👥 Contacts")
        st.markdown("Manage networking contacts, prospects, leads, and clients.")
        st.markdown(f"**{stats.get('total_contacts', 0)}** total contacts")
        if st.button("Go to Contacts", key="nav_contacts"):
            st.switch_page("pages/02_Contacts.py")

with col2:
    with st.container(border=True):
        st.markdown("### 🎯 Sales Pipeline")
        st.markdown("Track deals through your sales process.")
        st.markdown(f"**{stats.get('active_deals', 0)}** active deals | **${stats.get('pipeline_value', 0):,.0f}** in pipeline")
        if st.button("Go to Pipeline", key="nav_pipeline"):
            st.switch_page("pages/03_Pipeline.py")

with col3:
    with st.container(border=True):
        st.markdown("### 📧 Marketing")
        st.markdown("Email campaigns, drip sequences, and templates.")
        st.markdown("Email templates and campaigns")
        if st.button("Go to Marketing", key="nav_marketing"):
            st.switch_page("pages/07_Marketing.py")

st.divider()

# Recent Activity - Load from database if available
st.markdown("### Recent Activity")

if db.is_connected:
    try:
        activities_data = db.get_activities(limit=5)
        if activities_data:
            for activity in activities_data:
                activity_type = activity.get('type', 'note')
                icon = {"email_sent": "📧", "call": "📞", "meeting": "🤝", "deal_stage_change": "🎯", "note": "📝"}.get(activity_type, "📌")
                created = activity.get('created_at', '')
                if created and 'T' in str(created):
                    created = str(created).split('T')[0]
                col1, col2 = st.columns([6, 1])
                with col1:
                    st.markdown(f"{icon} {activity.get('description', 'Activity')}")
                with col2:
                    st.caption(created)
        else:
            st.info("No recent activity. Start by creating contacts and deals!")
    except Exception:
        st.caption("_Activity tracking coming soon..._")
else:
    # Placeholder activities
    activities = [
        {"icon": "🤝", "text": "Start by adding contacts and creating deals", "time": ""},
        {"icon": "📧", "text": "Connect to Supabase for real activity tracking", "time": ""},
    ]
    for activity in activities:
        col1, col2 = st.columns([6, 1])
        with col1:
            st.markdown(f"{activity['icon']} {activity['text']}")
        with col2:
            st.caption(activity['time'])

st.divider()

# Upcoming Tasks
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📋 Upcoming Tasks")
    if db.is_connected:
        try:
            from datetime import datetime, timedelta
            upcoming_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
            tasks = db.get_tasks(due_date=upcoming_date)
            if tasks:
                for task in tasks[:5]:
                    priority_icon = {"urgent": "🔴", "high": "🔴", "medium": "🟡", "low": "🟢"}.get(task.get('priority', 'medium'), "🟡")
                    due = task.get('due_date', 'No date')
                    st.markdown(f"{priority_icon} **{task.get('title', 'Task')}** - {due}")
            else:
                st.info("No upcoming tasks. Create tasks from deal details!")
        except Exception:
            st.caption("_Task tracking coming soon..._")
    else:
        st.caption("_Connect to database for task tracking_")

with col2:
    st.markdown("### 📅 Deals Closing Soon")
    if db.is_connected:
        try:
            deals = db.get_deals()
            # Filter deals with expected_close in the next 14 days
            from datetime import datetime, timedelta
            closing_soon = []
            for deal in deals:
                if deal.get('expected_close') and deal.get('stage') not in ['won', 'lost']:
                    try:
                        close_date = datetime.strptime(str(deal['expected_close']), "%Y-%m-%d")
                        if close_date <= datetime.now() + timedelta(days=14):
                            closing_soon.append(deal)
                    except Exception:
                        pass

            if closing_soon:
                for deal in closing_soon[:5]:
                    st.markdown(f"• **{deal.get('title', 'Deal')}** - {deal.get('expected_close')} (${deal.get('value', 0):,.0f})")
            else:
                st.info("No deals closing in the next 2 weeks")
        except Exception:
            st.caption("_Deal tracking coming soon..._")
    else:
        st.caption("_Connect to database for deal tracking_")

# Footer
st.divider()
st.caption("MPT-CRM v0.3.0 | Metro Point Technology, LLC")
