"""
MPT-CRM - Metro Point Technology Customer Relationship Management
Main application entry point for Streamlit multi-page app
"""
import streamlit as st
import sys
from pathlib import Path

# Add project root to path for shared imports
sys.path.insert(0, str(Path(__file__).parent))
from shared.navigation import render_sidebar, render_sidebar_stats

st.set_page_config(
    page_title="MPT-CRM",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Render shared sidebar (includes all styling)
render_sidebar("Dashboard")
render_sidebar_stats({
    "Active Deals": "12",
    "Pipeline Value": "$84,500",
    "Won This Month": "$24,000"
})

# Main Dashboard
st.title("📊 MPT-CRM Dashboard")
st.markdown("### Metro Point Technology - Customer Relationship Management")

st.divider()

# Quick Stats Row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Active Deals",
        value="12",
        delta="3 this week"
    )

with col2:
    st.metric(
        label="Total Contacts",
        value="47",
        delta="5 new"
    )

with col3:
    st.metric(
        label="Pipeline Value",
        value="$84,500",
        delta="$12,000"
    )

with col4:
    st.metric(
        label="Won This Month",
        value="$24,000",
        delta="2 deals"
    )

st.divider()

# Navigation Cards
st.markdown("### Quick Navigation")

col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.markdown("### 👥 Contacts")
        st.markdown("Manage networking contacts, prospects, leads, and clients.")
        st.markdown("**47** total contacts | **12** active leads")
        if st.button("Go to Contacts", key="nav_contacts"):
            st.switch_page("pages/02_Contacts.py")

with col2:
    with st.container(border=True):
        st.markdown("### 🎯 Sales Pipeline")
        st.markdown("Track deals through your sales process.")
        st.markdown("**12** active deals | **$84,500** in pipeline")
        if st.button("Go to Pipeline", key="nav_pipeline"):
            st.switch_page("pages/03_Pipeline.py")

with col3:
    with st.container(border=True):
        st.markdown("### 📧 Marketing")
        st.markdown("Email campaigns, drip sequences, and templates.")
        st.markdown("**4** active campaigns | **89%** open rate")
        if st.button("Go to Marketing", key="nav_marketing"):
            st.switch_page("pages/07_Marketing.py")

st.divider()

# Recent Activity
st.markdown("### Recent Activity")

activities = [
    {"icon": "🤝", "text": "New networking contact: John Smith from ABC Corp", "time": "2 hours ago"},
    {"icon": "📧", "text": "Drip email sent to 5 contacts", "time": "4 hours ago"},
    {"icon": "🎯", "text": "Deal 'Website Redesign' moved to Proposal", "time": "Yesterday"},
    {"icon": "⭐", "text": "New client: Tampa Bay Insurance", "time": "2 days ago"},
    {"icon": "📝", "text": "Proposal sent: Custom CRM Development", "time": "3 days ago"},
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
    tasks = [
        {"task": "Follow up with Mike Johnson", "due": "Today", "priority": "🔴"},
        {"task": "Send proposal to Cape Coral Tech", "due": "Tomorrow", "priority": "🟡"},
        {"task": "Schedule discovery call - XYZ Corp", "due": "This week", "priority": "🟢"},
    ]
    for task in tasks:
        st.markdown(f"{task['priority']} **{task['task']}** - {task['due']}")

with col2:
    st.markdown("### 📅 Upcoming Follow-ups")
    followups = [
        {"contact": "Sarah Williams", "type": "Drip Day 3", "due": "Today"},
        {"contact": "Chamber Contacts (5)", "type": "Drip Day 7", "due": "Friday"},
        {"contact": "ABC Manufacturing", "type": "Proposal check-in", "due": "Next Monday"},
    ]
    for f in followups:
        st.markdown(f"• **{f['contact']}** - {f['type']} ({f['due']})")

# Footer
st.divider()
st.caption("MPT-CRM v0.1.0 | Metro Point Technology, LLC")
