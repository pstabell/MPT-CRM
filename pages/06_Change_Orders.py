"""
MPT-CRM Change Orders Page
Manage project scope changes with approval workflow

Change Order Workflow:
- draft → pending → approved/rejected → completed
"""

import streamlit as st
from datetime import datetime, date, timedelta
import json
from db_service import (
    db_is_connected, get_db, 
    db_get_projects, db_get_project
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
    "Dashboard": {"icon": "📊", "path": "app.py"},
    "Discovery Call": {"icon": "📞", "path": "pages/01_Discovery.py"},
    "Companies": {"icon": "🏢", "path": "pages/01a_Companies.py"},
    "Contacts": {"icon": "👥", "path": "pages/02_Contacts.py"},
    "Pipeline": {"icon": "🏆", "path": "pages/03_Pipeline.py"},
    "Projects": {"icon": "📁", "path": "pages/04_Projects.py"},
    "Tasks": {"icon": "✅", "path": "pages/05_Tasks.py"},
    "Change Orders": {"icon": "📝", "path": "pages/06_Change_Orders.py"},
    "Time & Billing": {"icon": "⏰", "path": "pages/06_Time_Billing.py"},
    "Marketing": {"icon": "📢", "path": "pages/07_Marketing.py"},
    "Reports": {"icon": "📊", "path": "pages/08_Reports.py"},
    "Settings": {"icon": "⚙️", "path": "pages/09_Settings.py"},
    "Service": {"icon": "🛠️", "path": "pages/10_Service.py"},
    "Help": {"icon": "❓", "path": "pages/11_Help.py"}
}

def render_sidebar():
    """Render navigation sidebar"""
    st.markdown(HIDE_STREAMLIT_NAV, unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown("### 🚀 MPT-CRM")
        st.markdown("---")
        
        # Render auth status
        render_auth_status()
        st.markdown("---")
        
        # Navigation
        for page_name, config in PAGE_CONFIG.items():
            icon = config["icon"]
            path = config["path"]
            
            # Highlight current page
            if page_name == "Change Orders":
                st.markdown(f"**{icon} {page_name}**")
            else:
                if st.button(f"{icon} {page_name}", key=f"nav_{page_name}"):
                    st.switch_page(path)


# ============================================
# CHANGE ORDERS DATABASE FUNCTIONS
# ============================================

def db_get_change_orders(project_id=None, status=None):
    """Get change orders with optional filtering"""
    try:
        db = get_db()
        if not db:
            return []
        
        query = db.table('change_orders').select("""
            id, project_id, title, description, status,
            requested_by, approved_by, requested_at, approved_at,
            estimated_hours, actual_hours, hourly_rate, total_amount,
            impact_description, requires_client_approval, client_signature,
            created_at, updated_at,
            projects(name, client_id, contacts(first_name, last_name, company))
        """).order('created_at', desc=True)
        
        if project_id:
            query = query.eq('project_id', project_id)
        if status:
            query = query.eq('status', status)
            
        result = query.execute()
        return result.data if result.data else []
        
    except Exception as e:
        st.error(f"Error fetching change orders: {str(e)}")
        return []

def db_create_change_order(data):
    """Create a new change order"""
    try:
        db = get_db()
        if not db:
            return None
        
        # Calculate total_amount if hourly_rate and estimated_hours are provided
        if data.get('estimated_hours') and data.get('hourly_rate'):
            data['total_amount'] = float(data['estimated_hours']) * float(data['hourly_rate'])
        
        result = db.table('change_orders').insert(data).execute()
        return result.data[0] if result.data else None
        
    except Exception as e:
        st.error(f"Error creating change order: {str(e)}")
        return None

def db_update_change_order(change_order_id, data):
    """Update a change order"""
    try:
        db = get_db()
        if not db:
            return None
        
        data['updated_at'] = datetime.now().isoformat()
        
        # Recalculate total_amount if hourly_rate and estimated_hours are provided
        if data.get('estimated_hours') and data.get('hourly_rate'):
            data['total_amount'] = float(data['estimated_hours']) * float(data['hourly_rate'])
        
        result = db.table('change_orders').update(data).eq('id', change_order_id).execute()
        return result.data[0] if result.data else None
        
    except Exception as e:
        st.error(f"Error updating change order: {str(e)}")
        return None

def db_get_change_order(change_order_id):
    """Get a single change order by ID"""
    try:
        db = get_db()
        if not db:
            return None
        
        result = db.table('change_orders').select("""
            id, project_id, title, description, status,
            requested_by, approved_by, requested_at, approved_at,
            estimated_hours, actual_hours, hourly_rate, total_amount,
            impact_description, requires_client_approval, client_signature,
            created_at, updated_at,
            projects(name, client_id, contacts(first_name, last_name, company))
        """).eq('id', change_order_id).execute()
        
        return result.data[0] if result.data else None
        
    except Exception as e:
        st.error(f"Error fetching change order: {str(e)}")
        return None


# ============================================
# UI COMPONENTS
# ============================================

def render_change_order_form(edit_change_order=None):
    """Render form for creating/editing change orders"""
    st.subheader("📝 Create New Change Order" if not edit_change_order else "✏️ Edit Change Order")
    
    with st.form(key="change_order_form"):
        # Get projects for dropdown
        projects = db_get_projects()
        project_options = {f"{p['name']} (ID: {p['id'][:8]}...)": p['id'] for p in projects}
        
        if not projects:
            st.warning("No projects found. Please create a project first.")
            return
        
        # Form fields
        col1, col2 = st.columns(2)
        
        with col1:
            selected_project = st.selectbox(
                "Project *",
                options=list(project_options.keys()),
                index=0 if not edit_change_order else 
                      list(project_options.values()).index(edit_change_order['project_id']) 
                      if edit_change_order['project_id'] in project_options.values() else 0,
                key="co_project"
            )
            
            title = st.text_input(
                "Title *",
                value=edit_change_order['title'] if edit_change_order else "",
                key="co_title"
            )
            
            requested_by = st.text_input(
                "Requested By *",
                value=edit_change_order['requested_by'] if edit_change_order else "Patrick Stabell",
                key="co_requested_by"
            )
            
            status = st.selectbox(
                "Status",
                options=["draft", "pending", "approved", "rejected", "completed"],
                index=["draft", "pending", "approved", "rejected", "completed"].index(edit_change_order['status']) 
                      if edit_change_order else 0,
                key="co_status"
            )
        
        with col2:
            estimated_hours = st.number_input(
                "Estimated Hours",
                min_value=0.0,
                step=0.5,
                value=float(edit_change_order['estimated_hours']) if edit_change_order and edit_change_order['estimated_hours'] else 0.0,
                key="co_estimated_hours"
            )
            
            hourly_rate = st.number_input(
                "Hourly Rate ($)",
                min_value=0.0,
                step=1.0,
                value=float(edit_change_order['hourly_rate']) if edit_change_order and edit_change_order['hourly_rate'] else 150.0,
                key="co_hourly_rate"
            )
            
            requires_client_approval = st.checkbox(
                "Requires Client Approval",
                value=edit_change_order['requires_client_approval'] if edit_change_order else False,
                key="co_client_approval"
            )
            
            # Show calculated total
            total_amount = estimated_hours * hourly_rate
            st.metric("Total Amount", f"${total_amount:,.2f}")
        
        description = st.text_area(
            "Description",
            value=edit_change_order['description'] if edit_change_order else "",
            height=100,
            key="co_description"
        )
        
        impact_description = st.text_area(
            "Impact Description",
            value=edit_change_order['impact_description'] if edit_change_order else "",
            height=80,
            key="co_impact"
        )
        
        # Approval fields (only show for certain statuses)
        if status in ["approved", "rejected", "completed"]:
            col1, col2 = st.columns(2)
            with col1:
                approved_by = st.text_input(
                    "Approved/Rejected By",
                    value=edit_change_order['approved_by'] if edit_change_order else "",
                    key="co_approved_by"
                )
            with col2:
                approved_at = st.date_input(
                    "Approval Date",
                    value=datetime.fromisoformat(edit_change_order['approved_at']).date() 
                          if edit_change_order and edit_change_order['approved_at'] else date.today(),
                    key="co_approved_at"
                )
        
        # Submit button
        submit_text = "Update Change Order" if edit_change_order else "Create Change Order"
        if st.form_submit_button(submit_text, type="primary"):
            # Validate required fields
            if not title.strip():
                st.error("Title is required")
                return
            
            if not requested_by.strip():
                st.error("Requested By is required")
                return
            
            # Prepare data
            data = {
                'project_id': project_options[selected_project],
                'title': title.strip(),
                'description': description.strip() if description else None,
                'status': status,
                'requested_by': requested_by.strip(),
                'estimated_hours': estimated_hours if estimated_hours > 0 else None,
                'hourly_rate': hourly_rate,
                'impact_description': impact_description.strip() if impact_description else None,
                'requires_client_approval': requires_client_approval
            }
            
            # Add approval fields if status requires them
            if status in ["approved", "rejected", "completed"]:
                data['approved_by'] = approved_by.strip() if approved_by else None
                data['approved_at'] = approved_at.isoformat() if approved_at else None
            
            # Create or update
            if edit_change_order:
                result = db_update_change_order(edit_change_order['id'], data)
                if result:
                    st.success("Change order updated successfully!")
                    st.rerun()
            else:
                result = db_create_change_order(data)
                if result:
                    st.success("Change order created successfully!")
                    st.rerun()

def render_change_orders_list():
    """Render list of change orders with filtering"""
    st.subheader("📋 Change Orders")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Project filter
        projects = db_get_projects()
        project_options = ["All Projects"] + [f"{p['name']} (ID: {p['id'][:8]}...)" for p in projects]
        selected_project_filter = st.selectbox("Filter by Project", project_options, key="filter_project")
        
        project_id_filter = None
        if selected_project_filter != "All Projects":
            # Extract project ID from selection
            for p in projects:
                if f"{p['name']} (ID: {p['id'][:8]}...)" == selected_project_filter:
                    project_id_filter = p['id']
                    break
    
    with col2:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All Statuses", "draft", "pending", "approved", "rejected", "completed"],
            key="filter_status"
        )
        status_filter = None if status_filter == "All Statuses" else status_filter
    
    with col3:
        if st.button("🔄 Refresh", key="refresh_change_orders"):
            st.rerun()
    
    # Get filtered change orders
    change_orders = db_get_change_orders(
        project_id=project_id_filter,
        status=status_filter
    )
    
    if not change_orders:
        st.info("No change orders found with current filters.")
        return
    
    # Display change orders
    for co in change_orders:
        with st.expander(f"**{co['title']}** - {co['status'].title()} - {co['projects']['name'] if co.get('projects') else 'Unknown Project'}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Project:** {co['projects']['name'] if co.get('projects') else 'Unknown'}")
                st.write(f"**Status:** {co['status'].title()}")
                st.write(f"**Requested By:** {co['requested_by']}")
                if co['approved_by']:
                    st.write(f"**Approved By:** {co['approved_by']}")
            
            with col2:
                if co['estimated_hours']:
                    st.write(f"**Estimated Hours:** {co['estimated_hours']}")
                if co['actual_hours']:
                    st.write(f"**Actual Hours:** {co['actual_hours']}")
                if co['hourly_rate']:
                    st.write(f"**Hourly Rate:** ${co['hourly_rate']:.2f}")
                if co['total_amount']:
                    st.write(f"**Total Amount:** ${co['total_amount']:,.2f}")
            
            with col3:
                st.write(f"**Created:** {datetime.fromisoformat(co['created_at']).strftime('%m/%d/%Y')}")
                if co['approved_at']:
                    st.write(f"**Approved:** {datetime.fromisoformat(co['approved_at']).strftime('%m/%d/%Y')}")
                if co['requires_client_approval']:
                    st.write("🔒 **Requires Client Approval**")
            
            if co['description']:
                st.write(f"**Description:** {co['description']}")
            
            if co['impact_description']:
                st.write(f"**Impact:** {co['impact_description']}")
            
            # Action buttons
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button(f"✏️ Edit", key=f"edit_{co['id']}"):
                    st.session_state.edit_change_order = co
                    st.rerun()
            
            with col2:
                # Quick status update buttons
                if co['status'] == 'draft':
                    if st.button(f"📤 Submit for Approval", key=f"submit_{co['id']}"):
                        db_update_change_order(co['id'], {'status': 'pending'})
                        st.rerun()
                elif co['status'] == 'pending':
                    if st.button(f"✅ Approve", key=f"approve_{co['id']}"):
                        db_update_change_order(co['id'], {
                            'status': 'approved',
                            'approved_by': 'Patrick Stabell',
                            'approved_at': datetime.now().isoformat()
                        })
                        st.rerun()
                elif co['status'] == 'approved':
                    if st.button(f"🏁 Mark Complete", key=f"complete_{co['id']}"):
                        db_update_change_order(co['id'], {'status': 'completed'})
                        st.rerun()
            
            with col3:
                if co['status'] == 'pending':
                    if st.button(f"❌ Reject", key=f"reject_{co['id']}"):
                        db_update_change_order(co['id'], {
                            'status': 'rejected',
                            'approved_by': 'Patrick Stabell',
                            'approved_at': datetime.now().isoformat()
                        })
                        st.rerun()


# ============================================
# MAIN PAGE
# ============================================

def main():
    st.set_page_config(
        page_title="Change Orders - MPT-CRM",
        page_icon="📝",
        layout="wide"
    )
    
    # SSO Auth check
    if not require_sso_auth():
        return
    
    render_sidebar()
    
    # Check database connection
    if not db_is_connected():
        st.error("🔌 Database connection failed. Please check your Supabase configuration.")
        return
    
    # Main header
    st.title("📝 Change Orders")
    st.markdown("Manage project scope changes with approval workflow")
    
    # Tab navigation
    tab1, tab2 = st.tabs(["📋 Change Orders List", "➕ Create New"])
    
    with tab1:
        render_change_orders_list()
    
    with tab2:
        # Check if we're editing
        if 'edit_change_order' in st.session_state:
            render_change_order_form(st.session_state.edit_change_order)
            if st.button("Cancel Edit"):
                del st.session_state.edit_change_order
                st.rerun()
        else:
            render_change_order_form()

if __name__ == "__main__":
    main()