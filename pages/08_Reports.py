"""
MPT-CRM Reports Page
Dashboard analytics, pipeline reports, and activity summaries
"""

import streamlit as st
from datetime import datetime, date, timedelta
import sys
from pathlib import Path

# Add project root to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.navigation import render_sidebar, render_sidebar_stats

st.set_page_config(
    page_title="MPT-CRM - Reports",
    page_icon="📈",
    layout="wide"
)

# Render shared sidebar
render_sidebar("Reports")

# Main page
st.title("📈 Reports & Analytics")

# Date range selector
col1, col2 = st.columns([3, 1])
with col2:
    report_range = st.selectbox("Time Period", ["This Month", "Last 30 Days", "This Quarter", "This Year", "All Time"])

# Get data from session state (fallback to empty lists)
contacts = st.session_state.get('contacts', [])
deals = st.session_state.get('deals', [])
projects = st.session_state.get('projects', [])
tasks = st.session_state.get('tasks', [])
time_entries = st.session_state.get('time_entries', [])

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
        pipeline_value = sum(d.get('value', 0) for d in active_deals)
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
        stages = ['discovery', 'proposal', 'negotiation', 'won', 'lost']
        stage_labels = ['Discovery', 'Proposal', 'Negotiation', 'Won', 'Lost']

        for stage, label in zip(stages, stage_labels):
            stage_deals = [d for d in deals if d.get('stage') == stage]
            stage_value = sum(d.get('value', 0) for d in stage_deals)

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
        won_value = sum(d.get('value', 0) for d in won_deals)
        st.metric("Total Won", f"${won_value:,.0f}")
    with col3:
        lost_value = sum(d.get('value', 0) for d in lost_deals)
        st.metric("Total Lost", f"${lost_value:,.0f}")

    st.markdown("---")

    # Deals by stage (visual representation)
    st.markdown("### Deals by Stage")

    total_deals = len(deals) if deals else 1  # Avoid division by zero

    for stage in ['discovery', 'proposal', 'negotiation']:
        stage_deals = [d for d in deals if d.get('stage') == stage]
        percentage = len(stage_deals) / total_deals * 100 if total_deals > 0 else 0

        st.markdown(f"**{stage.title()}** - {len(stage_deals)} deals")
        st.progress(percentage / 100)

    st.markdown("---")

    # Top deals
    st.markdown("### Top Deals by Value")

    if deals:
        sorted_deals = sorted(deals, key=lambda x: x.get('value', 0), reverse=True)[:5]
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
            project_revenue[proj_name] = project_revenue.get(proj_name, 0) + entry.get('hours', 0) * default_rate

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

# Sidebar stats
render_sidebar_stats({
    "Total Contacts": str(len(contacts)),
    "Active Deals": str(len(active_deals)),
    "Pipeline": f"${pipeline_value:,.0f}"
})
