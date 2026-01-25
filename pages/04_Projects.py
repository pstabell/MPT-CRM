"""
MPT-CRM Projects Page
Manage client projects with status tracking, time logging, and billing
"""

import streamlit as st
from datetime import datetime, date
import sys
from pathlib import Path

# Add project root to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.navigation import render_sidebar, render_sidebar_stats

st.set_page_config(
    page_title="MPT-CRM - Projects",
    page_icon="📁",
    layout="wide"
)

# Render shared sidebar
render_sidebar("Projects")

# Initialize session state for projects
if 'projects' not in st.session_state:
    st.session_state.projects = [
        {
            "id": "proj-1",
            "name": "Williams Insurance CRM",
            "client": "Williams Insurance",
            "client_id": "c-3",
            "status": "active",
            "description": "Custom CRM for insurance agency operations with policy tracking and client management.",
            "start_date": "2026-01-15",
            "target_end_date": "2026-03-15",
            "budget": 15000,
            "hours_logged": 24.5,
            "hourly_rate": 150
        },
        {
            "id": "proj-2",
            "name": "Taylor Data Migration",
            "client": "Taylor & Associates",
            "client_id": "c-4",
            "status": "active",
            "description": "Migrate legacy data from Excel spreadsheets to new cloud-based system.",
            "start_date": "2026-01-10",
            "target_end_date": "2026-02-10",
            "budget": 8500,
            "hours_logged": 18,
            "hourly_rate": 150
        },
        {
            "id": "proj-3",
            "name": "Johnson Website Redesign",
            "client": "Johnson & Co",
            "client_id": "c-2",
            "status": "planning",
            "description": "Complete website redesign with client portal integration.",
            "start_date": None,
            "target_end_date": "2026-04-01",
            "budget": 12000,
            "hours_logged": 0,
            "hourly_rate": 150
        },
    ]

if 'time_entries' not in st.session_state:
    st.session_state.time_entries = [
        {"id": "te-1", "project_id": "proj-1", "date": "2026-01-20", "hours": 4.5, "description": "Database schema design and setup", "billable": True},
        {"id": "te-2", "project_id": "proj-1", "date": "2026-01-21", "hours": 6, "description": "API development for contact management", "billable": True},
        {"id": "te-3", "project_id": "proj-1", "date": "2026-01-22", "hours": 5.5, "description": "Frontend UI components", "billable": True},
        {"id": "te-4", "project_id": "proj-1", "date": "2026-01-23", "hours": 8.5, "description": "Policy tracking module", "billable": True},
        {"id": "te-5", "project_id": "proj-2", "date": "2026-01-15", "hours": 6, "description": "Data analysis and mapping", "billable": True},
        {"id": "te-6", "project_id": "proj-2", "date": "2026-01-16", "hours": 8, "description": "Migration script development", "billable": True},
        {"id": "te-7", "project_id": "proj-2", "date": "2026-01-17", "hours": 4, "description": "Testing and validation", "billable": True},
    ]

if 'selected_project' not in st.session_state:
    st.session_state.selected_project = None

# Project status definitions
PROJECT_STATUS = {
    "planning": {"label": "Planning", "icon": "📋", "color": "#6c757d"},
    "active": {"label": "Active", "icon": "🚀", "color": "#28a745"},
    "on_hold": {"label": "On Hold", "icon": "⏸️", "color": "#ffc107"},
    "completed": {"label": "Completed", "icon": "✅", "color": "#17a2b8"},
    "cancelled": {"label": "Cancelled", "icon": "❌", "color": "#dc3545"},
}


def show_project_detail(project_id):
    """Show detailed project view"""
    project = next((p for p in st.session_state.projects if p['id'] == project_id), None)
    if not project:
        st.session_state.selected_project = None
        st.rerun()
        return

    status_info = PROJECT_STATUS.get(project['status'], PROJECT_STATUS['active'])

    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"## {status_info['icon']} {project['name']}")
        st.markdown(f"**Client:** {project['client']}")
    with col2:
        if st.button("← Back to Projects"):
            st.session_state.selected_project = None
            st.rerun()

    st.markdown("---")

    # Main content
    col1, col2 = st.columns([2, 1])

    with col1:
        # Project details
        st.markdown("### 📋 Project Details")

        new_name = st.text_input("Project Name", project['name'], key="edit_proj_name")
        new_desc = st.text_area("Description", project.get('description', ''), height=100, key="edit_proj_desc")

        date_col1, date_col2 = st.columns(2)
        with date_col1:
            start = project.get('start_date')
            new_start = st.date_input(
                "Start Date",
                value=datetime.strptime(start, "%Y-%m-%d").date() if start else None,
                key="edit_start"
            )
        with date_col2:
            end = project.get('target_end_date')
            new_end = st.date_input(
                "Target End Date",
                value=datetime.strptime(end, "%Y-%m-%d").date() if end else None,
                key="edit_end"
            )

        # Update project
        if new_name != project['name'] or new_desc != project.get('description', ''):
            project['name'] = new_name
            project['description'] = new_desc

        # Time entries section
        st.markdown("### ⏱️ Time Entries")

        project_entries = [e for e in st.session_state.time_entries if e['project_id'] == project_id]

        # Add new time entry
        with st.expander("➕ Log Time"):
            entry_col1, entry_col2 = st.columns(2)
            with entry_col1:
                new_entry_date = st.date_input("Date", value=date.today(), key="new_entry_date")
                new_entry_hours = st.number_input("Hours", min_value=0.0, max_value=24.0, step=0.5, key="new_entry_hours")
            with entry_col2:
                new_entry_desc = st.text_input("Description", key="new_entry_desc")
                new_entry_billable = st.checkbox("Billable", value=True, key="new_entry_billable")

            if st.button("Add Time Entry", type="primary"):
                if new_entry_hours > 0 and new_entry_desc:
                    new_entry = {
                        "id": f"te-{len(st.session_state.time_entries) + 1}",
                        "project_id": project_id,
                        "date": new_entry_date.strftime("%Y-%m-%d"),
                        "hours": new_entry_hours,
                        "description": new_entry_desc,
                        "billable": new_entry_billable
                    }
                    st.session_state.time_entries.append(new_entry)
                    project['hours_logged'] = project.get('hours_logged', 0) + new_entry_hours
                    st.success("Time entry added!")
                    st.rerun()

        # Display time entries
        if project_entries:
            for entry in sorted(project_entries, key=lambda x: x['date'], reverse=True):
                with st.container(border=True):
                    e_col1, e_col2, e_col3 = st.columns([2, 3, 1])
                    with e_col1:
                        st.markdown(f"**{entry['date']}**")
                        st.caption(f"{entry['hours']} hours")
                    with e_col2:
                        st.markdown(entry['description'])
                        if entry.get('billable'):
                            st.caption(f"💰 ${entry['hours'] * project.get('hourly_rate', 150):,.2f}")
                    with e_col3:
                        if entry.get('billable'):
                            st.markdown("✅ Billable")
                        else:
                            st.markdown("⬜ Non-billable")
        else:
            st.info("No time entries yet. Log your first entry above.")

    with col2:
        # Status
        st.markdown("### 📊 Status")
        status_options = list(PROJECT_STATUS.keys())
        status_labels = [f"{PROJECT_STATUS[s]['icon']} {PROJECT_STATUS[s]['label']}" for s in status_options]
        current_idx = status_options.index(project['status']) if project['status'] in status_options else 0
        new_status_label = st.selectbox("Status", status_labels, index=current_idx, key="edit_status")
        new_status = status_options[status_labels.index(new_status_label)]
        if new_status != project['status']:
            project['status'] = new_status
            st.rerun()

        # Budget & Billing
        st.markdown("### 💰 Budget & Billing")

        budget = project.get('budget', 0)
        hourly_rate = project.get('hourly_rate', 150)
        hours_logged = project.get('hours_logged', 0)
        amount_earned = hours_logged * hourly_rate

        st.metric("Budget", f"${budget:,.0f}")
        st.metric("Hourly Rate", f"${hourly_rate}/hr")
        st.metric("Hours Logged", f"{hours_logged:.1f} hrs")
        st.metric("Amount Earned", f"${amount_earned:,.2f}")

        # Progress bar
        if budget > 0:
            progress = min(amount_earned / budget, 1.0)
            st.progress(progress)
            st.caption(f"{progress * 100:.0f}% of budget used")

        # Quick actions
        st.markdown("### ⚡ Quick Actions")
        if st.button("📄 Generate Invoice", use_container_width=True):
            st.toast("Invoice generation coming soon!")
        if st.button("📧 Email Client", use_container_width=True):
            st.toast("Email feature coming soon!")
        if st.button("📊 View Report", use_container_width=True):
            st.toast("Project reports coming soon!")


# Main page
st.title("📁 Projects")

if st.session_state.selected_project:
    show_project_detail(st.session_state.selected_project)
else:
    # Toolbar
    toolbar_col1, toolbar_col2, toolbar_col3 = st.columns([2, 1, 1])

    with toolbar_col1:
        search = st.text_input("🔍 Search projects...", placeholder="Project name or client", label_visibility="collapsed")

    with toolbar_col2:
        status_filter = st.selectbox(
            "Status",
            ["All Status"] + [f"{PROJECT_STATUS[s]['icon']} {PROJECT_STATUS[s]['label']}" for s in PROJECT_STATUS],
            label_visibility="collapsed"
        )

    with toolbar_col3:
        if st.button("➕ New Project", type="primary"):
            st.toast("New project form coming soon!")

    # Stats
    active_projects = [p for p in st.session_state.projects if p['status'] == 'active']
    total_budget = sum(p.get('budget', 0) for p in active_projects)
    total_hours = sum(p.get('hours_logged', 0) for p in active_projects)

    render_sidebar_stats({
        "Active Projects": str(len(active_projects)),
        "Total Budget": f"${total_budget:,.0f}",
        "Hours Logged": f"{total_hours:.1f}"
    })

    # Stats row
    stat_cols = st.columns(5)
    for i, (status_key, status_info) in enumerate(PROJECT_STATUS.items()):
        count = len([p for p in st.session_state.projects if p['status'] == status_key])
        with stat_cols[i]:
            st.metric(f"{status_info['icon']} {status_info['label']}", count)

    st.markdown("---")

    # Filter projects
    filtered_projects = st.session_state.projects

    if search:
        search_lower = search.lower()
        filtered_projects = [p for p in filtered_projects if
            search_lower in p['name'].lower() or
            search_lower in p['client'].lower()]

    if status_filter != "All Status":
        status_key = next(k for k, v in PROJECT_STATUS.items() if f"{v['icon']} {v['label']}" == status_filter)
        filtered_projects = [p for p in filtered_projects if p['status'] == status_key]

    # Project list
    st.markdown(f"### Showing {len(filtered_projects)} projects")

    for project in filtered_projects:
        status_info = PROJECT_STATUS.get(project['status'], PROJECT_STATUS['active'])
        hours_logged = project.get('hours_logged', 0)
        budget = project.get('budget', 0)
        hourly_rate = project.get('hourly_rate', 150)
        earned = hours_logged * hourly_rate

        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

            with col1:
                st.markdown(f"**{status_info['icon']} {project['name']}**")
                st.caption(f"🏢 {project['client']}")

            with col2:
                if project.get('target_end_date'):
                    st.markdown(f"📅 Due: {project['target_end_date']}")
                st.caption(f"⏱️ {hours_logged:.1f} hours logged")

            with col3:
                st.markdown(f"💰 ${earned:,.0f} / ${budget:,.0f}")
                if budget > 0:
                    progress = min(earned / budget, 1.0)
                    st.progress(progress)

            with col4:
                if st.button("Open", key=f"open_{project['id']}"):
                    st.session_state.selected_project = project['id']
                    st.rerun()
