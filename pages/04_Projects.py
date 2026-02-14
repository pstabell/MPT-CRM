"""
MPT-CRM Projects Page
Manage client projects with status tracking, time logging, and billing

Real MPT project portfolio with pricing at $150/hr.
Database operations are handled by db_service.py - the single source of truth.
"""

import streamlit as st
from datetime import datetime, date, timedelta
from db_service import (
    db_is_connected, db_get_contact_email, db_get_projects,
    db_create_project, db_update_project, db_delete_project,
    db_get_project, db_get_project_time_entries,
    db_change_project_status, db_get_project_history, db_can_log_time_to_project,
    db_notify_mission_control_project_status,
    db_get_project_change_orders, db_create_change_order, db_update_change_order
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
    "Change Orders": {"icon": "📝", "path": "pages/06_Change_Orders.py"},
    "Time & Billing": {"icon": "\U0001f4b0", "path": "pages/06_Time_Billing.py"},
    "Marketing": {"icon": "\U0001f4e7", "path": "pages/07_Marketing.py"},
    "Reports": {"icon": "\U0001f4c8", "path": "pages/08_Reports.py"},
    "Settings": {"icon": "\u2699\ufe0f", "path": "pages/09_Settings.py"},
    "Help": {"icon": "❓", "path": "pages/11_Help.py"},
}

def render_sidebar(current_page="Projects"):
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
    page_title="MPT-CRM - Projects",
    page_icon="favicon.jpg",
    layout="wide"
)

require_sso_auth(allow_bypass=False)

# ============================================
# RENDER SIDEBAR
# ============================================
render_sidebar("Projects")

# ============================================
# CONSTANTS
# ============================================
DEFAULT_HOURLY_RATE = 150.00
CLIENT_NAME = "Metro Point Technology LLC"

# Project type definitions
PROJECT_TYPES = {
    "product": {"label": "Product", "icon": "\U0001f3f7\ufe0f"},
    "project": {"label": "Project", "icon": "\U0001f527"},
    "website": {"label": "Website", "icon": "\U0001f310"},
}

# Project status definitions
PROJECT_STATUS = {
    "planning": {"label": "Planning", "icon": "\U0001f4cb", "color": "#6c757d"},
    "active": {"label": "Active", "icon": "\U0001f680", "color": "#28a745"},
    "on-hold": {"label": "On Hold", "icon": "\u23f8\ufe0f", "color": "#ffc107"},
    "voided": {"label": "Voided", "icon": "\u274c", "color": "#dc3545"},
    "completed": {"label": "Completed", "icon": "\u2705", "color": "#17a2b8"},
    "maintenance": {"label": "Maintenance", "icon": "\U0001f6e0\ufe0f", "color": "#6f42c1"},
}

# ============================================
# DEFAULT MPT PROJECT DATA
# ============================================
DEFAULT_PROJECTS = [
    {
        "id": "mpt-proj-1",
        "name": "AMS-APP",
        "client": CLIENT_NAME,
        "client_name": CLIENT_NAME,
        "project_type": "product",
        "status": "active",
        "description": "Agency Management System - Flagship product. Agent Commission Tracker (ACT) at v3.9.32 production-ready. Agency Platform branch in active development. Full insurance agency operations platform with commission tracking, carrier management, and reporting. Tech: Streamlit, Python, Supabase.",
        "estimated_hours": 800,
        "hours_logged": 500,
        "hourly_rate": DEFAULT_HOURLY_RATE,
        "start_date": "2024-06-01",
        "target_end_date": "2026-06-30",
    },
    {
        "id": "mpt-proj-2",
        "name": "CRM-APP",
        "client": CLIENT_NAME,
        "client_name": CLIENT_NAME,
        "project_type": "product",
        "status": "planning",
        "description": "Insurance Agent CRM - Purpose-built CRM for insurance agents. ACORD forms integration, quote automation, sales pipeline management, drip email campaigns, and client communication tracking. Tech: Streamlit, Python, Supabase, SendGrid.",
        "estimated_hours": 600,
        "hours_logged": 80,
        "hourly_rate": DEFAULT_HOURLY_RATE,
        "start_date": "2025-10-01",
        "target_end_date": "2026-09-30",
    },
    {
        "id": "mpt-proj-3",
        "name": "WRAP Proposal Generator",
        "client": CLIENT_NAME,
        "client_name": CLIENT_NAME,
        "project_type": "product",
        "status": "maintenance",
        "description": "Insurance proposal generator - FREE lead magnet tool published on MPTech website. Generates professional insurance proposals to attract agency leads. Drives traffic and captures contact info for the sales pipeline. Fully functional - changes handled via work orders.",
        "estimated_hours": 120,
        "hours_logged": 120,
        "hourly_rate": DEFAULT_HOURLY_RATE,
        "start_date": "2025-11-01",
        "target_end_date": "2026-03-31",
    },
    {
        "id": "mpt-proj-4",
        "name": "MPT-CRM",
        "client": CLIENT_NAME,
        "client_name": CLIENT_NAME,
        "project_type": "project",
        "status": "active",
        "description": "Metro Point Technology's internal CRM - This app! 9+ pages including Discovery, Contacts, Pipeline, Projects, Tasks, Time & Billing, Marketing, Reports, and Settings. Mobile business card scanner, SendGrid email integration, Supabase backend. The single source of truth for project management and billing.",
        "estimated_hours": 500,
        "hours_logged": 200,
        "hourly_rate": DEFAULT_HOURLY_RATE,
        "start_date": "2025-12-01",
        "target_end_date": "2026-06-30",
    },
    {
        "id": "mpt-proj-5",
        "name": "MetroPointTech.com",
        "client": CLIENT_NAME,
        "client_name": CLIENT_NAME,
        "project_type": "website",
        "status": "active",
        "description": "Products showcase website - Public-facing site highlighting MPT's software products (AMS-APP, CRM-APP, WRAP). Product demos, pricing, feature breakdowns, and lead capture forms.",
        "estimated_hours": 80,
        "hours_logged": 20,
        "hourly_rate": DEFAULT_HOURLY_RATE,
        "start_date": "2026-01-01",
        "target_end_date": "2026-03-31",
    },
    {
        "id": "mpt-proj-6",
        "name": "MetroPointTechnology.com",
        "client": CLIENT_NAME,
        "client_name": CLIENT_NAME,
        "project_type": "website",
        "status": "planning",
        "description": "Services & consulting website - Professional services site for Metro Point Technology LLC. Custom development, consulting engagements, technology advisory, and support packages.",
        "estimated_hours": 80,
        "hours_logged": 10,
        "hourly_rate": DEFAULT_HOURLY_RATE,
        "start_date": "2026-01-15",
        "target_end_date": "2026-04-30",
    },
]

# ============================================
# INITIALIZE SESSION STATE
# ============================================

def _safe_num(val, default=0):
    """Return val if it's a number, otherwise default."""
    if val is None:
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def load_projects():
    """Load projects from database first, fall back to defaults.
    
    ALWAYS use database if connected and has data. Never fall back to
    hardcoded defaults when live data exists - that causes sync issues.
    """
    if db_is_connected():
        try:
            db_projects = db_get_projects()
            if db_projects:
                # ALWAYS use DB data when available - fill in missing values with defaults
                for p in db_projects:
                    # Force-replace None values (setdefault won't replace existing None keys)
                    p['hourly_rate'] = _safe_num(p.get('hourly_rate'), DEFAULT_HOURLY_RATE)
                    p['estimated_hours'] = _safe_num(p.get('estimated_hours'), 0)
                    p['hours_logged'] = _safe_num(p.get('hours_logged'), 0)
                    p['project_type'] = p.get('project_type') or 'project'
                    p['client_name'] = p.get('client_name') or CLIENT_NAME
                    p['client'] = p.get('client') or p.get('client_name') or CLIENT_NAME
                return db_projects
        except Exception as e:
            print(f"[Projects] DB load failed, using defaults: {e}")
    return [dict(p) for p in DEFAULT_PROJECTS]


# Force reload when code version changes (clears stale session state)
_CODE_VERSION = "v9-debug-all-projects"
if st.session_state.get('proj_code_version') != _CODE_VERSION:
    st.session_state.proj_projects = load_projects()
    st.session_state.proj_code_version = _CODE_VERSION
    st.session_state.proj_selected_project = None
    st.session_state.proj_show_new_form = False

if 'proj_projects' not in st.session_state:
    st.session_state.proj_projects = load_projects()

if 'proj_time_entries' not in st.session_state:
    st.session_state.proj_time_entries = []

if 'proj_selected_project' not in st.session_state:
    st.session_state.proj_selected_project = None

if 'proj_show_new_form' not in st.session_state:
    st.session_state.proj_show_new_form = False

if 'show_stop_modal' not in st.session_state:
    st.session_state.show_stop_modal = False

if 'show_void_modal' not in st.session_state:
    st.session_state.show_void_modal = False


# ============================================
# HELPER FUNCTIONS
# ============================================

def calc_project_value(project):
    """Calculate project value = estimated_hours x hourly_rate"""
    return _safe_num(project.get('estimated_hours'), 0) * _safe_num(project.get('hourly_rate'), DEFAULT_HOURLY_RATE)


def calc_revenue_earned(project):
    """Calculate revenue earned = hours_logged x hourly_rate"""
    return _safe_num(project.get('hours_logged'), 0) * _safe_num(project.get('hourly_rate'), DEFAULT_HOURLY_RATE)


def get_type_badge(project_type):
    """Get the display badge for a project type."""
    info = PROJECT_TYPES.get(project_type, PROJECT_TYPES['project'])
    return f"{info['icon']} {info['label']}"


# ============================================
# FINANCIAL DASHBOARD
# ============================================

def render_financial_dashboard(projects):
    """Render the portfolio financial dashboard at the top of the page."""
    total_estimated_hours = sum(p.get('estimated_hours', 0) or 0 for p in projects)
    total_hours_logged = sum(p.get('hours_logged', 0) or 0 for p in projects)
    total_portfolio_value = sum(calc_project_value(p) for p in projects)
    total_revenue_earned = sum(calc_revenue_earned(p) for p in projects)
    hours_remaining = total_estimated_hours - total_hours_logged
    remaining_value = hours_remaining * DEFAULT_HOURLY_RATE

    st.markdown("### \U0001f4bc MPT Portfolio Dashboard")
    st.caption(f"All projects billed at ${DEFAULT_HOURLY_RATE:.0f}/hr \u00b7 {CLIENT_NAME}")

    # Top-line financials
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("\U0001f4ca Portfolio Value", f"${total_portfolio_value:,.0f}")
    with col2:
        st.metric("\u23f1\ufe0f Hours Estimated", f"{total_estimated_hours:,.0f}")
    with col3:
        st.metric("\u23f1\ufe0f Hours Invested", f"{total_hours_logged:,.0f}")
    with col4:
        st.metric("\U0001f4b5 Revenue Earned", f"${total_revenue_earned:,.0f}")

    # Progress bar
    if total_estimated_hours > 0:
        overall_pct = total_hours_logged / total_estimated_hours
        st.progress(min(overall_pct, 1.0))
        st.caption(f"Overall progress: {overall_pct * 100:.1f}% complete \u00b7 {hours_remaining:,.0f} hours remaining \u00b7 ${remaining_value:,.0f} remaining value")

    # Breakdown by type
    st.markdown("---")
    type_cols = st.columns(3)
    for i, (type_key, type_info) in enumerate(PROJECT_TYPES.items()):
        type_projects = [p for p in projects if p.get('project_type') == type_key]
        type_value = sum(calc_project_value(p) for p in type_projects)
        type_hours = sum(p.get('estimated_hours', 0) or 0 for p in type_projects)
        type_logged = sum(p.get('hours_logged', 0) or 0 for p in type_projects)
        with type_cols[i]:
            with st.container(border=True):
                st.markdown(f"**{type_info['icon']} {type_info['label']}s** ({len(type_projects)})")
                st.markdown(f"Value: **${type_value:,.0f}**")
                st.caption(f"{type_logged:,.0f} / {type_hours:,.0f} hours")


# ============================================
# NEW PROJECT FORM
# ============================================

def show_new_project_form():
    """Show form to create a new project"""
    st.markdown("---")
    st.markdown("## \u2795 New Project")

    prefill_name = st.session_state.get('new_project_name', '')
    prefill_client = st.session_state.get('new_project_client', CLIENT_NAME)
    prefill_contact_id = st.session_state.get('new_project_contact_id', None)
    prefill_deal_id = st.session_state.get('new_project_deal_id', None)

    if prefill_name:
        st.success(f"Creating project from won deal: **{prefill_name}**")

    with st.form("new_project_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Project Name *", value=prefill_name, placeholder="e.g., AMS-APP")
            client = st.text_input("Client *", value=prefill_client, placeholder="Company or contact name")
            project_type = st.selectbox(
                "Project Type *",
                list(PROJECT_TYPES.keys()),
                format_func=lambda x: f"{PROJECT_TYPES[x]['icon']} {PROJECT_TYPES[x]['label']}"
            )
            description = st.text_area("Description", placeholder="Brief description of the project scope...")

        with col2:
            estimated_hours = st.number_input("Estimated Hours", min_value=0.0, step=10.0, value=0.0)
            hourly_rate = st.number_input("Hourly Rate ($)", min_value=0.0, step=25.0, value=DEFAULT_HOURLY_RATE)

            # Show calculated value
            if estimated_hours > 0:
                calc_value = estimated_hours * hourly_rate
                st.info(f"\U0001f4b0 Project Value: **${calc_value:,.2f}**")

            start_date = st.date_input("Start Date", value=date.today())
            target_end_date = st.date_input("Target End Date", value=date.today() + timedelta(days=90))
            status = st.selectbox("Initial Status", ["planning", "active"], format_func=lambda x: PROJECT_STATUS[x]['label'])

        col_submit, col_cancel = st.columns(2)
        with col_submit:
            submitted = st.form_submit_button("Create Project", type="primary", use_container_width=True)
        with col_cancel:
            cancelled = st.form_submit_button("Cancel", use_container_width=True)

        if submitted and name and client:
            budget = estimated_hours * hourly_rate
            new_project = {
                "id": f"proj-{len(st.session_state.proj_projects) + 1}-{datetime.now().strftime('%H%M%S')}",
                "name": name,
                "client": client,
                "client_name": client,
                "client_id": prefill_contact_id,
                "deal_id": prefill_deal_id,
                "project_type": project_type,
                "status": status,
                "description": description,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "target_end_date": target_end_date.strftime("%Y-%m-%d"),
                "estimated_hours": estimated_hours,
                "hours_logged": 0,
                "hourly_rate": hourly_rate,
                "budget": budget,
            }

            # Try to save to database - only include columns that exist in DB
            if db_is_connected():
                # DB columns: name, client_id, deal_id, status, description, 
                # start_date, target_end_date, budget, estimated_hours
                db_data = {
                    'name': name,
                    'client_id': prefill_contact_id,
                    'deal_id': prefill_deal_id,
                    'status': status,
                    'description': description,
                    'start_date': start_date.strftime("%Y-%m-%d"),
                    'target_end_date': target_end_date.strftime("%Y-%m-%d"),
                    'budget': budget,
                    'estimated_hours': estimated_hours,
                }
                # Remove None values to avoid insert errors
                db_data = {k: v for k, v in db_data.items() if v is not None}
                result = db_create_project(db_data)
                if result:
                    new_project['id'] = result.get('id', new_project['id'])

            st.session_state.proj_projects.append(new_project)
            st.success(f"Project '{name}' created! Value: ${budget:,.2f}")
            st.session_state.proj_show_new_form = False
            for key in ['new_project_name', 'new_project_client', 'new_project_contact_id', 'new_project_deal_id', 'new_project_budget']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

        if cancelled:
            st.session_state.proj_show_new_form = False
            for key in ['new_project_name', 'new_project_client', 'new_project_contact_id', 'new_project_deal_id', 'new_project_budget']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()


# ============================================
# PROJECT DETAIL VIEW
# ============================================

def show_project_detail(project_id):
    """Show detailed project view with pricing and time entries."""
    project = next((p for p in st.session_state.proj_projects if p['id'] == project_id), None)
    if not project:
        st.session_state.proj_selected_project = None
        st.rerun()
        return

    status_info = PROJECT_STATUS.get(project['status'], PROJECT_STATUS['active'])
    type_info = PROJECT_TYPES.get(project.get('project_type', 'project'), PROJECT_TYPES['project'])

    # Status Banner (for on-hold and voided projects)
    if project['status'] == 'on-hold':
        st.warning(f"⚠️ **Project On Hold** - {project.get('status_reason', 'No reason provided')}")
    elif project['status'] == 'voided':
        st.error(f"🚫 **Project Voided** - {project.get('status_reason', 'No reason provided')} (Read-only)")

    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"## {status_info['icon']} {project['name']}")
        st.markdown(f"**{type_info['icon']} {type_info['label']}** \u00b7 {project.get('client', CLIENT_NAME)}")
    with col2:
        if st.button("\u2190 Back to Projects"):
            st.session_state.proj_selected_project = None
            st.rerun()

    st.markdown("---")

    # Financial summary bar
    project_value = calc_project_value(project)
    revenue = calc_revenue_earned(project)
    hours_logged = project.get('hours_logged', 0) or 0
    estimated_hours = project.get('estimated_hours', 0) or 0
    hours_remaining = estimated_hours - hours_logged
    remaining_value = hours_remaining * (project.get('hourly_rate', DEFAULT_HOURLY_RATE) or DEFAULT_HOURLY_RATE)

    fin_cols = st.columns(4)
    with fin_cols[0]:
        st.metric("\U0001f4b0 Project Value", f"${project_value:,.0f}")
    with fin_cols[1]:
        st.metric("\U0001f4b5 Revenue Earned", f"${revenue:,.0f}")
    with fin_cols[2]:
        st.metric("\u23f1\ufe0f Hours", f"{hours_logged:,.0f} / {estimated_hours:,.0f}")
    with fin_cols[3]:
        st.metric("\U0001f4c9 Remaining", f"${remaining_value:,.0f}")

    if estimated_hours > 0:
        progress_pct = min(hours_logged / estimated_hours, 1.0)
        st.progress(progress_pct)
        st.caption(f"{progress_pct * 100:.1f}% complete \u00b7 {hours_remaining:,.0f} hours remaining")

    st.markdown("---")

    # Main content
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### \U0001f4cb Project Details")
        
        # Show update status from last save attempt
        if 'last_update_status' in st.session_state:
            status_type, status_msg = st.session_state.pop('last_update_status')
            if status_type == 'success':
                st.success(status_msg)
            elif status_type == 'error':
                st.error(status_msg)
            else:
                st.warning(status_msg)
        # Clean up debug info if present
        st.session_state.pop('last_update_debug', None)

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

        # Pricing fields
        st.markdown("### \U0001f4b2 Pricing")
        price_col1, price_col2 = st.columns(2)
        with price_col1:
            new_rate = st.number_input(
                "Hourly Rate ($)",
                min_value=0.0, step=25.0,
                value=float(project.get('hourly_rate', DEFAULT_HOURLY_RATE)),
                key="edit_rate"
            )
        with price_col2:
            new_est_hours = st.number_input(
                "Estimated Hours",
                min_value=0.0, step=10.0,
                value=float(project.get('estimated_hours', 0) or 0),
                key="edit_est_hours"
            )

        # Show calculated value
        new_value = new_est_hours * new_rate
        st.markdown(f"**Project Value:** ${new_value:,.2f}")

        # Save changes button
        if st.button("\U0001f4be Save Changes", type="primary"):
            project['name'] = new_name
            project['description'] = new_desc
            project['hourly_rate'] = new_rate
            project['estimated_hours'] = new_est_hours
            if new_start:
                project['start_date'] = new_start.strftime("%Y-%m-%d")
            if new_end:
                project['target_end_date'] = new_end.strftime("%Y-%m-%d")

            # ALWAYS persist to database - columns matched to actual DB schema
            if db_is_connected():
                update_data = {
                    'name': new_name,
                    'description': new_desc or '',
                    'estimated_hours': new_est_hours,
                    'start_date': project.get('start_date'),
                    'target_end_date': project.get('target_end_date'),
                    # DB has 'budget' not 'hourly_rate' - map it
                    'budget': new_rate,
                }
                result, error = db_update_project(project['id'], update_data)
                if result:
                    st.session_state['last_update_status'] = ('success', "Project updated and saved to database!")
                else:
                    st.session_state['last_update_status'] = ('error', f"Save failed: {error}")
            else:
                st.session_state['last_update_status'] = ('warning', "Database not connected - changes saved locally only.")
            st.rerun()

        # Time entries section
        st.markdown("### \u23f1\ufe0f Time Entries")

        project_entries = []
        if db_is_connected():
            try:
                project_entries = db_get_project_time_entries(project_id)
            except Exception:
                pass

        if not project_entries:
            project_entries = [e for e in st.session_state.proj_time_entries if e.get('project_id') == project_id]

        # Add new time entry
        with st.expander("\u2795 Log Time"):
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
                        "id": f"te-{len(st.session_state.proj_time_entries) + 1}",
                        "project_id": project_id,
                        "date": new_entry_date.strftime("%Y-%m-%d"),
                        "hours": new_entry_hours,
                        "description": new_entry_desc,
                        "billable": new_entry_billable
                    }
                    st.session_state.proj_time_entries.append(new_entry)
                    project['hours_logged'] = (project.get('hours_logged', 0) or 0) + new_entry_hours
                    st.success("Time entry added!")
                    st.rerun()

        # Display time entries
        if project_entries:
            for entry in sorted(project_entries, key=lambda x: x.get('date', ''), reverse=True):
                with st.container(border=True):
                    e_col1, e_col2, e_col3 = st.columns([2, 3, 1])
                    with e_col1:
                        st.markdown(f"**{entry.get('date', 'N/A')}**")
                        st.caption(f"{entry.get('hours', 0)} hours")
                    with e_col2:
                        st.markdown(entry.get('description', ''))
                        if entry.get('billable', True):
                            rate = project.get('hourly_rate', DEFAULT_HOURLY_RATE)
                            st.caption(f"\U0001f4b0 ${entry.get('hours', 0) * rate:,.2f}")
                    with e_col3:
                        if entry.get('billable', True):
                            st.markdown("\u2705 Billable")
                        else:
                            st.markdown("\u2b1c Non-billable")
        else:
            st.info("No time entries yet. Log your first entry above.")
        
        # Change Orders section
        st.markdown("### 📝 Change Orders")
        
        project_change_orders = []
        if db_is_connected():
            try:
                project_change_orders = db_get_project_change_orders(project_id)
            except Exception as e:
                st.warning(f"Could not load change orders: {str(e)}")
        
        # Quick stats
        if project_change_orders:
            co_stats = st.columns(4)
            total_cos = len(project_change_orders)
            pending_cos = len([co for co in project_change_orders if co['status'] == 'pending'])
            approved_cos = len([co for co in project_change_orders if co['status'] == 'approved'])
            total_co_value = sum(float(co['total_amount']) for co in project_change_orders if co.get('total_amount'))
            
            with co_stats[0]:
                st.metric("Total", total_cos)
            with co_stats[1]:
                st.metric("Pending", pending_cos)
            with co_stats[2]:
                st.metric("Approved", approved_cos)
            with co_stats[3]:
                st.metric("Value", f"${total_co_value:,.0f}")
        
        # Add new change order
        with st.expander("➕ New Change Order"):
            with st.form(key=f"new_co_{project_id}"):
                co_title = st.text_input("Title", key=f"co_title_{project_id}")
                co_description = st.text_area("Description", height=80, key=f"co_desc_{project_id}")
                
                co_col1, co_col2 = st.columns(2)
                with co_col1:
                    co_hours = st.number_input("Estimated Hours", min_value=0.0, step=0.5, key=f"co_hours_{project_id}")
                    co_requires_approval = st.checkbox("Requires Client Approval", key=f"co_approval_{project_id}")
                with co_col2:
                    co_rate = st.number_input("Hourly Rate ($)", min_value=0.0, step=1.0, 
                                           value=float(project.get('hourly_rate', 150)), key=f"co_rate_{project_id}")
                    co_impact = st.text_input("Impact Description", key=f"co_impact_{project_id}")
                
                if st.form_submit_button("Create Change Order", type="primary"):
                    if co_title.strip():
                        co_data = {
                            'project_id': project_id,
                            'title': co_title.strip(),
                            'description': co_description.strip() if co_description else None,
                            'status': 'draft',
                            'requested_by': 'Patrick Stabell',
                            'estimated_hours': co_hours if co_hours > 0 else None,
                            'hourly_rate': co_rate,
                            'impact_description': co_impact.strip() if co_impact else None,
                            'requires_client_approval': co_requires_approval
                        }
                        
                        if db_is_connected():
                            result = db_create_change_order(co_data)
                            if result:
                                st.success("Change order created!")
                                st.rerun()
                        else:
                            st.warning("Database not connected - change order not saved")
                    else:
                        st.error("Title is required")
        
        # Display existing change orders
        if project_change_orders:
            for co in sorted(project_change_orders, key=lambda x: x['created_at'], reverse=True):
                status_color = {
                    'draft': '🟡',
                    'pending': '🟠', 
                    'approved': '🟢',
                    'rejected': '🔴',
                    'completed': '🔵'
                }.get(co['status'], '⚪')
                
                with st.container(border=True):
                    co_col1, co_col2, co_col3 = st.columns([3, 2, 1])
                    
                    with co_col1:
                        st.markdown(f"**{co['title']}**")
                        st.caption(f"{status_color} {co['status'].title()}")
                        if co.get('description'):
                            st.markdown(f"*{co['description'][:100]}{'...' if len(co['description']) > 100 else ''}*")
                    
                    with co_col2:
                        if co.get('estimated_hours'):
                            st.caption(f"⏰ {co['estimated_hours']} hours")
                        if co.get('total_amount'):
                            st.caption(f"💰 ${float(co['total_amount']):,.2f}")
                        st.caption(f"📅 {datetime.fromisoformat(co['created_at']).strftime('%m/%d/%Y')}")
                    
                    with co_col3:
                        # Quick action buttons based on status
                        if co['status'] == 'draft':
                            if st.button("📤", help="Submit for approval", key=f"submit_co_{co['id']}"):
                                db_update_change_order(co['id'], {'status': 'pending'})
                                st.rerun()
                        elif co['status'] == 'pending':
                            col_a, col_b = st.columns(2)
                            with col_a:
                                if st.button("✅", help="Approve", key=f"approve_co_{co['id']}"):
                                    db_update_change_order(co['id'], {
                                        'status': 'approved',
                                        'approved_by': 'Patrick Stabell',
                                        'approved_at': datetime.now().isoformat()
                                    })
                                    st.rerun()
                            with col_b:
                                if st.button("❌", help="Reject", key=f"reject_co_{co['id']}"):
                                    db_update_change_order(co['id'], {
                                        'status': 'rejected',
                                        'approved_by': 'Patrick Stabell',
                                        'approved_at': datetime.now().isoformat()
                                    })
                                    st.rerun()
                        elif co['status'] == 'approved':
                            if st.button("🏁", help="Mark complete", key=f"complete_co_{co['id']}"):
                                db_update_change_order(co['id'], {'status': 'completed'})
                                st.rerun()
        else:
            st.info("No change orders yet. Create one above to track scope changes.")
        
        # Link to full Change Orders page
        if st.button("📝 Open Change Orders Page", key=f"open_co_page_{project_id}"):
            st.switch_page("pages/06_Change_Orders.py")

    with col2:
        # Status
        st.markdown("### \U0001f4ca Status")
        status_options = list(PROJECT_STATUS.keys())
        status_labels = [f"{PROJECT_STATUS[s]['icon']} {PROJECT_STATUS[s]['label']}" for s in status_options]
        current_idx = status_options.index(project['status']) if project['status'] in status_options else 0
        new_status_label = st.selectbox("Status", status_labels, index=current_idx, key="edit_status")
        new_status = status_options[status_labels.index(new_status_label)]
        if new_status != project['status']:
            project['status'] = new_status
            if db_is_connected():
                db_update_project(project['id'], {'status': new_status})  # Ignore result for quick status change
            st.rerun()

        # Project type
        st.markdown("### \U0001f3f7\ufe0f Type")
        type_options = list(PROJECT_TYPES.keys())
        type_labels = [f"{PROJECT_TYPES[t]['icon']} {PROJECT_TYPES[t]['label']}" for t in type_options]
        current_type_idx = type_options.index(project.get('project_type', 'project')) if project.get('project_type', 'project') in type_options else 0
        new_type_label = st.selectbox("Project Type", type_labels, index=current_type_idx, key="edit_type")
        new_type = type_options[type_labels.index(new_type_label)]
        if new_type != project.get('project_type'):
            project['project_type'] = new_type

        # Quick financial summary
        st.markdown("### \U0001f4b0 Financial Summary")
        st.metric("Hourly Rate", f"${project.get('hourly_rate', DEFAULT_HOURLY_RATE):,.0f}/hr")
        st.metric("Project Value", f"${project_value:,.0f}")
        st.metric("Revenue Earned", f"${revenue:,.0f}")
        st.metric("Remaining Value", f"${remaining_value:,.0f}")

        if project_value > 0:
            usage = min(revenue / project_value, 1.0)
            st.progress(usage)
            st.caption(f"{usage * 100:.0f}% of value earned")

        # Project Status Actions
        st.markdown("### \u26a1 Project Actions")
        
        current_status = project.get('status', 'active')
        
        # Stop/Resume Project Button
        if current_status == 'active':
            if st.button("\u23f8\ufe0f Stop Project", use_container_width=True, type="secondary"):
                st.session_state.show_stop_modal = True
                st.rerun()
        elif current_status == 'on-hold':
            if st.button("\u25b6\ufe0f Resume Project", use_container_width=True, type="primary"):
                success, error = db_change_project_status(
                    project_id=project['id'],
                    new_status='active',
                    reason='Project resumed',
                    changed_by='Metro Bot'
                )
                if success:
                    project['status'] = 'active'
                    project['status_reason'] = 'Project resumed'
                    db_notify_mission_control_project_status(
                        project['id'], project['name'], 'active', 'Project resumed'
                    )
                    st.success("Project resumed successfully!")
                    st.rerun()
                else:
                    st.error(f"Failed to resume project: {error}")
        
        # Void Project Button (only for active or on-hold projects)
        if current_status in ('active', 'on-hold'):
            if st.button("\u274c Void Project", use_container_width=True):
                st.session_state.show_void_modal = True
                st.rerun()
        
        st.markdown("---")
        
        # Standard Actions
        if st.button("\U0001f4c4 Generate Invoice", use_container_width=True):
            invoice_text = f"""INVOICE
{'='*50}
From: Metro Point Technology LLC
To: {project.get('client', CLIENT_NAME)}
Date: {datetime.now().strftime('%B %d, %Y')}
Project: {project.get('name', 'Project')}
Type: {get_type_badge(project.get('project_type', 'project'))}

Hours Logged: {hours_logged:.1f}
Hourly Rate: ${project.get('hourly_rate', DEFAULT_HOURLY_RATE):,.2f}
Amount Due: ${revenue:,.2f}

Estimated Total: {estimated_hours:.0f} hours
Project Value: ${project_value:,.2f}

Payment Terms: Net 30
{'='*50}
Metro Point Technology LLC
Support@MetroPointTech.com | (239) 600-8159
"""
            st.download_button(
                label="\U0001f4e5 Download Invoice",
                data=invoice_text,
                file_name=f"Invoice_{project.get('name', 'Project').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                key=f"dl_invoice_{project['id']}"
            )

        if st.button("\U0001f4e7 Email Client", use_container_width=True):
            if project.get('client_id') and db_is_connected():
                try:
                    contact_info = db_get_contact_email(project['client_id'])
                    if contact_info and contact_info.get('email'):
                        st.info(f"\U0001f4e7 Draft email to: {contact_info['email']}")
                        st.caption("Use the Marketing page to send emails with templates.")
                    else:
                        st.warning("No email found for this project's contact.")
                except Exception:
                    st.warning("Could not look up contact email.")
            else:
                st.info("\U0001f4a1 Link a contact to this project to enable email.")

        if st.button("\U0001f4ca View Report", use_container_width=True):
            st.markdown(f"""
**Project Report: {project.get('name', 'N/A')}**
- **Type:** {get_type_badge(project.get('project_type', 'project'))}
- **Status:** {status_info['icon']} {status_info['label']}
- **Client:** {project.get('client', CLIENT_NAME)}
- **Hourly Rate:** ${project.get('hourly_rate', DEFAULT_HOURLY_RATE):,.2f}/hr
- **Estimated Hours:** {estimated_hours:,.0f}
- **Hours Logged:** {hours_logged:,.1f}
- **Hours Remaining:** {hours_remaining:,.0f}
- **Project Value:** ${project_value:,.2f}
- **Revenue Earned:** ${revenue:,.2f}
- **Remaining Value:** ${remaining_value:,.2f}
            """)

    # Stop Project Modal
    if st.session_state.get('show_stop_modal', False):
        with st.container():
            st.markdown("---")
            st.subheader("\u23f8\ufe0f Stop Project")
            st.warning("This will put the project on hold. You can resume it later.")
            
            with st.form("stop_project_form"):
                stop_reason = st.text_area(
                    "Reason for stopping *",
                    placeholder="e.g., Client requested pause, waiting for approvals, resource constraints..."
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Stop Project", type="secondary", use_container_width=True):
                        if stop_reason:
                            success, error = db_change_project_status(
                                project_id=project['id'],
                                new_status='on-hold',
                                reason=stop_reason,
                                changed_by='Metro Bot'
                            )
                            if success:
                                project['status'] = 'on-hold'
                                project['status_reason'] = stop_reason
                                db_notify_mission_control_project_status(
                                    project['id'], project['name'], 'on-hold', stop_reason
                                )
                                st.session_state.show_stop_modal = False
                                st.success("Project stopped successfully!")
                                st.rerun()
                            else:
                                st.error(f"Failed to stop project: {error}")
                        else:
                            st.error("Please provide a reason for stopping the project.")
                
                with col2:
                    if st.form_submit_button("Cancel", use_container_width=True):
                        st.session_state.show_stop_modal = False
                        st.rerun()
    
    # Void Project Modal
    if st.session_state.get('show_void_modal', False):
        with st.container():
            st.markdown("---")
            st.subheader("\u274c Void Project")
            st.error("**Warning:** This will cancel the project permanently. This action cannot be undone!")
            
            with st.form("void_project_form"):
                void_reason = st.text_area(
                    "Reason for voiding *",
                    placeholder="e.g., Client cancelled contract, project requirements changed, budget issues..."
                )
                
                confirm_void = st.checkbox("I understand this action cannot be undone")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Void Project", type="secondary", use_container_width=True):
                        if void_reason and confirm_void:
                            success, error = db_change_project_status(
                                project_id=project['id'],
                                new_status='voided',
                                reason=void_reason,
                                changed_by='Metro Bot'
                            )
                            if success:
                                project['status'] = 'voided'
                                project['status_reason'] = void_reason
                                db_notify_mission_control_project_status(
                                    project['id'], project['name'], 'voided', void_reason
                                )
                                st.session_state.show_void_modal = False
                                st.error("Project voided permanently.")
                                st.rerun()
                            else:
                                st.error(f"Failed to void project: {error}")
                        elif not void_reason:
                            st.error("Please provide a reason for voiding the project.")
                        elif not confirm_void:
                            st.error("Please confirm you understand this action cannot be undone.")
                
                with col2:
                    if st.form_submit_button("Cancel", use_container_width=True):
                        st.session_state.show_void_modal = False
                        st.rerun()


# ============================================
# MAIN PAGE
# ============================================
st.title("\U0001f4c1 Projects")

if st.session_state.proj_show_new_form:
    show_new_project_form()
elif st.session_state.proj_selected_project:
    show_project_detail(st.session_state.proj_selected_project)
else:
    # Financial Dashboard
    render_financial_dashboard(st.session_state.proj_projects)

    st.markdown("---")

    # Toolbar
    toolbar_col1, toolbar_col2, toolbar_col3, toolbar_col4 = st.columns([2, 1, 1, 1])

    with toolbar_col1:
        search = st.text_input("\U0001f50d Search projects...", placeholder="Project name or client", label_visibility="collapsed")

    with toolbar_col2:
        status_filter = st.selectbox(
            "Status",
            ["All Status"] + [f"{PROJECT_STATUS[s]['icon']} {PROJECT_STATUS[s]['label']}" for s in PROJECT_STATUS],
            label_visibility="collapsed"
        )

    with toolbar_col3:
        type_filter = st.selectbox(
            "Type",
            ["All Types"] + [f"{PROJECT_TYPES[t]['icon']} {PROJECT_TYPES[t]['label']}" for t in PROJECT_TYPES],
            label_visibility="collapsed"
        )

    with toolbar_col4:
        if st.button("\u2795 New Project", type="primary"):
            st.session_state.proj_show_new_form = True
            st.rerun()

    # Sidebar stats
    active_projects = [p for p in st.session_state.proj_projects if p['status'] == 'active']
    total_value = sum(calc_project_value(p) for p in st.session_state.proj_projects)
    total_hours = sum(p.get('hours_logged', 0) or 0 for p in st.session_state.proj_projects)

    render_sidebar_stats({
        "Total Projects": str(len(st.session_state.proj_projects)),
        "Active": str(len(active_projects)),
        "Portfolio Value": f"${total_value:,.0f}",
        "Hours Logged": f"{total_hours:,.0f}"
    })

    # Status count row
    stat_cols = st.columns(6)
    for i, (status_key, status_info) in enumerate(PROJECT_STATUS.items()):
        count = len([p for p in st.session_state.proj_projects if p['status'] == status_key])
        with stat_cols[i]:
            st.metric(f"{status_info['icon']} {status_info['label']}", count)

    st.markdown("---")

    # Filter projects
    filtered_projects = list(st.session_state.proj_projects)

    if search:
        search_lower = search.lower()
        filtered_projects = [p for p in filtered_projects if
            search_lower in p['name'].lower() or
            search_lower in p.get('client', '').lower() or
            search_lower in p.get('description', '').lower()]

    if status_filter != "All Status":
        status_key = next(k for k, v in PROJECT_STATUS.items() if f"{v['icon']} {v['label']}" == status_filter)
        filtered_projects = [p for p in filtered_projects if p['status'] == status_key]

    if type_filter != "All Types":
        type_key = next(k for k, v in PROJECT_TYPES.items() if f"{v['icon']} {v['label']}" == type_filter)
        filtered_projects = [p for p in filtered_projects if p.get('project_type') == type_key]

    # Project list
    st.markdown(f"### Showing {len(filtered_projects)} projects")

    for project in filtered_projects:
        status_info = PROJECT_STATUS.get(project['status'], PROJECT_STATUS['active'])
        type_info = PROJECT_TYPES.get(project.get('project_type', 'project'), PROJECT_TYPES['project'])
        hours_logged = project.get('hours_logged', 0) or 0
        estimated_hours = project.get('estimated_hours', 0) or 0
        hourly_rate = project.get('hourly_rate', DEFAULT_HOURLY_RATE)
        revenue = hours_logged * hourly_rate
        value = calc_project_value(project)

        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

            with col1:
                st.markdown(f"**{status_info['icon']} {project['name']}**")
                st.caption(f"{type_info['icon']} {type_info['label']} \u00b7 {project.get('client', CLIENT_NAME)}")

            with col2:
                if estimated_hours > 0:
                    hrs_pct = min(hours_logged / estimated_hours, 1.0)
                    st.markdown(f"\u23f1\ufe0f {hours_logged:,.0f} / {estimated_hours:,.0f} hrs ({hrs_pct * 100:.0f}%)")
                    st.progress(hrs_pct)
                else:
                    st.markdown(f"\u23f1\ufe0f {hours_logged:,.0f} hours logged")

            with col3:
                st.markdown(f"\U0001f4b0 ${revenue:,.0f} / ${value:,.0f}")
                if value > 0:
                    rev_pct = min(revenue / value, 1.0)
                    st.progress(rev_pct)

            with col4:
                if st.button("Open", key=f"open_{project['id']}"):
                    st.session_state.proj_selected_project = project['id']
                    st.rerun()
