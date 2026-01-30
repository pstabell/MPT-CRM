"""
MPT-CRM Reports Page
Dashboard analytics, pipeline reports, and activity summaries

SELF-CONTAINED PAGE: All code is inline per CLAUDE.md rules
"""

import streamlit as st
from datetime import datetime, date, timedelta
import os

# ============================================
# DATABASE CONNECTION (self-contained)
# ============================================
try:
    from supabase import create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

@st.cache_resource(show_spinner=False)
def get_db():
    """Create and cache Supabase client"""
    if not SUPABASE_AVAILABLE:
        return None
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    if url and key:
        try:
            return create_client(url, key)
        except Exception:
            return None
    return None

def db_is_connected():
    """Check if database is connected"""
    return get_db() is not None

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
    "Tasks": {"icon": "✅", "path": "pages/05_Tasks.py"},
    "Time & Billing": {"icon": "💰", "path": "pages/06_Time_Billing.py"},
    "Marketing": {"icon": "📧", "path": "pages/07_Marketing.py"},
    "Reports": {"icon": "📈", "path": "pages/08_Reports.py"},
    "Settings": {"icon": "⚙️", "path": "pages/09_Settings.py"},
}

def render_sidebar(current_page="Reports"):
    """Render the navigation sidebar"""
    st.markdown(HIDE_STREAMLIT_NAV, unsafe_allow_html=True)

    with st.sidebar:
        # Logo/Title
        st.image("logo.jpg", use_container_width=True)
        st.markdown("---")

        # Navigation using radio buttons
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
    page_title="MPT-CRM - Reports",
    page_icon="favicon.jpg",
    layout="wide"
)

# ============================================
# RENDER SIDEBAR
# ============================================
render_sidebar("Reports")

# ============================================
# INITIALIZE SESSION STATE (use page-specific prefixes)
# ============================================
# Get data from session state with fallbacks
contacts = st.session_state.get('contacts', [])
deals = st.session_state.get('pipeline_deals', [])
projects = st.session_state.get('proj_projects', [])
tasks = st.session_state.get('tasks_list', [])
time_entries = st.session_state.get('tb_time_entries', [])

# ============================================
# MAIN PAGE
# ============================================
st.title("📈 Reports & Analytics")

# Date range selector
col1, col2 = st.columns([3, 1])
with col2:
    report_range = st.selectbox("Time Period", ["This Month", "Last 30 Days", "This Quarter", "This Year", "All Time"])

# Tabs for different reports
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "💼 Pipeline", "👥 Contacts", "⏱️ Time & Revenue"])

# ============================================
# OVERVIEW TAB
# ============================================
with tab1:
    st.markdown("### Key Metrics")

    # Top level metrics
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

    with metric_col1:
        st.metric("Total Contacts", len(contacts))

    with metric_col2:
        active_deals = [d for d in deals if d.get('stage') not in ['won', 'lost']]
        pipeline_value = sum(d.get('value', 0) or 0 for d in active_deals)
        st.metric("Pipeline Value", f"${pipeline_value:,.0f}")

    with metric_col3:
        active_projects = [p for p in projects if p.get('status') == 'active']
        st.metric("Active Projects", len(active_projects))

    with metric_col4:
        pending_tasks = [t for t in tasks if t.get('status') in ['pending', 'in_progress']]
        st.metric("Open Tasks", len(pending_tasks))

    st.markdown("---")

    # Two column layout
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 💼 Deal Pipeline")

        # Pipeline stages breakdown
        stages = ['lead', 'qualified', 'proposal', 'negotiation', 'contract', 'won', 'lost']
        stage_labels = ['Lead', 'Qualified', 'Proposal', 'Negotiation', 'Contract', 'Won', 'Lost']

        for stage, label in zip(stages, stage_labels):
            stage_deals = [d for d in deals if d.get('stage') == stage]
            stage_value = sum(d.get('value', 0) or 0 for d in stage_deals)

            with st.container(border=True):
                inner_col1, inner_col2 = st.columns([3, 1])
                with inner_col1:
                    st.markdown(f"**{label}**")
                    st.caption(f"{len(stage_deals)} deals")
                with inner_col2:
                    st.markdown(f"**${stage_value:,.0f}**")

    with col2:
        st.markdown("### 📁 Project Status")

        status_labels = {
            'planning': '📋 Planning',
            'active': '🚀 Active',
            'on_hold': '⏸️ On Hold',
            'completed': '✅ Completed'
        }

        for status, label in status_labels.items():
            status_projects = [p for p in projects if p.get('status') == status]
            total_budget = sum(p.get('budget', 0) for p in status_projects)

            with st.container(border=True):
                inner_col1, inner_col2 = st.columns([3, 1])
                with inner_col1:
                    st.markdown(f"**{label}**")
                    st.caption(f"{len(status_projects)} projects")
                with inner_col2:
                    st.markdown(f"**${total_budget:,.0f}**")

    st.markdown("---")

    # Recent activity
    st.markdown("### 📅 Recent Activity")
    st.info("Activity tracking will show recent emails, calls, meetings, and status changes once connected to the database.")

# ============================================
# PIPELINE TAB
# ============================================
with tab2:
    st.markdown("### Pipeline Analysis")

    # Win rate
    won_deals = [d for d in deals if d.get('stage') == 'won']
    lost_deals = [d for d in deals if d.get('stage') == 'lost']
    closed_deals = won_deals + lost_deals

    if closed_deals:
        win_rate = len(won_deals) / len(closed_deals) * 100
    else:
        win_rate = 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Win Rate", f"{win_rate:.0f}%")
    with col2:
        won_value = sum(d.get('value', 0) or 0 for d in won_deals)
        st.metric("Total Won", f"${won_value:,.0f}")
    with col3:
        lost_value = sum(d.get('value', 0) or 0 for d in lost_deals)
        st.metric("Total Lost", f"${lost_value:,.0f}")

    st.markdown("---")

    # Deals by stage (visual representation)
    st.markdown("### Deals by Stage")

    total_deals = len(deals) if deals else 1  # Avoid division by zero

    for stage in ['lead', 'qualified', 'proposal', 'negotiation', 'contract']:
        stage_deals = [d for d in deals if d.get('stage') == stage]
        percentage = len(stage_deals) / total_deals * 100 if total_deals > 0 else 0

        st.markdown(f"**{stage.title()}** - {len(stage_deals)} deals")
        st.progress(percentage / 100)

    st.markdown("---")

    # Top deals
    st.markdown("### Top Deals by Value")

    if deals:
        sorted_deals = sorted(deals, key=lambda x: x.get('value', 0) or 0, reverse=True)[:5]
        for deal in sorted_deals:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{deal.get('title', 'Untitled')}**")
                    st.caption(f"{deal.get('stage', 'Unknown').title()}")
                with col2:
                    st.markdown(f"**${deal.get('value', 0):,.0f}**")
    else:
        st.info("No deals to display.")

# ============================================
# CONTACTS TAB
# ============================================
with tab3:
    st.markdown("### Contact Analytics")

    # Contact types breakdown
    contact_types = {
        'networking': '🤝 Networking',
        'prospect': '🎯 Prospect',
        'lead': '🔥 Lead',
        'client': '⭐ Client',
        'former_client': '📦 Former Client',
        'partner': '🤝 Partner',
        'vendor': '🏢 Vendor'
    }

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### By Type")
        for type_key, type_label in contact_types.items():
            type_contacts = [c for c in contacts if c.get('type') == type_key]
            count = len(type_contacts)
            if count > 0:
                st.markdown(f"{type_label}: **{count}**")

    with col2:
        st.markdown("### By Source")
        sources = {}
        for contact in contacts:
            source = contact.get('source', 'Unknown')
            sources[source] = sources.get(source, 0) + 1

        for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
            st.markdown(f"{source.title()}: **{count}**")

    st.markdown("---")

    # Top tags
    st.markdown("### Popular Tags")
    tag_counts = {}
    for contact in contacts:
        for tag in contact.get('tags', []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    if tag_counts:
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        for tag, count in sorted_tags:
            st.markdown(f"`{tag}` - {count} contacts")
    else:
        st.info("No tags used yet.")

# ============================================
# TIME & REVENUE TAB
# ============================================
with tab4:
    st.markdown("### Time & Revenue Analysis")

    # Calculate totals
    total_hours = sum(e.get('hours', 0) for e in time_entries)
    billable_hours = sum(e.get('hours', 0) for e in time_entries if e.get('billable', True))
    default_rate = 150
    total_revenue = billable_hours * default_rate

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Hours", f"{total_hours:.1f}")
    with col2:
        st.metric("Billable Hours", f"{billable_hours:.1f}")
    with col3:
        st.metric("Revenue", f"${total_revenue:,.0f}")

    st.markdown("---")

    # By project
    st.markdown("### Revenue by Project")

    project_revenue = {}
    for entry in time_entries:
        proj_name = entry.get('project_name', 'Unknown')
        if entry.get('billable', True):
            rate = entry.get('hourly_rate', default_rate)
            project_revenue[proj_name] = project_revenue.get(proj_name, 0) + entry.get('hours', 0) * rate

    if project_revenue:
        sorted_projects = sorted(project_revenue.items(), key=lambda x: x[1], reverse=True)
        for proj, revenue in sorted_projects:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{proj}**")
                with col2:
                    st.markdown(f"**${revenue:,.0f}**")
    else:
        st.info("No billable time tracked yet.")

# ============================================
# SIDEBAR STATS
# ============================================
render_sidebar_stats({
    "Total Contacts": str(len(contacts)),
    "Active Deals": str(len(active_deals)),
    "Pipeline": f"${pipeline_value:,.0f}"
})
