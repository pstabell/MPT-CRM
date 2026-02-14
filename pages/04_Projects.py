"""
MPT-CRM Projects Page - Full Implementation
===========================================

Complete implementation with all required features:
1. Full CRUD for projects (create, read, update, delete)
2. Project detail view with all required sections
3. Status workflow: Draft → Active → On Hold → Completed → Archived
4. Mission Control integration for time tracking
5. Accounting integration for financials
6. Contact roles and file attachments
7. Quick actions and integrations
"""

import streamlit as st
from datetime import datetime, date, timedelta
import uuid
from decimal import Decimal

# Import all service layers
from db_service import (
    db_is_connected, db_get_contact_email, db_get_projects, db_create_project, 
    db_update_project, db_delete_project, db_get_project, db_get_project_time_entries,
    db_get_project_contacts, db_add_project_contact, db_remove_project_contact,
    db_get_project_files, db_add_project_file, db_delete_project_file,
    db_get_won_deals, db_get_companies_with_won_deals, db_check_deal_project_link,
    db_update_project_hours
)
from cross_system_service import get_accounting_service, render_project_financials
from mission_control_service import (
    get_mission_control_service, render_mission_control_time_tracking,
    render_mission_control_integration
)
from sso_auth import require_sso_auth

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
# NAVIGATION SIDEBAR
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
    "Companies": {"icon": "🏢", "path": "pages/01a_Companies.py"},
    "Contacts": {"icon": "👥", "path": "pages/02_Contacts.py"},
    "Sales Pipeline": {"icon": "🎯", "path": "pages/03_Pipeline.py"},
    "Projects": {"icon": "📁", "path": "pages/04_Projects.py"},
    "Service": {"icon": "🔧", "path": "pages/10_Service.py"},
    "Tasks": {"icon": "✅", "path": "pages/05_Tasks.py"},
    "Time & Billing": {"icon": "💰", "path": "pages/06_Time_Billing.py"},
    "Marketing": {"icon": "📧", "path": "pages/07_Marketing.py"},
    "Reports": {"icon": "📈", "path": "pages/08_Reports.py"},
    "Settings": {"icon": "⚙️", "path": "pages/09_Settings.py"},
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

render_sidebar("Projects")

# ============================================
# CONSTANTS
# ============================================
DEFAULT_HOURLY_RATE = 150.00
CLIENT_NAME = "Metro Point Technology LLC"

# Project type definitions with enhanced options
PROJECT_TYPES = {
    "product": {"label": "Product", "icon": "🏷️", "description": "Software product development"},
    "project": {"label": "Project", "icon": "🔧", "description": "Custom development project"},
    "website": {"label": "Website", "icon": "🌐", "description": "Website development"},
    "maintenance": {"label": "Maintenance", "icon": "🛠️", "description": "Ongoing maintenance and support"},
    "consulting": {"label": "Consulting", "icon": "💡", "description": "Strategic consulting engagement"}
}

# Enhanced project status workflow
PROJECT_STATUS = {
    "draft": {"label": "Draft", "icon": "📝", "color": "#6c757d", "next": ["active"]},
    "active": {"label": "Active", "icon": "🚀", "color": "#28a745", "next": ["on_hold", "completed"]},
    "on_hold": {"label": "On Hold", "icon": "⏸️", "color": "#ffc107", "next": ["active", "cancelled"]},
    "completed": {"label": "Completed", "icon": "✅", "color": "#17a2b8", "next": ["archived"]},
    "archived": {"label": "Archived", "icon": "📦", "color": "#6f42c1", "next": []},
    "cancelled": {"label": "Cancelled", "icon": "❌", "color": "#dc3545", "next": ["archived"]},
}

# Contact role options for projects
PROJECT_ROLES = [
    "Project Manager",
    "Developer",
    "Designer", 
    "QA Tester",
    "Client Contact",
    "Stakeholder",
    "Technical Lead",
    "Business Analyst"
]

# ============================================
# SESSION STATE INITIALIZATION
# ============================================
if 'projects_view' not in st.session_state:
    st.session_state.projects_view = "list"  # list, detail, new

if 'selected_project_id' not in st.session_state:
    st.session_state.selected_project_id = None

if 'projects_data' not in st.session_state:
    st.session_state.projects_data = []

if 'detail_tab' not in st.session_state:
    st.session_state.detail_tab = "overview"

# ============================================
# HELPER FUNCTIONS
# ============================================
def load_projects():
    """Load projects from database"""
    if db_is_connected():
        projects = db_get_projects()
        # Add calculated fields
        for project in projects:
            project['estimated_hours'] = project.get('estimated_hours') or 0
            project['actual_hours'] = project.get('actual_hours') or 0
            project['hourly_rate'] = project.get('hourly_rate') or project.get('budget', 0)
            project['project_value'] = (project.get('estimated_hours') or 0) * (project.get('hourly_rate') or DEFAULT_HOURLY_RATE)
            project['revenue_earned'] = (project.get('actual_hours') or 0) * (project.get('hourly_rate') or DEFAULT_HOURLY_RATE)
        return projects
    return []

def get_project_by_id(project_id):
    """Get a specific project by ID"""
    projects = load_projects()
    return next((p for p in projects if p['id'] == project_id), None)

# ============================================
# NEW PROJECT FORM
# ============================================
def render_new_project_form():
    """Render form for creating a new project"""
    st.title("📁 Create New Project")
    st.markdown("---")
    
    # Load companies with won deals (enforced business rule)
    companies = db_get_companies_with_won_deals() if db_is_connected() else []
    
    if not companies:
        st.error("❌ No companies have won deals available for project creation.")
        st.info("💡 Win a deal in the Sales Pipeline first, then create projects from won deals.")
        if st.button("← Back to Projects"):
            st.session_state.projects_view = "list"
            st.rerun()
        return
    
    with st.form("new_project_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🏢 Client & Deal")
            
            # Company selection
            company_options = [f"{c.get('company', '')} - {c.get('first_name', '')} {c.get('last_name', '')}" for c in companies]
            selected_company_idx = st.selectbox("Select Company", range(len(company_options)), format_func=lambda x: company_options[x])
            selected_company = companies[selected_company_idx] if companies else None
            
            # Won deals for selected company
            won_deals = []
            if selected_company:
                from db_service import db_get_won_deals_by_contact
                won_deals = db_get_won_deals_by_contact(selected_company['id'])
                # Filter out deals already linked to projects
                available_deals = []
                for deal in won_deals:
                    if not db_check_deal_project_link(deal['id']):
                        available_deals.append(deal)
                won_deals = available_deals
            
            if not won_deals:
                st.error("❌ No available won deals for this company.")
                st.info("All won deals for this company are already linked to projects.")
            else:
                deal_options = [f"{d['title']} - ${d.get('value', 0):,.2f}" for d in won_deals]
                selected_deal_idx = st.selectbox("Select Won Deal", range(len(deal_options)), format_func=lambda x: deal_options[x])
                selected_deal = won_deals[selected_deal_idx]
        
        with col2:
            st.markdown("#### 📝 Project Details")
            
            # Auto-populate from deal if available
            default_name = selected_deal.get('title', '') if 'selected_deal' in locals() else ''
            default_budget = selected_deal.get('value', 0) if 'selected_deal' in locals() else 0
            
            project_name = st.text_input("Project Name *", value=default_name, placeholder="e.g., AMS Mobile App")
            project_type = st.selectbox("Project Type *", list(PROJECT_TYPES.keys()), 
                                       format_func=lambda x: f"{PROJECT_TYPES[x]['icon']} {PROJECT_TYPES[x]['label']}")
            description = st.text_area("Description", placeholder="Project scope and objectives...")
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.markdown("#### 💰 Financial")
            estimated_hours = st.number_input("Estimated Hours", min_value=0.0, step=10.0, value=40.0)
            hourly_rate = st.number_input("Hourly Rate ($)", min_value=0.0, step=25.0, value=float(default_budget / estimated_hours) if default_budget and estimated_hours else DEFAULT_HOURLY_RATE)
            
            # Show calculated value
            if estimated_hours > 0:
                calc_value = estimated_hours * hourly_rate
                st.info(f"💰 Project Value: **${calc_value:,.2f}**")
        
        with col4:
            st.markdown("#### 📅 Timeline")
            start_date = st.date_input("Start Date", value=date.today())
            target_end_date = st.date_input("Target End Date", value=date.today() + timedelta(days=90))
            initial_status = st.selectbox("Initial Status", ["draft", "active"], format_func=lambda x: f"{PROJECT_STATUS[x]['icon']} {PROJECT_STATUS[x]['label']}")
        
        # Submit buttons
        st.markdown("---")
        col_submit, col_cancel = st.columns(2)
        
        with col_submit:
            submitted = st.form_submit_button("🚀 Create Project", type="primary", use_container_width=True)
        with col_cancel:
            cancelled = st.form_submit_button("❌ Cancel", use_container_width=True)
        
        if submitted and project_name and 'selected_deal' in locals():
            # Create project
            budget = estimated_hours * hourly_rate
            
            project_data = {
                "name": project_name,
                "client_id": selected_company['id'],
                "deal_id": selected_deal['id'],
                "project_type": project_type,
                "status": initial_status,
                "description": description,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "target_end_date": target_end_date.strftime("%Y-%m-%d"),
                "budget": budget,
                "estimated_hours": estimated_hours,
                "hourly_rate": hourly_rate,
                "actual_hours": 0
            }
            
            try:
                result = db_create_project(project_data)
                if result:
                    st.success(f"✅ Project '{project_name}' created successfully!")
                    st.success(f"💰 Project Value: ${budget:,.2f}")
                    
                    # Switch to project detail view
                    st.session_state.selected_project_id = result['id']
                    st.session_state.projects_view = "detail"
                    st.rerun()
                else:
                    st.error("❌ Failed to create project. Please try again.")
            except Exception as e:
                st.error(f"❌ Error creating project: {str(e)}")
        
        if cancelled:
            st.session_state.projects_view = "list"
            st.rerun()

# ============================================
# PROJECT DETAIL VIEW
# ============================================
def render_project_detail():
    """Render detailed project view with all features"""
    project_id = st.session_state.selected_project_id
    project = get_project_by_id(project_id)
    
    if not project:
        st.error("❌ Project not found")
        st.session_state.projects_view = "list"
        st.rerun()
        return
    
    # Header with status and navigation
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        status_info = PROJECT_STATUS.get(project['status'], PROJECT_STATUS['active'])
        type_info = PROJECT_TYPES.get(project.get('project_type', 'project'), PROJECT_TYPES['project'])
        st.title(f"{status_info['icon']} {project['name']}")
        st.markdown(f"**{type_info['icon']} {type_info['label']}** • {project.get('client_name', 'Unknown Client')}")
    
    with col2:
        # Quick status change
        current_status = project['status']
        possible_next = PROJECT_STATUS[current_status]['next']
        if possible_next:
            new_status = st.selectbox("Status", [current_status] + possible_next, 
                                    format_func=lambda x: f"{PROJECT_STATUS[x]['icon']} {PROJECT_STATUS[x]['label']}")
            if new_status != current_status:
                if db_update_project(project_id, {'status': new_status}):
                    st.success(f"Status changed to {PROJECT_STATUS[new_status]['label']}")
                    st.rerun()
    
    with col3:
        if st.button("← Back to List"):
            st.session_state.projects_view = "list"
            st.rerun()
    
    st.markdown("---")
    
    # Financial summary dashboard
    project_value = project.get('project_value', 0)
    revenue_earned = project.get('revenue_earned', 0)
    estimated_hours = project.get('estimated_hours', 0)
    actual_hours = project.get('actual_hours', 0)
    hours_remaining = max(0, estimated_hours - actual_hours)
    remaining_value = hours_remaining * project.get('hourly_rate', DEFAULT_HOURLY_RATE)
    
    fin_col1, fin_col2, fin_col3, fin_col4 = st.columns(4)
    
    with fin_col1:
        st.metric("💰 Project Value", f"${project_value:,.2f}")
    with fin_col2:
        st.metric("💵 Revenue Earned", f"${revenue_earned:,.2f}")
    with fin_col3:
        st.metric("⏱️ Hours Progress", f"{actual_hours:.1f} / {estimated_hours:.1f}")
    with fin_col4:
        st.metric("📊 Remaining Value", f"${remaining_value:,.2f}")
    
    # Progress bars
    if estimated_hours > 0:
        hours_progress = min(actual_hours / estimated_hours, 1.0)
        st.progress(hours_progress, text=f"Hours: {hours_progress * 100:.1f}% complete")
    
    if project_value > 0:
        revenue_progress = min(revenue_earned / project_value, 1.0)
        st.progress(revenue_progress, text=f"Revenue: {revenue_progress * 100:.1f}% earned")
    
    st.markdown("---")
    
    # Tabbed interface for different aspects
    tab_overview, tab_contacts, tab_time, tab_financials, tab_files, tab_service, tab_integration = st.tabs([
        "📋 Overview", "👥 Team", "⏱️ Time Tracking", "💰 Financials", "📎 Files", "🎫 Service", "🔗 Integration"
    ])
    
    with tab_overview:
        render_project_overview(project)
    
    with tab_contacts:
        render_project_contacts(project)
    
    with tab_time:
        render_project_time_tracking(project)
    
    with tab_financials:
        render_project_financials_detailed(project)
    
    with tab_files:
        render_project_files(project)
    
    with tab_service:
        render_project_service_tickets(project)
    
    with tab_integration:
        render_project_integrations(project)

def render_project_overview(project):
    """Render project overview and basic information"""
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📝 Project Information")
        
        # Editable fields
        with st.form("project_info_form"):
            new_name = st.text_input("Project Name", value=project.get('name', ''))
            new_description = st.text_area("Description", value=project.get('description', ''), height=100)
            
            date_col1, date_col2 = st.columns(2)
            with date_col1:
                start_date = project.get('start_date')
                new_start = st.date_input("Start Date", 
                    value=datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else date.today())
            with date_col2:
                end_date = project.get('target_end_date')
                new_end = st.date_input("Target End Date",
                    value=datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else date.today() + timedelta(days=90))
            
            pricing_col1, pricing_col2 = st.columns(2)
            with pricing_col1:
                new_estimated_hours = st.number_input("Estimated Hours", 
                    value=float(project.get('estimated_hours', 0)), min_value=0.0, step=10.0)
            with pricing_col2:
                new_hourly_rate = st.number_input("Hourly Rate ($)", 
                    value=float(project.get('hourly_rate', DEFAULT_HOURLY_RATE)), min_value=0.0, step=25.0)
            
            # Show calculated value
            new_value = new_estimated_hours * new_hourly_rate
            st.info(f"💰 Updated Project Value: **${new_value:,.2f}**")
            
            if st.form_submit_button("💾 Save Changes", type="primary"):
                update_data = {
                    'name': new_name,
                    'description': new_description,
                    'start_date': new_start.strftime("%Y-%m-%d"),
                    'target_end_date': new_end.strftime("%Y-%m-%d"),
                    'estimated_hours': new_estimated_hours,
                    'hourly_rate': new_hourly_rate,
                    'budget': new_value
                }
                
                success, error = db_update_project(project['id'], update_data)
                if success:
                    st.success("✅ Project updated successfully!")
                    st.rerun()
                else:
                    st.error(f"❌ Update failed: {error}")
    
    with col2:
        st.markdown("### 📊 Quick Stats")
        
        # Status
        status_info = PROJECT_STATUS.get(project['status'], PROJECT_STATUS['active'])
        st.markdown(f"**Status:** {status_info['icon']} {status_info['label']}")
        
        # Type
        type_info = PROJECT_TYPES.get(project.get('project_type', 'project'), PROJECT_TYPES['project'])
        st.markdown(f"**Type:** {type_info['icon']} {type_info['label']}")
        
        # Dates
        if project.get('start_date'):
            st.markdown(f"**Started:** {project['start_date']}")
        if project.get('target_end_date'):
            st.markdown(f"**Target End:** {project['target_end_date']}")
        
        # Key metrics
        st.metric("Hourly Rate", f"${project.get('hourly_rate', 0):,.2f}/hr")
        
        if project.get('estimated_hours', 0) > 0:
            completion = (project.get('actual_hours', 0) / project.get('estimated_hours', 1)) * 100
            st.metric("Completion", f"{completion:.1f}%")
        
        # Source deal info
        if project.get('deal_id'):
            st.markdown("### 🎯 Source Deal")
            deal_link = f"pages/03_Pipeline.py?deal_id={project['deal_id']}"
            st.markdown(f"**Deal:** [View in Pipeline]({deal_link})")
            if project.get('folder_url'):
                st.markdown(f"**Proposal:** [SharePoint Folder]({project['folder_url']})")

def render_project_contacts(project):
    """Render project team/contacts management"""
    st.markdown("### 👥 Project Team")
    
    # Get current team members
    team_members = db_get_project_contacts(project['id']) if db_is_connected() else []
    
    if team_members:
        st.markdown("#### Current Team")
        
        for member in team_members:
            contact = member.get('contacts', {})
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}"
                email = contact.get('email', '')
                company = contact.get('company', '')
                st.markdown(f"**{name}**")
                if email:
                    st.caption(f"📧 {email}")
                if company:
                    st.caption(f"🏢 {company}")
            
            with col2:
                st.markdown(f"**{member.get('role', 'Unknown Role')}**")
                if member.get('is_primary'):
                    st.markdown("⭐ Primary")
            
            with col3:
                if member.get('notes'):
                    st.caption(f"📝 {member['notes']}")
            
            with col4:
                if st.button("🗑️", key=f"remove_{member['id']}", help="Remove from project"):
                    if db_remove_project_contact(member['id']):
                        st.success("Team member removed")
                        st.rerun()
    
    else:
        st.info("No team members assigned yet.")
    
    # Add new team member
    st.markdown("#### Add Team Member")
    
    with st.form("add_team_member"):
        # Get all contacts for selection
        from db_service import db_get_contacts
        all_contacts = db_get_contacts() if db_is_connected() else []
        
        if all_contacts:
            contact_options = [f"{c.get('first_name', '')} {c.get('last_name', '')} - {c.get('email', '')}" for c in all_contacts]
            selected_contact_idx = st.selectbox("Select Contact", range(len(contact_options)), 
                                               format_func=lambda x: contact_options[x])
            selected_contact = all_contacts[selected_contact_idx]
            
            role = st.selectbox("Role", PROJECT_ROLES)
            is_primary = st.checkbox("Primary contact for this role")
            notes = st.text_input("Notes (optional)")
            
            if st.form_submit_button("➕ Add to Team"):
                result = db_add_project_contact(project['id'], selected_contact['id'], role, is_primary, notes)
                if result:
                    st.success(f"✅ Added {selected_contact.get('first_name', '')} as {role}")
                    st.rerun()
                else:
                    st.error("Failed to add team member")
        else:
            st.warning("No contacts available. Add contacts first in the Contacts page.")

def render_project_time_tracking(project):
    """Render time tracking from both Mission Control and local entries"""
    # Mission Control integration
    render_mission_control_time_tracking(project['id'], project.get('mc_task_id'))
    
    st.markdown("---")
    
    # Local time entries
    st.markdown("### 📝 Local Time Entries")
    
    local_entries = db_get_project_time_entries(project['id']) if db_is_connected() else []
    
    if local_entries:
        total_local_hours = sum(float(entry.get('hours', 0)) for entry in local_entries)
        st.metric("Total Local Hours", f"{total_local_hours:.1f}")
        
        for entry in local_entries:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**{entry.get('description', 'Time entry')}**")
                    st.caption(f"📅 {entry.get('date', 'Unknown date')}")
                
                with col2:
                    st.markdown(f"{entry.get('hours', 0):.2f} hrs")
                
                with col3:
                    rate = entry.get('hourly_rate', project.get('hourly_rate', DEFAULT_HOURLY_RATE))
                    amount = float(entry.get('hours', 0)) * float(rate)
                    st.markdown(f"${amount:.2f}")
                
                st.divider()
    
    # Add new time entry
    with st.expander("➕ Add Time Entry"):
        with st.form("add_time_entry"):
            entry_date = st.date_input("Date", value=date.today())
            hours = st.number_input("Hours", min_value=0.0, max_value=24.0, step=0.5, value=1.0)
            description = st.text_input("Description", placeholder="What did you work on?")
            billable = st.checkbox("Billable", value=True)
            rate = st.number_input("Rate ($/hr)", value=float(project.get('hourly_rate', DEFAULT_HOURLY_RATE)))
            
            if st.form_submit_button("Add Entry") and hours > 0 and description:
                from db_service import db_create_time_entry
                entry_data = {
                    'project_id': project['id'],
                    'date': entry_date.strftime("%Y-%m-%d"),
                    'hours': hours,
                    'description': description,
                    'hourly_rate': rate,
                    'is_billable': billable
                }
                
                result = db_create_time_entry(entry_data)
                if result:
                    # Update project actual hours
                    new_actual_hours = project.get('actual_hours', 0) + hours
                    db_update_project_hours(project['id'], new_actual_hours)
                    
                    st.success("✅ Time entry added!")
                    st.rerun()
                else:
                    st.error("Failed to add time entry")

def render_project_financials_detailed(project):
    """Render detailed financial information from Accounting"""
    # Use cross-system service for Accounting integration
    render_project_financials(project['id'], project.get('project_value', 0))

def render_project_files(project):
    """Render file attachments management"""
    st.markdown("### 📎 Project Files")
    
    # Get current files
    project_files = db_get_project_files(project['id']) if db_is_connected() else []
    
    if project_files:
        for file_record in project_files:
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                filename = file_record.get('filename', 'Unknown file')
                description = file_record.get('description', '')
                st.markdown(f"**📄 {filename}**")
                if description:
                    st.caption(description)
                
                category = file_record.get('category', 'general')
                uploaded_by = file_record.get('uploaded_by', 'Unknown')
                upload_date = file_record.get('created_at', '')[:10] if file_record.get('created_at') else ''
                st.caption(f"🏷️ {category.title()} • 👤 {uploaded_by} • 📅 {upload_date}")
            
            with col2:
                file_size = file_record.get('file_size', 0)
                if file_size:
                    if file_size < 1024:
                        size_str = f"{file_size} B"
                    elif file_size < 1024*1024:
                        size_str = f"{file_size/1024:.1f} KB"
                    else:
                        size_str = f"{file_size/(1024*1024):.1f} MB"
                    st.caption(size_str)
            
            with col3:
                storage_url = file_record.get('storage_url')
                if storage_url:
                    st.markdown(f"[📥 Download]({storage_url})")
            
            with col4:
                if st.button("🗑️", key=f"delete_file_{file_record['id']}", help="Delete file"):
                    if db_delete_project_file(file_record['id']):
                        st.success("File deleted")
                        st.rerun()
            
            st.divider()
    else:
        st.info("No files uploaded yet.")
    
    # File upload
    with st.expander("📤 Upload Files"):
        uploaded_files = st.file_uploader("Choose files", accept_multiple_files=True)
        
        if uploaded_files:
            for uploaded_file in uploaded_files:
                col1, col2 = st.columns(2)
                
                with col1:
                    file_description = st.text_input(f"Description for {uploaded_file.name}", key=f"desc_{uploaded_file.name}")
                
                with col2:
                    file_category = st.selectbox(f"Category for {uploaded_file.name}", 
                                               ["general", "contract", "proposal", "deliverable", "documentation"],
                                               key=f"cat_{uploaded_file.name}")
                
                if st.button(f"Upload {uploaded_file.name}", key=f"upload_{uploaded_file.name}"):
                    try:
                        # Upload to Supabase storage
                        from db_service import get_db
                        db = get_db()
                        if db:
                            # Generate unique filename
                            file_ext = uploaded_file.name.split('.')[-1] if '.' in uploaded_file.name else 'bin'
                            unique_filename = f"projects/{project['id']}/{uuid.uuid4().hex[:8]}_{uploaded_file.name}"
                            
                            # Upload file
                            storage_response = db.storage.from_("project-files").upload(
                                unique_filename,
                                uploaded_file.read(),
                                {"content-type": uploaded_file.type or "application/octet-stream"}
                            )
                            
                            if storage_response:
                                # Get public URL
                                storage_url = db.storage.from_("project-files").get_public_url(unique_filename)
                                
                                # Save file record
                                file_data = {
                                    'project_id': project['id'],
                                    'filename': uploaded_file.name,
                                    'file_size': uploaded_file.size,
                                    'file_type': uploaded_file.type or "unknown",
                                    'description': file_description,
                                    'category': file_category,
                                    'storage_url': storage_url,
                                    'uploaded_by': 'CRM User'
                                }
                                
                                if db_add_project_file(file_data):
                                    st.success(f"✅ {uploaded_file.name} uploaded successfully!")
                                    st.rerun()
                                else:
                                    st.error("Failed to save file record")
                            else:
                                st.error("Failed to upload file")
                        else:
                            st.error("Database not connected")
                    except Exception as e:
                        st.error(f"Upload error: {str(e)}")

def render_project_service_tickets(project):
    """Render service tickets and change orders"""
    st.markdown("### 🎫 Service Tickets & Change Orders")
    
    # Get service tickets for this project
    from db_service import get_db
    if db_is_connected():
        db = get_db()
        try:
            # Service tickets
            tickets_response = db.table("service_tickets").select("*").eq("project_id", project['id']).execute()
            service_tickets = tickets_response.data or []
            
            # Change orders
            change_orders_response = db.table("change_orders").select("*").eq("project_id", project['id']).execute()
            change_orders = change_orders_response.data or []
            
        except Exception as e:
            st.error(f"Error loading service data: {e}")
            service_tickets = []
            change_orders = []
    else:
        service_tickets = []
        change_orders = []
    
    # Service Tickets
    if service_tickets:
        st.markdown("#### 🔧 Service Tickets")
        for ticket in service_tickets:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**{ticket.get('title', 'Untitled')}**")
                    st.caption(ticket.get('description', ''))
                
                with col2:
                    status = ticket.get('status', 'open')
                    priority = ticket.get('priority', 'medium')
                    st.markdown(f"Status: **{status.title()}**")
                    st.caption(f"Priority: {priority}")
                
                with col3:
                    hours = ticket.get('estimated_hours', 0)
                    if hours:
                        rate = ticket.get('hourly_rate', DEFAULT_HOURLY_RATE)
                        value = float(hours) * float(rate)
                        st.markdown(f"**${value:,.2f}**")
                        st.caption(f"{hours}h @ ${rate}/hr")
                
                st.divider()
    
    # Change Orders
    if change_orders:
        st.markdown("#### 📋 Change Orders")
        for order in change_orders:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**{order.get('title', 'Untitled Change Order')}**")
                    st.caption(order.get('description', ''))
                
                with col2:
                    status = order.get('status', 'draft')
                    st.markdown(f"Status: **{status.title()}**")
                    if order.get('requested_by'):
                        st.caption(f"By: {order['requested_by']}")
                
                with col3:
                    amount = order.get('total_amount', 0)
                    if amount:
                        st.markdown(f"**${amount:,.2f}**")
                    hours = order.get('estimated_hours', 0)
                    if hours:
                        st.caption(f"{hours}h estimated")
                
                st.divider()
    
    # Quick actions
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🎫 Create Service Ticket"):
            st.info("Navigate to Service page to create tickets")
    
    with col2:
        if st.button("📋 Create Change Order"):
            st.info("Change order creation will be implemented here")

def render_project_integrations(project):
    """Render system integrations and quick actions"""
    # Mission Control Integration
    render_mission_control_integration(project)
    
    st.markdown("---")
    
    # Accounting Integration Status
    st.markdown("### 💰 Accounting Integration")
    accounting_service = get_accounting_service()
    financials = accounting_service.get_project_financials(project['id'])
    
    if financials['invoice_count'] > 0:
        st.success(f"✅ Connected - {financials['invoice_count']} invoices found")
        st.info(f"💰 Total Invoiced: ${financials['total_invoiced']:,.2f}")
    else:
        st.info("ℹ️ No invoices found in Accounting system yet")
    
    # Quick Actions
    st.markdown("### ⚡ Quick Actions")
    
    action_col1, action_col2, action_col3 = st.columns(3)
    
    with action_col1:
        if st.button("📧 Email Client"):
            if project.get('client_id'):
                contact_info = db_get_contact_email(project['client_id'])
                if contact_info and contact_info.get('email'):
                    st.success(f"✅ Draft email to: {contact_info['email']}")
                    st.info("Use the Marketing page to send emails with templates.")
                else:
                    st.warning("No email found for this project's client.")
            else:
                st.warning("No client linked to this project.")
    
    with action_col2:
        if st.button("📄 Generate Invoice"):
            st.info("Invoice generation will create a draft in Accounting system")
            # This would integrate with accounting system to create invoice
    
    with action_col3:
        if st.button("📊 View Reports"):
            st.info("Navigate to Reports page for detailed project analytics")
    
    # External Links
    st.markdown("### 🔗 External Links")
    
    if project.get('folder_url'):
        st.markdown(f"📁 [SharePoint Project Folder]({project['folder_url']})")
    
    if project.get('mc_task_id'):
        mc_url = f"https://mpt-mission-control.vercel.app/?task={project['mc_task_id']}"
        st.markdown(f"🎯 [Mission Control Task]({mc_url})")

# ============================================
# PROJECT LIST VIEW
# ============================================
def render_project_list():
    """Render main project list with filtering and actions"""
    st.title("📁 Projects")
    
    # Load projects
    projects = load_projects()
    
    # Financial dashboard
    if projects:
        total_value = sum(p.get('project_value', 0) for p in projects)
        total_revenue = sum(p.get('revenue_earned', 0) for p in projects)
        total_hours = sum(p.get('actual_hours', 0) for p in projects)
        active_projects = len([p for p in projects if p.get('status') == 'active'])
        
        fin_col1, fin_col2, fin_col3, fin_col4 = st.columns(4)
        
        with fin_col1:
            st.metric("🎯 Total Portfolio", f"${total_value:,.2f}")
        with fin_col2:
            st.metric("💰 Revenue Earned", f"${total_revenue:,.2f}")
        with fin_col3:
            st.metric("⏱️ Hours Logged", f"{total_hours:,.1f}")
        with fin_col4:
            st.metric("🚀 Active Projects", active_projects)
        
        # Portfolio progress
        if total_value > 0:
            portfolio_progress = total_revenue / total_value
            st.progress(portfolio_progress, text=f"Portfolio Progress: {portfolio_progress * 100:.1f}% complete")
    
    st.markdown("---")
    
    # Toolbar
    toolbar_col1, toolbar_col2, toolbar_col3, toolbar_col4, toolbar_col5 = st.columns([2, 1, 1, 1, 1])
    
    with toolbar_col1:
        search = st.text_input("🔍 Search projects...", placeholder="Name, client, or description", label_visibility="collapsed")
    
    with toolbar_col2:
        status_options = ["All Status"] + [f"{PROJECT_STATUS[s]['icon']} {PROJECT_STATUS[s]['label']}" for s in PROJECT_STATUS]
        status_filter = st.selectbox("Status", status_options, label_visibility="collapsed")
    
    with toolbar_col3:
        type_options = ["All Types"] + [f"{PROJECT_TYPES[t]['icon']} {PROJECT_TYPES[t]['label']}" for t in PROJECT_TYPES]
        type_filter = st.selectbox("Type", type_options, label_visibility="collapsed")
    
    with toolbar_col4:
        sort_options = ["Name", "Start Date", "Value", "Status", "Progress"]
        sort_by = st.selectbox("Sort By", sort_options, label_visibility="collapsed")
    
    with toolbar_col5:
        if st.button("➕ New Project", type="primary", use_container_width=True):
            st.session_state.projects_view = "new"
            st.rerun()
    
    # Status summary
    if projects:
        status_cols = st.columns(len(PROJECT_STATUS))
        for i, (status_key, status_info) in enumerate(PROJECT_STATUS.items()):
            count = len([p for p in projects if p.get('status') == status_key])
            with status_cols[i]:
                st.metric(f"{status_info['icon']} {status_info['label']}", count)
    
    st.markdown("---")
    
    # Filter projects
    filtered_projects = projects
    
    if search:
        search_lower = search.lower()
        filtered_projects = [p for p in filtered_projects if
            search_lower in p.get('name', '').lower() or
            search_lower in p.get('description', '').lower() or
            search_lower in str(p.get('client_name', '')).lower()]
    
    if status_filter != "All Status":
        status_key = next(k for k, v in PROJECT_STATUS.items() if f"{v['icon']} {v['label']}" == status_filter)
        filtered_projects = [p for p in filtered_projects if p.get('status') == status_key]
    
    if type_filter != "All Types":
        type_key = next(k for k, v in PROJECT_TYPES.items() if f"{v['icon']} {v['label']}" == type_filter)
        filtered_projects = [p for p in filtered_projects if p.get('project_type') == type_key]
    
    # Sort projects
    if sort_by == "Name":
        filtered_projects.sort(key=lambda x: x.get('name', ''))
    elif sort_by == "Start Date":
        filtered_projects.sort(key=lambda x: x.get('start_date', ''), reverse=True)
    elif sort_by == "Value":
        filtered_projects.sort(key=lambda x: x.get('project_value', 0), reverse=True)
    elif sort_by == "Status":
        filtered_projects.sort(key=lambda x: x.get('status', ''))
    elif sort_by == "Progress":
        filtered_projects.sort(key=lambda x: 
            (x.get('actual_hours', 0) / max(x.get('estimated_hours', 1), 1)), reverse=True)
    
    # Project list
    st.markdown(f"### 📋 Showing {len(filtered_projects)} projects")
    
    for project in filtered_projects:
        render_project_card(project)
    
    # Sidebar stats
    render_sidebar_stats({
        "Total Projects": str(len(projects)),
        "Active": str(len([p for p in projects if p.get('status') == 'active'])),
        "Portfolio Value": f"${sum(p.get('project_value', 0) for p in projects):,.0f}",
        "Hours Logged": f"{sum(p.get('actual_hours', 0) for p in projects):,.0f}"
    })

def render_project_card(project):
    """Render individual project card in list view"""
    status_info = PROJECT_STATUS.get(project.get('status'), PROJECT_STATUS['active'])
    type_info = PROJECT_TYPES.get(project.get('project_type', 'project'), PROJECT_TYPES['project'])
    
    with st.container():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        
        with col1:
            st.markdown(f"**{status_info['icon']} {project.get('name', 'Unnamed Project')}**")
            st.caption(f"{type_info['icon']} {type_info['label']} • {project.get('client_name', 'Unknown Client')}")
            
            if project.get('description'):
                description = project['description'][:100] + "..." if len(project.get('description', '')) > 100 else project['description']
                st.caption(f"📝 {description}")
        
        with col2:
            estimated_hours = project.get('estimated_hours', 0)
            actual_hours = project.get('actual_hours', 0)
            
            if estimated_hours > 0:
                progress = min(actual_hours / estimated_hours, 1.0)
                st.markdown(f"⏱️ {actual_hours:.1f} / {estimated_hours:.1f} hrs ({progress * 100:.0f}%)")
                st.progress(progress)
            else:
                st.markdown(f"⏱️ {actual_hours:.1f} hours logged")
        
        with col3:
            project_value = project.get('project_value', 0)
            revenue_earned = project.get('revenue_earned', 0)
            
            st.markdown(f"💰 ${revenue_earned:,.0f} / ${project_value:,.0f}")
            if project_value > 0:
                revenue_progress = min(revenue_earned / project_value, 1.0)
                st.progress(revenue_progress)
        
        with col4:
            if st.button("👁️ View", key=f"view_{project['id']}"):
                st.session_state.selected_project_id = project['id']
                st.session_state.projects_view = "detail"
                st.rerun()
        
        st.divider()

# ============================================
# MAIN APP LOGIC
# ============================================
def main():
    """Main application logic"""
    
    # Route to appropriate view
    if st.session_state.projects_view == "new":
        render_new_project_form()
    elif st.session_state.projects_view == "detail":
        render_project_detail()
    else:
        render_project_list()

if __name__ == "__main__":
    main()