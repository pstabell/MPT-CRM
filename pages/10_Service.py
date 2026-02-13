# -*- coding: utf-8 -*-
"""
MPT-CRM Service Page
Post-delivery work tracking: Change Orders, Maintenance, Service Tickets

Change Orders = Customer-triggered, BILLABLE at $150/hr
Maintenance = MPT-triggered, BILLABLE (vendor updates, security patches, health checks)
Service Tickets = Subscriber-triggered, FREE (cost center MPT absorbs)

Database operations are handled by db_service.py \u2014 the single source of truth.
"""

import streamlit as st
from datetime import datetime, date, timedelta
from db_service import (
    db_is_connected, db_get_projects,
    db_get_service_tickets, db_get_service_ticket,
    db_create_service_ticket, db_update_service_ticket,
)
from sso_auth import require_sso_auth, render_auth_status

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
    "Dashboard": {"icon": "\U0001f4ca", "path": "app.py"},
    "Discovery Call": {"icon": "\U0001f4de", "path": "pages/01_Discovery.py"},
    "Companies": {"icon": "🏢", "path": "pages/01a_Companies.py"},
    "Contacts": {"icon": "\U0001f465", "path": "pages/02_Contacts.py"},
    "Sales Pipeline": {"icon": "\U0001f3af", "path": "pages/03_Pipeline.py"},
    "Projects": {"icon": "\U0001f4c1", "path": "pages/04_Projects.py"},
    "Service": {"icon": "\U0001f527", "path": "pages/10_Service.py"},
    "Tasks": {"icon": "\u2705", "path": "pages/05_Tasks.py"},
    "Time & Billing": {"icon": "\U0001f4b0", "path": "pages/06_Time_Billing.py"},
    "Marketing": {"icon": "\U0001f4e7", "path": "pages/07_Marketing.py"},
    "Reports": {"icon": "\U0001f4c8", "path": "pages/08_Reports.py"},
    "Settings": {"icon": "\u2699\ufe0f", "path": "pages/09_Settings.py"},
}


def render_sidebar(current_page="Service"):
    """Render the navigation sidebar"""
    st.markdown(HIDE_STREAMLIT_NAV, unsafe_allow_html=True)

    with st.sidebar:
        st.image("logo.jpg", use_container_width=True)
        st.markdown("---")

        pages = [f"{config['icon']} {name}" for name, config in PAGE_CONFIG.items()]
        current_index = list(PAGE_CONFIG.keys()).index(current_page) if current_page in PAGE_CONFIG else 0

        selected = st.radio("Navigation", pages, index=current_index, label_visibility="collapsed")

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
    page_title="MPT-CRM - Service",
    page_icon="favicon.jpg",
    layout="wide"
)

require_sso_auth(allow_bypass=False)

# ============================================
# RENDER SIDEBAR
# ============================================
render_sidebar("Service")

# ============================================
# CONSTANTS
# ============================================
DEFAULT_HOURLY_RATE = 150.00
CLIENT_NAME = "Metro Point Technology LLC"

# Ticket type definitions
TICKET_TYPES = {
    "change_order": {"label": "Change Order", "icon": "\U0001f4dd", "billable": True},
    "maintenance": {"label": "Maintenance", "icon": "\U0001f6e0\ufe0f", "billable": True},
    "service": {"label": "Service Ticket", "icon": "\U0001f3ab", "billable": False},
}

# Status definitions per ticket type
CHANGE_ORDER_STATUSES = {
    "open": {"label": "Open", "icon": "\U0001f7e1", "color": "#ffc107"},
    "in_progress": {"label": "In Progress", "icon": "\U0001f535", "color": "#007bff"},
    "completed": {"label": "Completed", "icon": "\u2705", "color": "#28a745"},
    "billed": {"label": "Billed", "icon": "\U0001f4b2", "color": "#17a2b8"},
}

MAINTENANCE_STATUSES = {
    "scheduled": {"label": "Scheduled", "icon": "\U0001f4c5", "color": "#6c757d"},
    "in_progress": {"label": "In Progress", "icon": "\U0001f535", "color": "#007bff"},
    "completed": {"label": "Completed", "icon": "\u2705", "color": "#28a745"},
    "billed": {"label": "Billed", "icon": "\U0001f4b2", "color": "#17a2b8"},
}

SERVICE_STATUSES = {
    "open": {"label": "Open", "icon": "\U0001f7e1", "color": "#ffc107"},
    "in_progress": {"label": "In Progress", "icon": "\U0001f535", "color": "#007bff"},
    "resolved": {"label": "Resolved", "icon": "\u2705", "color": "#28a745"},
    "closed": {"label": "Closed", "icon": "\u2b1c", "color": "#6c757d"},
}

MAINTENANCE_TYPES = {
    "vendor_update": {"label": "Vendor Update", "icon": "\U0001f4e6"},
    "security_patch": {"label": "Security Patch", "icon": "\U0001f6e1\ufe0f"},
    "health_check": {"label": "Health Check", "icon": "\U0001f3e5"},
    "dependency_update": {"label": "Dependency Update", "icon": "\U0001f504"},
    "other": {"label": "Other", "icon": "\U0001f527"},
}

PRIORITY_CONFIG = {
    "low": {"label": "Low", "icon": "\U0001f7e2", "color": "#28a745"},
    "medium": {"label": "Medium", "icon": "\U0001f7e1", "color": "#ffc107"},
    "high": {"label": "High", "icon": "\U0001f7e0", "color": "#fd7e14"},
    "urgent": {"label": "Urgent", "icon": "\U0001f534", "color": "#dc3545"},
}

# ============================================
# DEFAULT SAMPLE DATA
# ============================================
DEFAULT_SERVICE_TICKETS = [
    {
        "id": "svc-ticket-1",
        "title": "Add carrier export to CSV",
        "description": "Client requested the ability to export carrier commission data to CSV format from the ACT module.",
        "ticket_type": "change_order",
        "project_id": "mpt-proj-1",
        "client_name": CLIENT_NAME,
        "status": "in_progress",
        "priority": "medium",
        "estimated_hours": 4.0,
        "actual_hours": 2.5,
        "hourly_rate": DEFAULT_HOURLY_RATE,
        "is_billable": True,
        "requested_by": "Patrick (Internal)",
        "maintenance_type": None,
        "created_at": "2025-06-01T10:00:00",
        "updated_at": "2025-06-10T14:30:00",
        "completed_at": None,
    },
    {
        "id": "svc-ticket-2",
        "title": "Dashboard layout redesign",
        "description": "Restructure the main dashboard to show key metrics above the fold. Add quick-action cards.",
        "ticket_type": "change_order",
        "project_id": "mpt-proj-4",
        "client_name": CLIENT_NAME,
        "status": "open",
        "priority": "low",
        "estimated_hours": 6.0,
        "actual_hours": 0,
        "hourly_rate": DEFAULT_HOURLY_RATE,
        "is_billable": True,
        "requested_by": "Patrick (Internal)",
        "maintenance_type": None,
        "created_at": "2025-06-12T09:00:00",
        "updated_at": "2025-06-12T09:00:00",
        "completed_at": None,
    },
    {
        "id": "svc-ticket-3",
        "title": "Streamlit v1.45 update - AMS-APP",
        "description": "Update Streamlit from 1.41 to 1.45. Test all pages for breaking changes. Update requirements.txt.",
        "ticket_type": "maintenance",
        "project_id": "mpt-proj-1",
        "client_name": CLIENT_NAME,
        "status": "scheduled",
        "priority": "medium",
        "estimated_hours": 2.0,
        "actual_hours": 0,
        "hourly_rate": DEFAULT_HOURLY_RATE,
        "is_billable": True,
        "requested_by": None,
        "maintenance_type": "vendor_update",
        "created_at": "2025-06-15T08:00:00",
        "updated_at": "2025-06-15T08:00:00",
        "completed_at": None,
    },
    {
        "id": "svc-ticket-4",
        "title": "Monthly health check - WRAP Generator",
        "description": "Monthly application health monitoring. Check error logs, performance metrics, uptime, and dependency status.",
        "ticket_type": "maintenance",
        "project_id": "mpt-proj-3",
        "client_name": CLIENT_NAME,
        "status": "completed",
        "priority": "low",
        "estimated_hours": 1.0,
        "actual_hours": 1.5,
        "hourly_rate": DEFAULT_HOURLY_RATE,
        "is_billable": True,
        "requested_by": None,
        "maintenance_type": "health_check",
        "created_at": "2025-06-01T08:00:00",
        "updated_at": "2025-06-05T16:00:00",
        "completed_at": "2025-06-05T16:00:00",
    },
    {
        "id": "svc-ticket-5",
        "title": "Supabase Python SDK security patch",
        "description": "Apply security patch for supabase-py. CVE-2025-XXXX advisory. Update across all projects.",
        "ticket_type": "maintenance",
        "project_id": None,
        "client_name": CLIENT_NAME,
        "status": "in_progress",
        "priority": "high",
        "estimated_hours": 3.0,
        "actual_hours": 1.0,
        "hourly_rate": DEFAULT_HOURLY_RATE,
        "is_billable": True,
        "requested_by": None,
        "maintenance_type": "security_patch",
        "created_at": "2025-06-14T10:00:00",
        "updated_at": "2025-06-15T11:00:00",
        "completed_at": None,
    },
    {
        "id": "svc-ticket-6",
        "title": "ACT commission report not loading",
        "description": "Subscriber reports that the commission summary report shows a spinner but never loads. Likely a timeout on large datasets.",
        "ticket_type": "service",
        "project_id": "mpt-proj-1",
        "client_name": "Demo Subscriber",
        "status": "open",
        "priority": "high",
        "estimated_hours": 2.0,
        "actual_hours": 0.5,
        "hourly_rate": DEFAULT_HOURLY_RATE,
        "is_billable": False,
        "requested_by": "demo@agency.com",
        "maintenance_type": None,
        "created_at": "2025-06-16T14:00:00",
        "updated_at": "2025-06-16T15:00:00",
        "completed_at": None,
    },
    {
        "id": "svc-ticket-7",
        "title": "Login issue - password reset flow",
        "description": "Subscriber unable to reset password via the forgot password link. Email not being received.",
        "ticket_type": "service",
        "project_id": "mpt-proj-1",
        "client_name": "Demo Subscriber",
        "status": "resolved",
        "priority": "urgent",
        "estimated_hours": 1.0,
        "actual_hours": 0.75,
        "hourly_rate": DEFAULT_HOURLY_RATE,
        "is_billable": False,
        "requested_by": "support@agency2.com",
        "maintenance_type": None,
        "created_at": "2025-06-10T09:00:00",
        "updated_at": "2025-06-10T12:00:00",
        "completed_at": "2025-06-10T12:00:00",
    },
]


# ============================================
# HELPERS
# ============================================

def _safe_num(val, default=0):
    """Return val as float if numeric, otherwise default."""
    if val is None:
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _format_date(dt_str):
    """Format a datetime string for display."""
    if not dt_str:
        return "N/A"
    try:
        if "T" in str(dt_str):
            dt = datetime.fromisoformat(str(dt_str).replace("Z", "+00:00"))
        else:
            dt = datetime.strptime(str(dt_str), "%Y-%m-%d")
        return dt.strftime("%m/%d/%Y")
    except Exception:
        return str(dt_str)[:10]


def _get_status_map(ticket_type):
    """Return the status map for a given ticket type."""
    if ticket_type == "change_order":
        return CHANGE_ORDER_STATUSES
    elif ticket_type == "maintenance":
        return MAINTENANCE_STATUSES
    elif ticket_type == "service":
        return SERVICE_STATUSES
    return CHANGE_ORDER_STATUSES


def _get_project_options():
    """Get project names for dropdown selection."""
    projects = st.session_state.get("svc_projects", [])
    options = {"": "-- No Project --"}
    for p in projects:
        pid = p.get("id", "")
        name = p.get("name", "Unknown")
        client = p.get("client_name", p.get("client", ""))
        options[pid] = f"{name} ({client})" if client else name
    return options


def _get_project_name(project_id):
    """Get project name from ID."""
    if not project_id:
        return "N/A"
    projects = st.session_state.get("svc_projects", [])
    for p in projects:
        if str(p.get("id", "")) == str(project_id):
            return p.get("name", "Unknown")
    return "Unknown"


# ============================================
# INITIALIZE SESSION STATE
# ============================================

def load_service_tickets():
    """Load service tickets from DB first, fall back to defaults."""
    if db_is_connected():
        try:
            db_tickets = db_get_service_tickets()
            if db_tickets:
                return db_tickets
        except Exception as e:
            print(f"[Service] DB load failed, using defaults: {e}")
    return [dict(t) for t in DEFAULT_SERVICE_TICKETS]


def load_projects_for_linking():
    """Load projects for the project dropdown."""
    if db_is_connected():
        try:
            db_projects = db_get_projects()
            if db_projects:
                return db_projects
        except Exception:
            pass
    # Fall back to default project list
    return [
        {"id": "mpt-proj-1", "name": "AMS-APP", "client_name": CLIENT_NAME},
        {"id": "mpt-proj-2", "name": "CRM-APP", "client_name": CLIENT_NAME},
        {"id": "mpt-proj-3", "name": "WRAP Proposal Generator", "client_name": CLIENT_NAME},
        {"id": "mpt-proj-4", "name": "MPT-CRM", "client_name": CLIENT_NAME},
        {"id": "mpt-proj-5", "name": "MetroPointTech.com", "client_name": CLIENT_NAME},
        {"id": "mpt-proj-6", "name": "MetroPointTechnology.com", "client_name": CLIENT_NAME},
    ]


# Force reload when code version changes
_CODE_VERSION = "v1-service-tickets"
if st.session_state.get("svc_code_version") != _CODE_VERSION:
    st.session_state.svc_projects = load_projects_for_linking()
    st.session_state.svc_tickets = load_service_tickets()
    st.session_state.svc_code_version = _CODE_VERSION

if "svc_tickets" not in st.session_state:
    st.session_state.svc_tickets = load_service_tickets()

if "svc_projects" not in st.session_state:
    st.session_state.svc_projects = load_projects_for_linking()


# ============================================
# DASHBOARD METRICS
# ============================================

def render_service_dashboard(tickets):
    """Render the service dashboard metrics at the top of the page."""
    now = datetime.now()
    current_month = now.month
    current_year = now.year

    # Split tickets by type
    change_orders = [t for t in tickets if t.get("ticket_type") == "change_order"]
    maintenance = [t for t in tickets if t.get("ticket_type") == "maintenance"]
    service_tix = [t for t in tickets if t.get("ticket_type") == "service"]

    # Open items (not completed/billed/resolved/closed)
    closed_statuses = {"completed", "billed", "resolved", "closed"}
    open_co = [t for t in change_orders if t.get("status") not in closed_statuses]
    open_maint = [t for t in maintenance if t.get("status") not in closed_statuses]
    open_svc = [t for t in service_tix if t.get("status") not in closed_statuses]
    total_open = len(open_co) + len(open_maint) + len(open_svc)

    # Billable revenue (change orders + maintenance actual hours)
    billable_tickets = change_orders + maintenance
    billable_hours = sum(_safe_num(t.get("actual_hours")) for t in billable_tickets)
    billable_revenue = sum(
        _safe_num(t.get("actual_hours")) * _safe_num(t.get("hourly_rate"), DEFAULT_HOURLY_RATE)
        for t in billable_tickets
    )

    # Service cost (free tickets hours x rate)
    service_hours = sum(_safe_num(t.get("actual_hours")) for t in service_tix)
    service_cost = sum(
        _safe_num(t.get("actual_hours")) * _safe_num(t.get("hourly_rate"), DEFAULT_HOURLY_RATE)
        for t in service_tix
    )

    # This month's hours
    month_hours = 0
    for t in tickets:
        created = str(t.get("created_at", ""))
        try:
            if "T" in created:
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            else:
                dt = datetime.strptime(created, "%Y-%m-%d")
            if dt.month == current_month and dt.year == current_year:
                month_hours += _safe_num(t.get("actual_hours"))
        except Exception:
            pass

    st.markdown("### \U0001f527 Service Dashboard")
    st.caption(f"Post-delivery work tracking \u00b7 All billable work at ${DEFAULT_HOURLY_RATE:.0f}/hr")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("\U0001f4cb Open Items", total_open)
    with col2:
        st.metric("\U0001f4b5 Billable Revenue", f"${billable_revenue:,.0f}")
    with col3:
        st.metric("\U0001f4b8 Service Cost", f"${service_cost:,.0f}")
    with col4:
        st.metric("\u23f1\ufe0f This Month", f"{month_hours:.1f} hrs")

    # Type breakdown
    st.markdown("---")
    type_cols = st.columns(3)

    with type_cols[0]:
        with st.container(border=True):
            st.markdown(f"**\U0001f4dd Change Orders** ({len(change_orders)})")
            st.markdown(f"Open: **{len(open_co)}** \u00b7 Hours: **{sum(_safe_num(t.get('actual_hours')) for t in change_orders):.1f}**")
            co_rev = sum(_safe_num(t.get('actual_hours')) * _safe_num(t.get('hourly_rate'), DEFAULT_HOURLY_RATE) for t in change_orders)
            st.caption(f"\U0001f4b0 Revenue: ${co_rev:,.0f}")

    with type_cols[1]:
        with st.container(border=True):
            st.markdown(f"**\U0001f6e0\ufe0f Maintenance** ({len(maintenance)})")
            st.markdown(f"Open: **{len(open_maint)}** \u00b7 Hours: **{sum(_safe_num(t.get('actual_hours')) for t in maintenance):.1f}**")
            maint_rev = sum(_safe_num(t.get('actual_hours')) * _safe_num(t.get('hourly_rate'), DEFAULT_HOURLY_RATE) for t in maintenance)
            st.caption(f"\U0001f4b0 Revenue: ${maint_rev:,.0f}")

    with type_cols[2]:
        with st.container(border=True):
            st.markdown(f"**\U0001f3ab Service Tickets** ({len(service_tix)})")
            st.markdown(f"Open: **{len(open_svc)}** \u00b7 Hours: **{service_hours:.1f}**")
            st.caption(f"\U0001f4b8 Cost: ${service_cost:,.0f} (MPT absorbs)")


# ============================================
# CHANGE ORDERS TAB
# ============================================

def render_change_orders_tab(tickets):
    """Render the Change Orders tab."""
    change_orders = [t for t in tickets if t.get("ticket_type") == "change_order"]

    # Status filter
    filter_col1, filter_col2, filter_col3 = st.columns([2, 1, 1])
    with filter_col1:
        search = st.text_input(
            "\U0001f50d Search change orders...",
            placeholder="Title, client, or project",
            key="co_search",
            label_visibility="collapsed",
        )
    with filter_col2:
        status_options = ["All"] + [v["label"] for v in CHANGE_ORDER_STATUSES.values()]
        status_filter = st.selectbox("Status", status_options, key="co_status_filter", label_visibility="collapsed")
    with filter_col3:
        if st.button("\u2795 New Change Order", type="primary", key="btn_new_co"):
            st.session_state.svc_show_new_co = True
            st.rerun()

    # New change order form
    if st.session_state.get("svc_show_new_co", False):
        _render_new_ticket_form("change_order")

    # Filter
    filtered = list(change_orders)
    if search:
        sl = search.lower()
        filtered = [t for t in filtered if sl in t.get("title", "").lower() or sl in t.get("client_name", "").lower() or sl in _get_project_name(t.get("project_id", "")).lower()]
    if status_filter != "All":
        status_key = next((k for k, v in CHANGE_ORDER_STATUSES.items() if v["label"] == status_filter), None)
        if status_key:
            filtered = [t for t in filtered if t.get("status") == status_key]

    # List
    if not filtered:
        st.info("No change orders found. Create one to get started!")
        return

    st.markdown(f"**Showing {len(filtered)} change order(s)**")

    for ticket in filtered:
        _render_ticket_card(ticket, CHANGE_ORDER_STATUSES)


# ============================================
# MAINTENANCE TAB
# ============================================

def render_maintenance_tab(tickets):
    """Render the Maintenance tab."""
    maintenance = [t for t in tickets if t.get("ticket_type") == "maintenance"]

    filter_col1, filter_col2, filter_col3 = st.columns([2, 1, 1])
    with filter_col1:
        search = st.text_input(
            "\U0001f50d Search maintenance...",
            placeholder="Title, type, or project",
            key="maint_search",
            label_visibility="collapsed",
        )
    with filter_col2:
        status_options = ["All"] + [v["label"] for v in MAINTENANCE_STATUSES.values()]
        status_filter = st.selectbox("Status", status_options, key="maint_status_filter", label_visibility="collapsed")
    with filter_col3:
        if st.button("\u2795 New Maintenance Task", type="primary", key="btn_new_maint"):
            st.session_state.svc_show_new_maint = True
            st.rerun()

    # New maintenance form
    if st.session_state.get("svc_show_new_maint", False):
        _render_new_ticket_form("maintenance")

    # Filter
    filtered = list(maintenance)
    if search:
        sl = search.lower()
        filtered = [t for t in filtered if sl in t.get("title", "").lower() or sl in (t.get("maintenance_type") or "").lower() or sl in _get_project_name(t.get("project_id", "")).lower()]
    if status_filter != "All":
        status_key = next((k for k, v in MAINTENANCE_STATUSES.items() if v["label"] == status_filter), None)
        if status_key:
            filtered = [t for t in filtered if t.get("status") == status_key]

    if not filtered:
        st.info("No maintenance tasks found. Schedule proactive work to keep apps healthy!")
        return

    st.markdown(f"**Showing {len(filtered)} maintenance task(s)**")

    for ticket in filtered:
        _render_ticket_card(ticket, MAINTENANCE_STATUSES)


# ============================================
# SERVICE TICKETS TAB
# ============================================

def render_service_tickets_tab(tickets):
    """Render the Service Tickets tab."""
    service_tix = [t for t in tickets if t.get("ticket_type") == "service"]

    filter_col1, filter_col2, filter_col3 = st.columns([2, 1, 1])
    with filter_col1:
        search = st.text_input(
            "\U0001f50d Search service tickets...",
            placeholder="Title, subscriber, or product",
            key="svc_search",
            label_visibility="collapsed",
        )
    with filter_col2:
        status_options = ["All"] + [v["label"] for v in SERVICE_STATUSES.values()]
        status_filter = st.selectbox("Status", status_options, key="svc_status_filter", label_visibility="collapsed")
    with filter_col3:
        if st.button("\u2795 New Service Ticket", type="primary", key="btn_new_svc"):
            st.session_state.svc_show_new_svc = True
            st.rerun()

    # New service ticket form
    if st.session_state.get("svc_show_new_svc", False):
        _render_new_ticket_form("service")

    # Cost summary banner
    total_svc_hours = sum(_safe_num(t.get("actual_hours")) for t in service_tix)
    total_svc_cost = sum(_safe_num(t.get("actual_hours")) * _safe_num(t.get("hourly_rate"), DEFAULT_HOURLY_RATE) for t in service_tix)
    if total_svc_hours > 0:
        st.warning(
            f"\U0001f4b8 **Service Cost Center:** {total_svc_hours:.1f} hours \u00d7 ${DEFAULT_HOURLY_RATE:.0f}/hr = "
            f"**${total_svc_cost:,.0f}** absorbed by MPT (not billed to subscribers)"
        )

    # Filter
    filtered = list(service_tix)
    if search:
        sl = search.lower()
        filtered = [t for t in filtered if sl in t.get("title", "").lower() or sl in (t.get("requested_by") or "").lower() or sl in _get_project_name(t.get("project_id", "")).lower()]
    if status_filter != "All":
        status_key = next((k for k, v in SERVICE_STATUSES.items() if v["label"] == status_filter), None)
        if status_key:
            filtered = [t for t in filtered if t.get("status") == status_key]

    if not filtered:
        st.info("No service tickets found. That\u2019s a good sign \u2014 subscribers are happy!")
        return

    st.markdown(f"**Showing {len(filtered)} service ticket(s)**")

    for ticket in filtered:
        _render_ticket_card(ticket, SERVICE_STATUSES)


# ============================================
# SHARED COMPONENTS
# ============================================

def _render_ticket_card(ticket, status_map):
    """Render a single ticket card."""
    ticket_id = ticket.get("id", "")
    ticket_type = ticket.get("ticket_type", "change_order")
    status = ticket.get("status", "open")
    status_info = status_map.get(status, {"label": status, "icon": "\u2753", "color": "#6c757d"})
    priority = ticket.get("priority", "medium")
    priority_info = PRIORITY_CONFIG.get(priority, PRIORITY_CONFIG["medium"])

    estimated = _safe_num(ticket.get("estimated_hours"))
    actual = _safe_num(ticket.get("actual_hours"))
    rate = _safe_num(ticket.get("hourly_rate"), DEFAULT_HOURLY_RATE)
    amount = actual * rate
    is_billable = ticket.get("is_billable", True)

    with st.container(border=True):
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

        with col1:
            st.markdown(f"**{status_info['icon']} {ticket.get('title', 'Untitled')}**")
            project_name = _get_project_name(ticket.get("project_id"))
            client = ticket.get("client_name", "")
            subtitle_parts = []
            if project_name != "N/A":
                subtitle_parts.append(project_name)
            if client:
                subtitle_parts.append(client)
            subtitle = " \u00b7 ".join(subtitle_parts) if subtitle_parts else "No project linked"

            # Add maintenance type if applicable
            if ticket_type == "maintenance" and ticket.get("maintenance_type"):
                mtype = MAINTENANCE_TYPES.get(ticket["maintenance_type"], {"label": ticket["maintenance_type"], "icon": "\U0001f527"})
                subtitle = f"{mtype['icon']} {mtype['label']} \u00b7 {subtitle}"

            # Add requester for service tickets
            if ticket_type == "service" and ticket.get("requested_by"):
                subtitle = f"\U0001f464 {ticket['requested_by']} \u00b7 {subtitle}"

            st.caption(f"{priority_info['icon']} {priority_info['label']} \u00b7 {subtitle}")

        with col2:
            if estimated > 0:
                pct = min(actual / estimated, 1.0) if estimated > 0 else 0
                st.markdown(f"\u23f1\ufe0f {actual:.1f} / {estimated:.1f} hrs ({pct * 100:.0f}%)")
                st.progress(pct)
            else:
                st.markdown(f"\u23f1\ufe0f {actual:.1f} hours logged")

        with col3:
            if is_billable:
                st.markdown(f"\U0001f4b0 **${amount:,.0f}**")
                st.caption("Billable")
            else:
                st.markdown(f"\U0001f4b8 **${amount:,.0f}**")
                st.caption("Cost (MPT absorbs)")

        with col4:
            if st.button("Edit", key=f"edit_{ticket_id}"):
                st.session_state.svc_editing = ticket_id
                st.rerun()

    # Inline edit panel
    if st.session_state.get("svc_editing") == ticket_id:
        _render_edit_panel(ticket, status_map)


def _render_edit_panel(ticket, status_map):
    """Render inline edit panel for a ticket."""
    ticket_id = ticket.get("id", "")
    ticket_type = ticket.get("ticket_type", "change_order")

    with st.container(border=True):
        st.markdown(f"#### \u270f\ufe0f Edit: {ticket.get('title', '')}")

        col1, col2 = st.columns(2)

        with col1:
            new_title = st.text_input("Title", value=ticket.get("title", ""), key=f"edit_title_{ticket_id}")
            new_desc = st.text_area("Description", value=ticket.get("description", ""), height=80, key=f"edit_desc_{ticket_id}")

            # Status
            status_keys = list(status_map.keys())
            status_labels = [f"{status_map[s]['icon']} {status_map[s]['label']}" for s in status_keys]
            current_status_idx = status_keys.index(ticket.get("status", status_keys[0])) if ticket.get("status") in status_keys else 0
            new_status_label = st.selectbox("Status", status_labels, index=current_status_idx, key=f"edit_status_{ticket_id}")
            new_status = status_keys[status_labels.index(new_status_label)]

            # Priority
            priority_keys = list(PRIORITY_CONFIG.keys())
            priority_labels = [f"{PRIORITY_CONFIG[p]['icon']} {PRIORITY_CONFIG[p]['label']}" for p in priority_keys]
            current_priority_idx = priority_keys.index(ticket.get("priority", "medium")) if ticket.get("priority") in priority_keys else 1
            new_priority_label = st.selectbox("Priority", priority_labels, index=current_priority_idx, key=f"edit_priority_{ticket_id}")
            new_priority = priority_keys[priority_labels.index(new_priority_label)]

        with col2:
            new_est = st.number_input("Estimated Hours", min_value=0.0, step=0.5, value=_safe_num(ticket.get("estimated_hours")), key=f"edit_est_{ticket_id}")
            new_actual = st.number_input("Actual Hours", min_value=0.0, step=0.25, value=_safe_num(ticket.get("actual_hours")), key=f"edit_actual_{ticket_id}")
            new_rate = st.number_input("Hourly Rate ($)", min_value=0.0, step=25.0, value=_safe_num(ticket.get("hourly_rate"), DEFAULT_HOURLY_RATE), key=f"edit_rate_{ticket_id}")

            # Show calculated amount
            calc_amount = new_actual * new_rate
            is_billable = ticket.get("is_billable", True)
            if is_billable:
                st.info(f"\U0001f4b0 Billable Amount: **${calc_amount:,.2f}**")
            else:
                st.warning(f"\U0001f4b8 Cost to MPT: **${calc_amount:,.2f}**")

            # Maintenance type (only for maintenance tickets)
            new_maint_type = None
            if ticket_type == "maintenance":
                mtype_keys = list(MAINTENANCE_TYPES.keys())
                mtype_labels = [f"{MAINTENANCE_TYPES[m]['icon']} {MAINTENANCE_TYPES[m]['label']}" for m in mtype_keys]
                current_mtype = ticket.get("maintenance_type", "other")
                current_mtype_idx = mtype_keys.index(current_mtype) if current_mtype in mtype_keys else len(mtype_keys) - 1
                new_mtype_label = st.selectbox("Maintenance Type", mtype_labels, index=current_mtype_idx, key=f"edit_mtype_{ticket_id}")
                new_maint_type = mtype_keys[mtype_labels.index(new_mtype_label)]

            # Requested by (for change orders and service tickets)
            new_requested_by = None
            if ticket_type in ("change_order", "service"):
                rb_label = "Requested By" if ticket_type == "change_order" else "Reported By"
                new_requested_by = st.text_input(rb_label, value=ticket.get("requested_by", "") or "", key=f"edit_rb_{ticket_id}")

        # Action buttons
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        with btn_col1:
            if st.button("\U0001f4be Save Changes", type="primary", key=f"save_{ticket_id}"):
                # Update ticket in session state
                for t in st.session_state.svc_tickets:
                    if t.get("id") == ticket_id:
                        t["title"] = new_title
                        t["description"] = new_desc
                        t["status"] = new_status
                        t["priority"] = new_priority
                        t["estimated_hours"] = new_est
                        t["actual_hours"] = new_actual
                        t["hourly_rate"] = new_rate
                        t["updated_at"] = datetime.now().isoformat()
                        if new_maint_type is not None:
                            t["maintenance_type"] = new_maint_type
                        if new_requested_by is not None:
                            t["requested_by"] = new_requested_by
                        if new_status in ("completed", "billed", "resolved", "closed") and not t.get("completed_at"):
                            t["completed_at"] = datetime.now().isoformat()
                        break

                # Try DB update
                if db_is_connected() and not str(ticket_id).startswith("svc-ticket-"):
                    update_data = {
                        "title": new_title,
                        "description": new_desc,
                        "status": new_status,
                        "priority": new_priority,
                        "estimated_hours": new_est,
                        "actual_hours": new_actual,
                        "hourly_rate": new_rate,
                    }
                    if new_maint_type is not None:
                        update_data["maintenance_type"] = new_maint_type
                    if new_requested_by is not None:
                        update_data["requested_by"] = new_requested_by
                    db_update_service_ticket(ticket_id, update_data)

                st.success("Ticket updated!")
                st.session_state.svc_editing = None
                st.rerun()

        with btn_col2:
            if st.button("Cancel", key=f"cancel_{ticket_id}"):
                st.session_state.svc_editing = None
                st.rerun()

        with btn_col3:
            pass  # Reserved for future delete button


def _render_new_ticket_form(ticket_type):
    """Render the new ticket creation form."""
    type_info = TICKET_TYPES.get(ticket_type, TICKET_TYPES["change_order"])
    status_map = _get_status_map(ticket_type)
    form_key = f"new_{ticket_type}_form"
    session_key = {
        "change_order": "svc_show_new_co",
        "maintenance": "svc_show_new_maint",
        "service": "svc_show_new_svc",
    }.get(ticket_type, "svc_show_new_co")

    st.markdown("---")
    st.markdown(f"### {type_info['icon']} New {type_info['label']}")

    with st.form(form_key):
        col1, col2 = st.columns(2)

        with col1:
            title = st.text_input("Title *", placeholder=f"Brief description of the {type_info['label'].lower()}")
            description = st.text_area("Description", placeholder="Detailed description of the work needed...", height=100)

            # Project dropdown
            project_options = _get_project_options()
            project_ids = list(project_options.keys())
            project_labels = list(project_options.values())
            selected_project_label = st.selectbox("Linked Project", project_labels)
            selected_project_id = project_ids[project_labels.index(selected_project_label)]

            # Priority
            priority_keys = list(PRIORITY_CONFIG.keys())
            priority_labels = [f"{PRIORITY_CONFIG[p]['icon']} {PRIORITY_CONFIG[p]['label']}" for p in priority_keys]
            selected_priority_label = st.selectbox("Priority", priority_labels, index=1)  # Default medium
            selected_priority = priority_keys[priority_labels.index(selected_priority_label)]

        with col2:
            estimated_hours = st.number_input("Estimated Hours", min_value=0.0, step=0.5, value=1.0)

            if estimated_hours > 0:
                est_amount = estimated_hours * DEFAULT_HOURLY_RATE
                if type_info["billable"]:
                    st.info(f"\U0001f4b0 Estimated billable: **${est_amount:,.2f}**")
                else:
                    st.warning(f"\U0001f4b8 Estimated cost to MPT: **${est_amount:,.2f}**")

            # Type-specific fields
            maintenance_type_val = None
            requested_by_val = None

            if ticket_type == "maintenance":
                mtype_keys = list(MAINTENANCE_TYPES.keys())
                mtype_labels = [f"{MAINTENANCE_TYPES[m]['icon']} {MAINTENANCE_TYPES[m]['label']}" for m in mtype_keys]
                selected_mtype_label = st.selectbox("Maintenance Type", mtype_labels)
                maintenance_type_val = mtype_keys[mtype_labels.index(selected_mtype_label)]

            if ticket_type == "change_order":
                requested_by_val = st.text_input("Requested By", placeholder="Client name or contact")

            if ticket_type == "service":
                requested_by_val = st.text_input("Reported By", placeholder="Subscriber email or name")

            client_name = st.text_input("Client Name", value=CLIENT_NAME)

        col_submit, col_cancel = st.columns(2)
        with col_submit:
            submitted = st.form_submit_button(f"Create {type_info['label']}", type="primary", use_container_width=True)
        with col_cancel:
            cancelled = st.form_submit_button("Cancel", use_container_width=True)

        if submitted and title:
            # Determine initial status
            initial_status = list(status_map.keys())[0]

            new_ticket = {
                "id": f"svc-{ticket_type[:3]}-{len(st.session_state.svc_tickets) + 1}-{datetime.now().strftime('%H%M%S')}",
                "title": title,
                "description": description,
                "ticket_type": ticket_type,
                "project_id": selected_project_id if selected_project_id else None,
                "client_name": client_name,
                "status": initial_status,
                "priority": selected_priority,
                "estimated_hours": estimated_hours,
                "actual_hours": 0,
                "hourly_rate": DEFAULT_HOURLY_RATE,
                "is_billable": type_info["billable"],
                "requested_by": requested_by_val,
                "maintenance_type": maintenance_type_val,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "completed_at": None,
            }

            # Try DB save
            if db_is_connected():
                db_data = {k: v for k, v in new_ticket.items() if k != "id"}
                result = db_create_service_ticket(db_data)
                if result:
                    new_ticket["id"] = result.get("id", new_ticket["id"])

            st.session_state.svc_tickets.append(new_ticket)
            st.success(f"{type_info['label']} '{title}' created!")
            st.session_state[session_key] = False
            st.rerun()

        if cancelled:
            st.session_state[session_key] = False
            st.rerun()


# ============================================
# MAIN PAGE
# ============================================
st.title("\U0001f527 Service")

# Dashboard metrics
render_service_dashboard(st.session_state.svc_tickets)

st.markdown("---")

# Sidebar stats
closed_statuses = {"completed", "billed", "resolved", "closed"}
open_tickets = [t for t in st.session_state.svc_tickets if t.get("status") not in closed_statuses]
billable_total = sum(
    _safe_num(t.get("actual_hours")) * _safe_num(t.get("hourly_rate"), DEFAULT_HOURLY_RATE)
    for t in st.session_state.svc_tickets if t.get("is_billable", True)
)
total_hours = sum(_safe_num(t.get("actual_hours")) for t in st.session_state.svc_tickets)

render_sidebar_stats({
    "Total Tickets": str(len(st.session_state.svc_tickets)),
    "Open": str(len(open_tickets)),
    "Billable Revenue": f"${billable_total:,.0f}",
    "Total Hours": f"{total_hours:.1f}",
})

# Tabs
tab_co, tab_maint, tab_svc = st.tabs([
    "\U0001f4dd Change Orders",
    "\U0001f6e0\ufe0f Maintenance",
    "\U0001f3ab Service Tickets",
])

with tab_co:
    render_change_orders_tab(st.session_state.svc_tickets)

with tab_maint:
    render_maintenance_tab(st.session_state.svc_tickets)

with tab_svc:
    render_service_tickets_tab(st.session_state.svc_tickets)
