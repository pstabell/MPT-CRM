"""
MPT-CRM Tasks Page
Manage tasks with priorities, due dates, and associations to contacts/deals/projects
"""

import streamlit as st
from datetime import datetime, date, timedelta
import sys
from pathlib import Path

# Add project root to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.navigation import render_sidebar, render_sidebar_stats

st.set_page_config(
    page_title="MPT-CRM - Tasks",
    page_icon="✅",
    layout="wide"
)

# Render shared sidebar
render_sidebar("Tasks")

# Initialize session state for tasks
if 'tasks' not in st.session_state:
    st.session_state.tasks = [
        {
            "id": "task-1",
            "title": "Follow up with John Smith",
            "description": "Send networking follow-up email after Chamber meeting",
            "status": "pending",
            "priority": "high",
            "due_date": (date.today() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "contact_name": "John Smith",
            "contact_id": "c-1",
            "deal_id": None,
            "project_id": None,
            "created_at": "2026-01-23"
        },
        {
            "id": "task-2",
            "title": "Send proposal to Sarah Johnson",
            "description": "Website redesign proposal with client portal specs",
            "status": "in_progress",
            "priority": "urgent",
            "due_date": date.today().strftime("%Y-%m-%d"),
            "contact_name": "Sarah Johnson",
            "contact_id": "c-2",
            "deal_id": "deal-2",
            "project_id": None,
            "created_at": "2026-01-22"
        },
        {
            "id": "task-3",
            "title": "Complete CRM database design",
            "description": "Finish database schema for Williams Insurance CRM",
            "status": "in_progress",
            "priority": "high",
            "due_date": (date.today() + timedelta(days=3)).strftime("%Y-%m-%d"),
            "contact_name": "Mike Williams",
            "contact_id": "c-3",
            "deal_id": None,
            "project_id": "proj-1",
            "created_at": "2026-01-20"
        },
        {
            "id": "task-4",
            "title": "Schedule discovery call with David Chen",
            "description": "Discuss mobile app requirements for field team",
            "status": "pending",
            "priority": "medium",
            "due_date": (date.today() + timedelta(days=5)).strftime("%Y-%m-%d"),
            "contact_name": "David Chen",
            "contact_id": "c-6",
            "deal_id": None,
            "project_id": None,
            "created_at": "2026-01-21"
        },
        {
            "id": "task-5",
            "title": "Review data migration scripts",
            "description": "Test and validate migration scripts before production run",
            "status": "pending",
            "priority": "medium",
            "due_date": (date.today() + timedelta(days=2)).strftime("%Y-%m-%d"),
            "contact_name": "Robert Taylor",
            "contact_id": "c-4",
            "deal_id": None,
            "project_id": "proj-2",
            "created_at": "2026-01-22"
        },
        {
            "id": "task-6",
            "title": "Send thank you note to Amanda",
            "description": "Thank Amanda for the referral to Johnson & Co",
            "status": "completed",
            "priority": "low",
            "due_date": "2026-01-22",
            "contact_name": "Amanda White",
            "contact_id": "c-7",
            "deal_id": None,
            "project_id": None,
            "created_at": "2026-01-20",
            "completed_at": "2026-01-22"
        },
    ]

# Task status definitions
TASK_STATUS = {
    "pending": {"label": "Pending", "icon": "⏳", "color": "#6c757d"},
    "in_progress": {"label": "In Progress", "icon": "🔄", "color": "#007bff"},
    "completed": {"label": "Completed", "icon": "✅", "color": "#28a745"},
    "cancelled": {"label": "Cancelled", "icon": "❌", "color": "#dc3545"},
}

TASK_PRIORITY = {
    "low": {"label": "Low", "icon": "🟢", "color": "#28a745"},
    "medium": {"label": "Medium", "icon": "🟡", "color": "#ffc107"},
    "high": {"label": "High", "icon": "🟠", "color": "#fd7e14"},
    "urgent": {"label": "Urgent", "icon": "🔴", "color": "#dc3545"},
}


def get_due_status(due_date_str):
    """Get visual indicator for due date status"""
    if not due_date_str:
        return "", ""

    due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
    today = date.today()
    diff = (due_date - today).days

    if diff < 0:
        return "🔴 Overdue", "red"
    elif diff == 0:
        return "⚠️ Due Today", "orange"
    elif diff <= 2:
        return "📅 Due Soon", "yellow"
    else:
        return f"📅 {due_date_str}", "gray"


# Main page
st.title("✅ Tasks")

# Toolbar
toolbar_col1, toolbar_col2, toolbar_col3, toolbar_col4 = st.columns([2, 1, 1, 1])

with toolbar_col1:
    search = st.text_input("🔍 Search tasks...", placeholder="Task title or contact", label_visibility="collapsed")

with toolbar_col2:
    status_filter = st.selectbox(
        "Status",
        ["All Status", "Pending", "In Progress", "Completed"],
        label_visibility="collapsed"
    )

with toolbar_col3:
    priority_filter = st.selectbox(
        "Priority",
        ["All Priority", "Urgent", "High", "Medium", "Low"],
        label_visibility="collapsed"
    )

with toolbar_col4:
    show_new_task = st.button("➕ New Task", type="primary")

# New task form
if show_new_task or st.session_state.get('show_new_task_form'):
    st.session_state.show_new_task_form = True

    with st.container(border=True):
        st.markdown("### ➕ New Task")

        new_title = st.text_input("Task Title", key="new_task_title")

        col1, col2 = st.columns(2)
        with col1:
            new_priority = st.selectbox(
                "Priority",
                ["medium", "high", "urgent", "low"],
                format_func=lambda x: f"{TASK_PRIORITY[x]['icon']} {TASK_PRIORITY[x]['label']}",
                key="new_task_priority"
            )
            new_due = st.date_input("Due Date", value=date.today() + timedelta(days=1), key="new_task_due")
        with col2:
            new_desc = st.text_area("Description", height=100, key="new_task_desc")

        btn_col1, btn_col2 = st.columns([1, 4])
        with btn_col1:
            if st.button("Create Task", type="primary"):
                if new_title:
                    new_task = {
                        "id": f"task-{len(st.session_state.tasks) + 1}",
                        "title": new_title,
                        "description": new_desc,
                        "status": "pending",
                        "priority": new_priority,
                        "due_date": new_due.strftime("%Y-%m-%d"),
                        "contact_name": None,
                        "contact_id": None,
                        "deal_id": None,
                        "project_id": None,
                        "created_at": date.today().strftime("%Y-%m-%d")
                    }
                    st.session_state.tasks.append(new_task)
                    st.session_state.show_new_task_form = False
                    st.success("Task created!")
                    st.rerun()
        with btn_col2:
            if st.button("Cancel"):
                st.session_state.show_new_task_form = False
                st.rerun()

# Stats
pending_tasks = [t for t in st.session_state.tasks if t['status'] == 'pending']
in_progress = [t for t in st.session_state.tasks if t['status'] == 'in_progress']
overdue = [t for t in st.session_state.tasks if t['status'] in ['pending', 'in_progress'] and t.get('due_date') and datetime.strptime(t['due_date'], "%Y-%m-%d").date() < date.today()]

render_sidebar_stats({
    "Pending": str(len(pending_tasks)),
    "In Progress": str(len(in_progress)),
    "Overdue": str(len(overdue))
})

# Stats row
stat_cols = st.columns(4)
with stat_cols[0]:
    st.metric("⏳ Pending", len(pending_tasks))
with stat_cols[1]:
    st.metric("🔄 In Progress", len(in_progress))
with stat_cols[2]:
    st.metric("🔴 Overdue", len(overdue))
with stat_cols[3]:
    completed_today = len([t for t in st.session_state.tasks if t['status'] == 'completed' and t.get('completed_at') == date.today().strftime("%Y-%m-%d")])
    st.metric("✅ Completed Today", completed_today)

st.markdown("---")

# Filter tasks
filtered_tasks = st.session_state.tasks

if search:
    search_lower = search.lower()
    filtered_tasks = [t for t in filtered_tasks if
        search_lower in t['title'].lower() or
        search_lower in (t.get('contact_name') or '').lower()]

if status_filter != "All Status":
    status_key = status_filter.lower().replace(" ", "_")
    filtered_tasks = [t for t in filtered_tasks if t['status'] == status_key]

if priority_filter != "All Priority":
    priority_key = priority_filter.lower()
    filtered_tasks = [t for t in filtered_tasks if t['priority'] == priority_key]

# Sort by priority and due date
priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
filtered_tasks = sorted(filtered_tasks, key=lambda t: (
    0 if t['status'] in ['pending', 'in_progress'] else 1,  # Active tasks first
    priority_order.get(t['priority'], 2),  # Then by priority
    t.get('due_date') or '9999-99-99'  # Then by due date
))

# Task list
st.markdown(f"### Showing {len(filtered_tasks)} tasks")

for task in filtered_tasks:
    status_info = TASK_STATUS.get(task['status'], TASK_STATUS['pending'])
    priority_info = TASK_PRIORITY.get(task['priority'], TASK_PRIORITY['medium'])
    due_label, due_color = get_due_status(task.get('due_date'))

    with st.container(border=True):
        col1, col2, col3, col4 = st.columns([0.5, 3, 2, 1.5])

        with col1:
            # Checkbox to complete
            is_complete = task['status'] == 'completed'
            if st.checkbox("", value=is_complete, key=f"check_{task['id']}", label_visibility="collapsed"):
                if not is_complete:
                    task['status'] = 'completed'
                    task['completed_at'] = date.today().strftime("%Y-%m-%d")
                    st.rerun()
            else:
                if is_complete:
                    task['status'] = 'pending'
                    task.pop('completed_at', None)
                    st.rerun()

        with col2:
            title_style = "text-decoration: line-through; color: gray;" if is_complete else ""
            st.markdown(f"<span style='{title_style}'><b>{priority_info['icon']} {task['title']}</b></span>", unsafe_allow_html=True)
            if task.get('contact_name'):
                st.caption(f"👤 {task['contact_name']}")

        with col3:
            if not is_complete and due_label:
                st.markdown(f"{due_label}")
            if task.get('project_id'):
                st.caption("📁 Project linked")
            if task.get('deal_id'):
                st.caption("💼 Deal linked")

        with col4:
            # Status selector
            if not is_complete:
                status_options = ["pending", "in_progress"]
                current_idx = status_options.index(task['status']) if task['status'] in status_options else 0
                new_status = st.selectbox(
                    "Status",
                    status_options,
                    index=current_idx,
                    format_func=lambda x: f"{TASK_STATUS[x]['icon']} {TASK_STATUS[x]['label']}",
                    key=f"status_{task['id']}",
                    label_visibility="collapsed"
                )
                if new_status != task['status']:
                    task['status'] = new_status
                    st.rerun()
            else:
                st.markdown(f"{status_info['icon']} {status_info['label']}")
