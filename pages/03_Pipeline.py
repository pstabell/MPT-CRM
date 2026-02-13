"""
MPT-CRM Sales Pipeline
Drag-and-drop Kanban board for Metro Point Technology
Using streamlit-sortables for draggable cards between columns
Connected to Supabase for data persistence

Database operations are handled by db_service.py — the single source of truth.
"""

import streamlit as st
from streamlit_sortables import sort_items
from datetime import datetime, timedelta
from db_service import (
    db_is_connected, reset_db_connection, db_test_connection,
    db_get_deals, db_create_deal, db_update_deal, db_update_deal_stage,
    db_delete_deal, db_get_deal_tasks, db_add_deal_task, db_toggle_deal_task,
    db_get_contacts, db_update_contact_type,
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

def render_sidebar(current_page="Sales Pipeline"):
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
    page_title="MPT-CRM - Sales Pipeline",
    page_icon="favicon.jpg",
    layout="wide"
)

require_sso_auth(allow_bypass=False)

# Custom CSS for Kanban styling
st.markdown("""
<style>
    /* Hide Streamlit defaults */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}

    /* Main container */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 100%;
    }

</style>
""", unsafe_allow_html=True)

# ============================================
# DATA LOADING FUNCTIONS
# ============================================
def load_deals():
    """Load deals from database"""
    if db_is_connected():
        deals = db_get_deals(include_contacts=True)
        return deals if deals is not None else []
    # No database connection - return empty list (no sample data)
    return []

def save_deal_stage(deal_id: str, new_stage: str):
    """Save deal stage change to database"""
    if db_is_connected() and not deal_id.startswith("sample-") and not deal_id.startswith("local-"):
        return db_update_deal_stage(deal_id, new_stage)
    return False

def create_deal(deal_data: dict):
    """Create a new deal in the database"""
    if db_is_connected():
        return db_create_deal(deal_data)
    return None

def update_deal(deal_id: str, deal_data: dict):
    """Update a deal in the database"""
    if db_is_connected() and not deal_id.startswith("sample-") and not deal_id.startswith("local-"):
        return db_update_deal(deal_id, deal_data)
    return None

def delete_deal(deal_id: str):
    """Delete a deal from the database or session state"""
    if db_is_connected() and not deal_id.startswith("sample-") and not deal_id.startswith("local-"):
        return db_delete_deal(deal_id)
    return False

# ============================================
# INITIALIZE SESSION STATE
# ============================================
# Refresh from database on first load or when flagged
needs_refresh = (
    'pipeline_deals' not in st.session_state or
    st.session_state.get('pipeline_deals_need_refresh', True)
)
if needs_refresh:
    st.session_state.pipeline_deals = load_deals()
    st.session_state.pipeline_deals_need_refresh = False

if 'pipeline_selected_deal' not in st.session_state:
    st.session_state.pipeline_selected_deal = None

if 'pipeline_show_lost' not in st.session_state:
    st.session_state.pipeline_show_lost = False

if 'pipeline_show_new_deal_form' not in st.session_state:
    st.session_state.pipeline_show_new_deal_form = False

# ============================================
# RENDER SIDEBAR
# ============================================
render_sidebar("Sales Pipeline")

# Calculate stats for sidebar
active_deals = [d for d in st.session_state.pipeline_deals if d.get('stage') not in ['won', 'lost']]
total_value = sum(d.get('value', 0) or 0 for d in active_deals)
won_value = sum(d.get('value', 0) or 0 for d in st.session_state.pipeline_deals if d.get('stage') == 'won')

render_sidebar_stats({
    "Active Deals": str(len(active_deals)),
    "Pipeline Value": f"${total_value:,}",
    "Won This Month": f"${won_value:,}"
})

# Show database connection status in sidebar
with st.sidebar:
    if db_is_connected():
        st.success("Database connected", icon="✅")
        if st.button("Test Connection", key="test_db"):
            with st.spinner("Testing..."):
                success, message = db_test_connection()
                if success:
                    st.success(message)
                else:
                    st.error(f"Connection failed: {message[:100]}")
    else:
        st.error("Database not connected - check .env file", icon="❌")

# ============================================
# STAGE DEFINITIONS
# ============================================
STAGES = [
    {"id": "lead", "name": "Lead", "color": "#6c757d"},
    {"id": "qualified", "name": "Qualified", "color": "#17a2b8"},
    {"id": "proposal", "name": "Proposal", "color": "#ffc107"},
    {"id": "negotiation", "name": "Negotiation", "color": "#fd7e14"},
    {"id": "contract", "name": "Contract", "color": "#28a745"},
    {"id": "won", "name": "Won", "color": "#20c997"},
]

# ============================================
# HELPER FUNCTIONS
# ============================================
def format_deal_card(deal):
    """Format deal as a compact card string with client name"""
    priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(deal.get('priority', 'medium'), "🟡")
    value = deal.get('value', 0) or 0

    # Get client/company name from either contact relationship or stored fields
    client_name = ""
    if deal.get('contacts'):
        # From joined contacts table
        contact = deal['contacts']
        if contact.get('company'):
            client_name = contact['company']
        elif contact.get('first_name'):
            client_name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
    elif deal.get('company_name'):
        client_name = deal['company_name']
    elif deal.get('contact_name'):
        client_name = deal['contact_name']

    if client_name:
        return f"{priority_icon} {deal['title']} - {client_name} | ${value:,.0f}"
    return f"{priority_icon} {deal['title']} | ${value:,.0f}"

def find_deal_by_card(card_text):
    """Find deal matching the card text"""
    for deal in st.session_state.pipeline_deals:
        if format_deal_card(deal) == card_text:
            return deal
    return None

# ============================================
# NEW DEAL FORM
# ============================================
def show_new_deal_form():
    st.markdown("---")
    st.markdown("## New Deal")

    # Get pre-filled values from session state (set by Contacts page)
    prefill_contact_id = st.session_state.get('new_deal_contact_id', None)
    prefill_contact_name = st.session_state.get('new_deal_contact_name', '')
    prefill_company_name = st.session_state.get('new_deal_company_name', '')

    # If contact already selected (came from Contacts page), show the form
    if prefill_contact_id:
        st.success(f"**Contact:** {prefill_contact_name} ({prefill_company_name})")

        with st.form("new_deal_form"):
            col1, col2 = st.columns(2)

            with col1:
                title = st.text_input("Deal Title *", placeholder="e.g., Website Redesign")
                source = st.selectbox("Source", ["Networking", "Referral", "Website", "LinkedIn", "Cold Outreach", "Other"])
                description = st.text_area("Description", placeholder="Brief description of the deal...")

            with col2:
                value = st.number_input("Deal Value ($)", min_value=0, step=1000, value=5000)
                priority = st.selectbox("Priority", ["Low", "Medium", "High"], index=1)
                expected_close = st.date_input("Expected Close Date", value=datetime.now() + timedelta(days=30))
                # All pipeline stages available
                stage_names = [s['name'] for s in STAGES]
                stage_ids = [s['id'] for s in STAGES]
                selected_stage_idx = st.selectbox("Initial Stage", range(len(stage_names)), format_func=lambda i: stage_names[i], index=0)
                stage = stage_ids[selected_stage_idx]

            col_submit, col_cancel = st.columns(2)
            with col_submit:
                submitted = st.form_submit_button("Create Deal", type="primary", use_container_width=True)
            with col_cancel:
                cancelled = st.form_submit_button("Cancel", use_container_width=True)

            if submitted and title:
                deal_data = {
                    "title": title,
                    "contact_name": prefill_contact_name,
                    "company_name": prefill_company_name,
                    "contact_id": prefill_contact_id,
                    "source": source,
                    "value": value,
                    "priority": priority.lower(),
                    "expected_close": expected_close.strftime("%Y-%m-%d"),
                    "stage": stage,
                    "description": description,
                    "days_in_stage": 0,
                    "labels": []
                }

                result = create_deal(deal_data)
                if result:
                    st.success(f"Deal '{title}' created!")
                    st.session_state.pipeline_deals_need_refresh = True
                    st.session_state.pipeline_show_new_deal_form = False
                    # Clear prefill values
                    for key in ['new_deal_contact_id', 'new_deal_contact_name', 'new_deal_company_name']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
                else:
                    st.error("Failed to create deal")

            if cancelled:
                st.session_state.pipeline_show_new_deal_form = False
                # Clear prefill values
                for key in ['new_deal_contact_id', 'new_deal_contact_name', 'new_deal_company_name']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
    else:
        # No contact selected - show contact search/selection
        st.info("**Step 1:** Select a contact for this deal")

        # Load contacts from database
        contacts = db_get_contacts()

        if not contacts:
            st.warning("No contacts found. Please create a contact first.")
            if st.button("Go to Contacts", type="primary"):
                st.switch_page("pages/02_Contacts.py")
            if st.button("Cancel"):
                st.session_state.pipeline_show_new_deal_form = False
                st.rerun()
            return

        # Search box
        search = st.text_input("🔍 Search contacts...", placeholder="Type name or company")

        # Filter contacts based on search
        if search:
            search_lower = search.lower()
            filtered_contacts = [c for c in contacts if
                search_lower in f"{c.get('first_name', '')} {c.get('last_name', '')}".lower() or
                search_lower in (c.get('company') or '').lower()]
        else:
            filtered_contacts = contacts

        # Show contact list
        st.markdown("**Select a contact:**")

        if not filtered_contacts:
            st.caption("No contacts match your search")
        else:
            # Show up to 10 contacts
            for contact in filtered_contacts[:10]:
                contact_display = f"{contact.get('first_name', '')} {contact.get('last_name', '')}"
                company = contact.get('company', '')
                if company:
                    contact_display += f" - {company}"

                if st.button(contact_display, key=f"select_contact_{contact['id']}", use_container_width=True):
                    st.session_state.new_deal_contact_id = contact['id']
                    st.session_state.new_deal_contact_name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}"
                    st.session_state.new_deal_company_name = contact.get('company', '')
                    st.rerun()

            if len(filtered_contacts) > 10:
                st.caption(f"_Showing 10 of {len(filtered_contacts)} contacts. Use search to narrow results._")

        st.markdown("---")
        if st.button("Cancel", use_container_width=True):
            st.session_state.pipeline_show_new_deal_form = False
            st.rerun()

# ============================================
# DEAL DETAIL PANEL
# ============================================
def show_deal_detail(deal_id):
    deal = next((d for d in st.session_state.pipeline_deals if d.get('id') == deal_id), None)
    if not deal:
        st.session_state.pipeline_selected_deal = None
        return

    st.markdown("---")

    # Editable title
    st.markdown("### Project Title")
    new_title = st.text_input("Project Title", deal['title'], key=f"title_{deal_id}", label_visibility="collapsed")
    if new_title != deal['title'] and new_title.strip():
        deal['title'] = new_title
        update_deal(deal_id, {"title": new_title})

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### Description")
        new_desc = st.text_area("Description", deal.get('description', ''), key=f"desc_{deal_id}", height=100, label_visibility="collapsed")
        if new_desc != deal.get('description', ''):
            deal['description'] = new_desc
            update_deal(deal_id, {"description": new_desc})

        # Tasks section (uses deal_tasks table)
        st.markdown("### Tasks")
        if db_is_connected() and not deal_id.startswith("sample-"):
            # Load tasks from deal_tasks relationship if available
            tasks = deal.get('deal_tasks', []) or db_get_deal_tasks(deal_id)
        else:
            tasks = []

        if tasks:
            completed = sum(1 for t in tasks if t.get('is_complete'))
            st.progress(completed / len(tasks), text=f"{completed}/{len(tasks)} complete")

            for task in tasks:
                col_check, col_text = st.columns([0.1, 0.9])
                with col_check:
                    new_status = st.checkbox("", task.get('is_complete', False), key=f"task_{deal_id}_{task['id']}", label_visibility="collapsed")
                    if new_status != task.get('is_complete', False):
                        db_toggle_deal_task(task['id'], new_status)
                        st.rerun()
                with col_text:
                    st.markdown(f"~~{task['title']}~~" if task.get('is_complete') else task['title'])

        new_task = st.text_input("Add a task...", key=f"new_task_{deal_id}", placeholder="Type and press Enter")
        if new_task and db_is_connected() and not deal_id.startswith("sample-"):
            db_add_deal_task(deal_id, new_task)
            st.session_state.pipeline_deals_need_refresh = True
            st.rerun()

    with col2:
        st.markdown("### Deal Info")

        stages_list = ["lead", "qualified", "proposal", "negotiation", "contract", "won", "lost"]
        stage_names = ["Lead", "Qualified", "Proposal", "Negotiation", "Contract", "Won", "Lost"]
        current_idx = stages_list.index(deal.get('stage', 'lead')) if deal.get('stage') in stages_list else 0
        new_stage = st.selectbox("Stage", stage_names, index=current_idx, key=f"stage_{deal_id}")
        new_stage_id = stages_list[stage_names.index(new_stage)]
        if new_stage_id != deal.get('stage'):
            old_stage = deal.get('stage')
            deal['stage'] = new_stage_id
            deal['days_in_stage'] = 0
            if save_deal_stage(deal_id, new_stage_id):
                st.session_state.pipeline_deals_need_refresh = True
            # If changed to "won", convert contact to client and prompt to create project
            if new_stage_id == 'won' and old_stage != 'won':
                # Convert contact to client type
                contact_id = deal.get('contact_id')
                if contact_id:
                    if db_update_contact_type(contact_id, 'client'):
                        st.toast(f"Contact converted to Client!")
                st.session_state[f"show_create_project_{deal_id}"] = True
            st.rerun()

        # Show "Create Project" prompt if deal was just marked as won
        if st.session_state.get(f"show_create_project_{deal_id}"):
            st.success("Deal Won!")
            st.info("Would you like to create a project for this deal?")
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("Create Project", key=f"create_proj_{deal_id}", type="primary", use_container_width=True):
                    # Set up prefill values for Projects page
                    st.session_state.new_project_name = deal.get('title', '')
                    st.session_state.new_project_client = deal.get('company_name') or deal.get('contact_name', '')
                    st.session_state.new_project_contact_id = deal.get('contact_id')
                    st.session_state.new_project_deal_id = deal_id
                    st.session_state.new_project_budget = deal.get('value', 0) or 0
                    st.session_state.proj_show_new_form = True
                    st.session_state[f"show_create_project_{deal_id}"] = False
                    st.switch_page("pages/04_Projects.py")
            with col_no:
                if st.button("Not Now", key=f"skip_proj_{deal_id}", use_container_width=True):
                    st.session_state[f"show_create_project_{deal_id}"] = False
                    st.rerun()

        current_value = deal.get('value', 0) or 0
        new_value = st.number_input("Value ($)", value=int(current_value), step=1000, key=f"value_{deal_id}")
        if new_value != current_value:
            deal['value'] = new_value
            update_deal(deal_id, {"value": new_value})

        priorities = ["low", "medium", "high"]
        priority_names = ["Low", "Medium", "High"]
        current_priority = priorities.index(deal.get('priority', 'medium')) if deal.get('priority') in priorities else 1
        new_priority = st.selectbox("Priority", priority_names, index=current_priority, key=f"priority_{deal_id}")
        new_priority_id = priorities[priority_names.index(new_priority)]
        if new_priority_id != deal.get('priority'):
            deal['priority'] = new_priority_id
            update_deal(deal_id, {"priority": new_priority_id})

        st.markdown("---")

        # Contact link - navigate to contact detail if contact_id exists
        contact_name = deal.get('contact_name', 'N/A')
        contact_id = deal.get('contact_id')
        if contact_id:
            if st.button(f"👤 {contact_name}", key=f"view_contact_{deal_id}", use_container_width=True):
                st.session_state.contacts_selected = contact_id
                st.session_state.selected_contact = contact_id
                st.switch_page("pages/02_Contacts.py")
        else:
            st.markdown(f"**Contact:** {contact_name}")

        st.markdown(f"**Company:** {deal.get('company_name', 'N/A')}")
        st.markdown(f"**Source:** {deal.get('source', 'N/A')}")
        if deal.get('expected_close'):
            st.markdown(f"**Expected Close:** {deal.get('expected_close')}")

    # Auto-save indicator
    st.caption("_Changes are saved automatically_")

    # Action buttons
    col_close, col_delete = st.columns(2)
    with col_close:
        if st.button("✓ Done", key=f"close_{deal_id}", use_container_width=True, type="primary"):
            st.session_state.pipeline_selected_deal = None
            st.rerun()
    with col_delete:
        if st.button("🗑️ Delete Deal", key=f"delete_{deal_id}", type="secondary", use_container_width=True):
            st.session_state[f"confirm_delete_{deal_id}"] = True
            st.rerun()

    # Confirm delete dialog
    if st.session_state.get(f"confirm_delete_{deal_id}"):
        st.warning(f"Are you sure you want to delete **{deal['title']}**? This cannot be undone.")
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("Yes, Delete", key=f"confirm_yes_{deal_id}", type="primary", use_container_width=True):
                # Delete from database
                if delete_deal(deal_id):
                    st.success("Deal deleted from database!")
                # Remove from session state
                st.session_state.pipeline_deals = [d for d in st.session_state.pipeline_deals if d.get('id') != deal_id]
                st.session_state.pipeline_selected_deal = None
                st.session_state[f"confirm_delete_{deal_id}"] = False
                st.rerun()
        with col_no:
            if st.button("Cancel", key=f"confirm_no_{deal_id}", use_container_width=True):
                st.session_state[f"confirm_delete_{deal_id}"] = False
                st.rerun()

# ============================================
# MAIN CONTENT
# ============================================
st.title("Sales Pipeline")

# Toolbar
toolbar_col1, toolbar_col2, toolbar_col3, toolbar_col4 = st.columns([2, 1, 1, 1])

with toolbar_col1:
    search = st.text_input("Search deals...", placeholder="Search by name, company, or contact", label_visibility="collapsed")

with toolbar_col2:
    st.session_state.pipeline_show_lost = st.checkbox("Show Lost Deals", st.session_state.pipeline_show_lost)

with toolbar_col3:
    if st.button("🔄 Refresh", use_container_width=True):
        # Clear cached database connection and deals
        reset_db_connection()
        if 'pipeline_deals' in st.session_state:
            del st.session_state['pipeline_deals']
        st.session_state.pipeline_deals_need_refresh = True
        st.rerun()

with toolbar_col4:
    if st.button("➕ New Deal", type="primary", use_container_width=True):
        st.session_state.pipeline_show_new_deal_form = True
        st.session_state.pipeline_selected_deal = None

# Show new deal form if requested
if st.session_state.pipeline_show_new_deal_form:
    show_new_deal_form()
# Show deal detail if selected
elif st.session_state.pipeline_selected_deal:
    show_deal_detail(st.session_state.pipeline_selected_deal)
else:
    # Filter deals
    filtered_deals = st.session_state.pipeline_deals
    if search:
        search_lower = search.lower()
        filtered_deals = [d for d in filtered_deals if
            search_lower in d.get('title', '').lower() or
            search_lower in (d.get('company_name') or '').lower() or
            search_lower in (d.get('contact_name') or '').lower()]

    visible_stages = STAGES.copy()
    if st.session_state.pipeline_show_lost:
        visible_stages.append({"id": "lost", "name": "Lost", "color": "#dc3545"})

    # Build the sortable board data
    board_data = []
    for stage in visible_stages:
        stage_deals = [d for d in filtered_deals if d.get('stage') == stage['id']]
        stage_value = sum(d.get('value', 0) or 0 for d in stage_deals)
        items = [format_deal_card(deal) for deal in stage_deals]
        board_data.append({
            'header': f"{stage['name']} ({len(stage_deals)}) ${stage_value:,}",
            'items': items
        })

    st.markdown("**Drag cards between columns to move deals**")

    # Custom CSS for the sortable cards - powder blue theme
    kanban_style = """
    .sortable-item {
        background-color: #B0E0E6 !important;
        border-left: 4px solid #4682B4 !important;
        border-radius: 6px !important;
        color: #1a1a2e !important;
    }
    .sortable-item:hover {
        background-color: #87CEEB !important;
    }
    .sortable-container-header {
        background-color: #1a1a2e !important;
        color: white !important;
        border-radius: 6px 6px 0 0 !important;
        padding: 8px 12px !important;
    }
    .sortable-container-body {
        background-color: #2d2d44 !important;
        border-radius: 0 0 6px 6px !important;
    }
    """

    # The sortable Kanban board
    sorted_board = sort_items(board_data, multi_containers=True, direction="horizontal", custom_style=kanban_style)

    # Detect changes and update deal stages
    # Note: We avoid st.rerun() here to prevent React component errors during drag
    if sorted_board:
        changes_made = False
        won_deal = None  # Track if a deal was moved to Won
        for stage_idx, stage in enumerate(visible_stages):
            new_items = sorted_board[stage_idx].get('items', [])
            for card_text in new_items:
                deal = find_deal_by_card(card_text)
                if deal and deal.get('stage') != stage['id']:
                    old_stage = deal.get('stage')
                    deal['stage'] = stage['id']
                    deal['days_in_stage'] = 0

                    # Track if moved to Won (before attempting database save)
                    if stage['id'] == 'won' and old_stage != 'won':
                        won_deal = deal
                        # Convert contact to client type
                        contact_id = deal.get('contact_id')
                        if contact_id:
                            db_update_contact_type(contact_id, 'client')

                    # Save to database
                    if save_deal_stage(deal.get('id'), stage['id']):
                        st.toast(f"Moved '{deal['title']}' to {stage['name']}")
                        st.session_state.pipeline_deals_need_refresh = True
                    else:
                        st.warning(f"Stage change for '{deal['title']}' saved locally (database sync pending)")
                    changes_made = True

        # If a deal was moved to Won, open it to show create project prompt
        if won_deal:
            st.session_state[f"show_create_project_{won_deal.get('id')}"] = True
            st.session_state.pipeline_selected_deal = won_deal.get('id')
            st.toast("Deal Won! Opening project creation...")

        # Only rerun after all changes are processed (not during drag)
        if changes_made:
            st.rerun()

    st.markdown("---")

    # View deal details section
    st.markdown("**Click to view deal details:**")
    detail_cols = st.columns(len(visible_stages))
    for col_idx, stage in enumerate(visible_stages):
        with detail_cols[col_idx]:
            st.markdown(f"**{stage['name']}**")
            stage_deals = [d for d in filtered_deals if d.get('stage') == stage['id']]
            for deal in stage_deals:
                if st.button(deal['title'][:18], key=f"view_{deal.get('id')}", use_container_width=True):
                    st.session_state.pipeline_selected_deal = deal.get('id')
                    st.rerun()

    # Summary
    st.markdown("---")
    st.subheader("Pipeline Summary")
    metric_cols = st.columns(6)

    all_deals = st.session_state.pipeline_deals
    with metric_cols[0]:
        st.metric("Leads", f"${sum(d.get('value', 0) or 0 for d in all_deals if d.get('stage') == 'lead'):,}")
    with metric_cols[1]:
        st.metric("In Progress", f"${sum(d.get('value', 0) or 0 for d in all_deals if d.get('stage') in ['qualified', 'proposal']):,}")
    with metric_cols[2]:
        st.metric("Closing", f"${sum(d.get('value', 0) or 0 for d in all_deals if d.get('stage') in ['negotiation', 'contract']):,}")
    with metric_cols[3]:
        st.metric("Won", f"${sum(d.get('value', 0) or 0 for d in all_deals if d.get('stage') == 'won'):,}")
    with metric_cols[4]:
        st.metric("Lost", f"${sum(d.get('value', 0) or 0 for d in all_deals if d.get('stage') == 'lost'):,}")
    with metric_cols[5]:
        closed = [d for d in all_deals if d.get('stage') in ['won', 'lost']]
        won = [d for d in all_deals if d.get('stage') == 'won']
        win_rate = (len(won) / len(closed) * 100) if closed else 0
        st.metric("Win Rate", f"{win_rate:.0f}%")
