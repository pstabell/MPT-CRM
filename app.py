"""
MPT-CRM - Metro Point Technology Customer Relationship Management
Main application entry point for Streamlit multi-page app
Connected to Supabase for real-time data

Database operations are handled by db_service.py — the single source of truth.
"""
import os
try:
    import streamlit as st
    if hasattr(st, "secrets"):
        for key, value in st.secrets.items():
            if isinstance(value, str):
                os.environ.setdefault(key, value)
except Exception:
    pass

import streamlit as st
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from db_service import (
    db_is_connected,
    db_get_dashboard_stats, db_get_activities, db_get_tasks, db_get_deals,
    db_process_due_campaign_enrollments,
)
from sso_auth import require_sso_auth, render_auth_status, logout, is_authenticated

# ============================================
# NAVIGATION SIDEBAR (self-contained)
# ============================================
HIDE_STREAMLIT_NAV = """
<style>
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #1a1a2e;
    }
    section[data-testid="stSidebar"] .stMarkdown {
        color: white;
    }
    section[data-testid="stSidebar"] .stRadio label {
        color: white;
    }
    section[data-testid="stSidebar"] .stRadio label span {
        color: white !important;
    }
    section[data-testid="stSidebar"] [data-testid="stMetricLabel"] {
        color: rgba(255,255,255,0.7) !important;
    }
    section[data-testid="stSidebar"] [data-testid="stMetricValue"] {
        color: white !important;
    }
</style>
"""

PAGE_CONFIG = {
    "Dashboard": {"icon": "📊", "path": "app.py"},
    "Discovery Call": {"icon": "📞", "path": "pages/01_Discovery.py"},
    "Contacts": {"icon": "👥", "path": "pages/02_Contacts.py"},
    "Sales Pipeline": {"icon": "🎯", "path": "pages/03_Pipeline.py"},
    "Projects": {"icon": "📁", "path": "pages/04_Projects.py"},
    "Service": {"icon": "\U0001f527", "path": "pages/10_Service.py"},
    "Tasks": {"icon": "✅", "path": "pages/05_Tasks.py"},
    "Time & Billing": {"icon": "💰", "path": "pages/06_Time_Billing.py"},
    "Marketing": {"icon": "📧", "path": "pages/07_Marketing.py"},
    "Reports": {"icon": "📈", "path": "pages/08_Reports.py"},
    "Settings": {"icon": "⚙️", "path": "pages/09_Settings.py"},
    "Help": {"icon": "❓", "path": "pages/11_Help.py"},
}

def render_sidebar(current_page="Dashboard"):
    """Render the navigation sidebar"""
    st.markdown(HIDE_STREAMLIT_NAV, unsafe_allow_html=True)

    with st.sidebar:
        # Logo/Title
        st.image("logo.jpg", use_container_width=True)
        st.markdown("---")

        # Navigation using radio buttons (same as Discovery page)
        pages = [f"{config['icon']} {name}" for name, config in PAGE_CONFIG.items()]
        current_index = list(PAGE_CONFIG.keys()).index(current_page) if current_page in PAGE_CONFIG else 0

        selected = st.radio("Navigation", pages, index=current_index, label_visibility="collapsed")

        # Handle navigation
        selected_name = selected.split(" ", 1)[1] if " " in selected else selected
        if selected_name != current_page:
            config = PAGE_CONFIG.get(selected_name)
            if config and config['path']:
                st.switch_page(config['path'])

        st.markdown("---")
        
        # External link to Mission Control
        st.markdown("### 🎯 Mission Control")
        st.markdown("[Open Mission Control →](https://mpt-mission-control.vercel.app/)", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Auth status at bottom
        render_auth_status()

def render_sidebar_stats(stats: dict):
    """Render stats in the sidebar"""
    with st.sidebar:
        st.markdown("### Quick Stats")
        for label, value in stats.items():
            st.metric(label, value)

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="MPT-CRM",
    page_icon="favicon.jpg",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# AUTHENTICATION
# ============================================
# TEMPORARY: allow_bypass=True while Mission Control Supabase is down (2026-02-12)
# TODO: Change back to allow_bypass=False when MC Supabase recovers
require_sso_auth(allow_bypass=False)

# ============================================
# START DRIP SCHEDULER (once per process)
# ============================================
@st.cache_resource(show_spinner=False)
def start_drip_scheduler():
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(
        db_process_due_campaign_enrollments,
        "interval",
        minutes=30,
        id="drip_scheduler",
        replace_existing=True,
        max_instances=1,
        coalesce=True
    )
    scheduler.start()
    return scheduler

scheduler = start_drip_scheduler()
scheduler_running = bool(scheduler and getattr(scheduler, "running", False))

# ============================================
# LOAD DATA
# ============================================
@st.cache_data(ttl=120, show_spinner=False)
def get_dashboard_stats():
    """Get dashboard statistics - cached for 2 minutes"""
    return db_get_dashboard_stats()

@st.cache_data(ttl=120, show_spinner=False)
def get_recent_activities():
    """Get recent activities - cached for 2 minutes"""
    return db_get_activities(limit=5)

@st.cache_data(ttl=120, show_spinner=False)
def get_upcoming_tasks():
    """Get upcoming tasks - cached for 2 minutes"""
    upcoming_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    return db_get_tasks(due_date=upcoming_date)

@st.cache_data(ttl=120, show_spinner=False)
def get_deals_closing_soon():
    """Get deals closing in next 14 days"""
    deals = db_get_deals()
    closing_soon = []
    for deal in deals:
        if deal.get('expected_close') and deal.get('stage') not in ['won', 'lost']:
            try:
                close_date = datetime.strptime(str(deal['expected_close']), "%Y-%m-%d")
                if close_date <= datetime.now() + timedelta(days=14):
                    closing_soon.append(deal)
            except Exception:
                pass
    return closing_soon

# Get real stats
stats = get_dashboard_stats()

# ============================================
# RENDER SIDEBAR
# ============================================
render_sidebar("Dashboard")
render_sidebar_stats({
    "Active Deals": str(stats.get("active_deals", 0)),
    "Pipeline Value": f"${stats.get('pipeline_value', 0):,.0f}",
    "Won This Month": f"${stats.get('won_this_month', 0):,.0f}"
})

# Show database connection status in sidebar
with st.sidebar:
    if db_is_connected():
        st.success("Database connected", icon="✅")
    else:
        st.error("Database not connected - check .env file", icon="❌")

    # Drip scheduler status
    if scheduler_running:
        st.caption("📧 Drip scheduler: running")
    else:
        st.caption("📧 Drip scheduler: stopped")

    # Logout button
    st.markdown("---")
    if is_authenticated():
        st.caption(f"Logged in as: **{st.session_state.get('auth_user', 'unknown')}**")
        if st.button("🚪 Logout", use_container_width=True):
            logout()
            st.rerun()

# ============================================
# MAIN DASHBOARD
# ============================================
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

# Recent Activity - Load from cached data
st.markdown("### Recent Activity")

activities_data = get_recent_activities()
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

st.divider()

# Upcoming Tasks
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📋 Upcoming Tasks")
    tasks = get_upcoming_tasks()
    if tasks:
        for task in tasks[:5]:
            priority_icon = {"urgent": "🔴", "high": "🔴", "medium": "🟡", "low": "🟢"}.get(task.get('priority', 'medium'), "🟡")
            due = task.get('due_date', 'No date')
            st.markdown(f"{priority_icon} **{task.get('title', 'Task')}** - {due}")
    else:
        st.info("No upcoming tasks. Create tasks from deal details!")

with col2:
    st.markdown("### 📅 Deals Closing Soon")
    closing_soon = get_deals_closing_soon()
    if closing_soon:
        for deal in closing_soon[:5]:
            st.markdown(f"• **{deal.get('title', 'Deal')}** - {deal.get('expected_close')} (${deal.get('value', 0):,.0f})")
    else:
        st.info("No deals closing in the next 2 weeks")

# Footer
st.divider()
st.caption("MPT-CRM v0.4.0 | Metro Point Technology, LLC")
