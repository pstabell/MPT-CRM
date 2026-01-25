"""
MPT-CRM Sales Pipeline
Drag-and-drop Kanban board for Metro Point Technology
Using streamlit-sortables for draggable cards between columns
Connected to Supabase for data persistence
"""

import streamlit as st
from streamlit_sortables import sort_items
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.navigation import render_sidebar, render_sidebar_stats
from services.database import db

# Page config
st.set_page_config(
    page_title="MPT-CRM - Sales Pipeline",
    page_icon="📊",
    layout="wide"
)

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

# Sample data for when database is not connected
SAMPLE_DEALS = [
    {
        "id": "sample-1",
        "title": "Cape Coral Chamber Contact",
        "stage": "lead",
        "value": 5000,
        "contact_name": "John Smith",
        "company_name": "Smith Consulting",
        "source": "Networking",
        "days_in_stage": 1,
        "priority": "medium",
        "expected_close": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        "labels": ["New Lead"],
        "description": "Met at Cape Coral Chamber Networking at Noon event.",
    },
    {
        "id": "sample-2",
        "title": "Website Redesign",
        "stage": "qualified",
        "value": 12000,
        "contact_name": "Sarah Johnson",
        "company_name": "Johnson & Co",
        "source": "Referral",
        "days_in_stage": 5,
        "priority": "high",
        "expected_close": (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d"),
        "labels": ["Referral", "Website"],
        "description": "Referral from Mike Williams. Needs modern website with client portal.",
    },
    {
        "id": "sample-3",
        "title": "Custom CRM Development",
        "stage": "proposal",
        "value": 45000,
        "contact_name": "Mike Williams",
        "company_name": "Williams Insurance",
        "source": "Website",
        "days_in_stage": 12,
        "priority": "high",
        "expected_close": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
        "labels": ["CRM", "Insurance"],
        "description": "Full custom CRM for insurance agency.",
    },
]

def load_deals():
    """Load deals from database or return sample data"""
    if db.is_connected:
        try:
            deals = db.get_deals()
            # Return database deals (even if empty list) when connected
            # Only fall back to sample data if there's an error
            return deals if deals is not None else []
        except Exception as e:
            st.warning(f"Could not load from database: {str(e)[:50]}...")
            return SAMPLE_DEALS
    # Return sample data if no database connection
    return SAMPLE_DEALS

def save_deal_stage(deal_id: str, new_stage: str):
    """Save deal stage change to database"""
    if db.is_connected and not deal_id.startswith("sample-") and not deal_id.startswith("local-"):
        try:
            db.update_deal_stage(deal_id, new_stage)
            return True
        except Exception as e:
            st.error(f"Failed to save: {str(e)[:50]}")
    return False

def create_deal(deal_data: dict):
    """Create a new deal in the database"""
    if db.is_connected:
        try:
            return db.create_deal(deal_data)
        except Exception as e:
            st.error(f"Database error: {str(e)[:50]}")
    return None

def update_deal(deal_id: str, deal_data: dict):
    """Update a deal in the database"""
    if db.is_connected and not deal_id.startswith("sample-") and not deal_id.startswith("local-"):
        try:
            return db.update_deal(deal_id, deal_data)
        except Exception:
            pass  # Silently fail for updates
    return None

# Initialize session state
if 'deals' not in st.session_state or st.session_state.get('deals_need_refresh', True):
    st.session_state.deals = load_deals()
    st.session_state.deals_need_refresh = False

if 'selected_deal' not in st.session_state:
    st.session_state.selected_deal = None

if 'show_lost' not in st.session_state:
    st.session_state.show_lost = False

if 'show_new_deal_form' not in st.session_state:
    st.session_state.show_new_deal_form = False

# Render shared sidebar
render_sidebar("Sales Pipeline")

# Calculate stats for sidebar
active_deals = [d for d in st.session_state.deals if d.get('stage') not in ['won', 'lost']]
total_value = sum(d.get('value', 0) or 0 for d in active_deals)
won_value = sum(d.get('value', 0) or 0 for d in st.session_state.deals if d.get('stage') == 'won')

render_sidebar_stats({
    "Active Deals": str(len(active_deals)),
    "Pipeline Value": f"${total_value:,}",
    "Won This Month": f"${won_value:,}"
})

# Show database connection status in sidebar
with st.sidebar:
    if db.is_connected:
        st.success("Database connected", icon="✅")
        if st.button("Test Connection", key="test_db"):
            with st.spinner("Testing..."):
                success, message = db.test_connection()
                if success:
                    st.success(message)
                else:
                    st.error(f"Connection failed: {message[:100]}")
    else:
        error = db.get_connection_error()
        st.warning("Using sample data", icon="⚠️")
        if error:
            st.caption(f"Error: {error[:50]}...")

# Stage definitions
STAGES = [
    {"id": "lead", "name": "Lead", "color": "#6c757d"},
    {"id": "qualified", "name": "Qualified", "color": "#17a2b8"},
    {"id": "proposal", "name": "Proposal", "color": "#ffc107"},
    {"id": "negotiation", "name": "Negotiation", "color": "#fd7e14"},
    {"id": "contract", "name": "Contract", "color": "#28a745"},
    {"id": "won", "name": "Won", "color": "#20c997"},
]

def format_deal_card(deal):
    """Format deal as a compact card string"""
    priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(deal.get('priority', 'medium'), "🟡")
    value = deal.get('value', 0) or 0
    return f"{priority_icon} {deal['title']} (${value:,.0f})"

def find_deal_by_card(card_text):
    """Find deal matching the card text"""
    for deal in st.session_state.deals:
        if format_deal_card(deal) == card_text:
            return deal
    return None

# Function to display new deal form
def show_new_deal_form():
    st.markdown("---")
    st.markdown("## New Deal")

    with st.form("new_deal_form"):
        col1, col2 = st.columns(2)

        with col1:
            title = st.text_input("Deal Title *", placeholder="e.g., Website Redesign")
            contact_name = st.text_input("Contact Name", placeholder="e.g., John Smith")
            company_name = st.text_input("Company", placeholder="e.g., Smith Consulting")
            source = st.selectbox("Source", ["Networking", "Referral", "Website", "LinkedIn", "Cold Outreach", "Other"])

        with col2:
            value = st.number_input("Deal Value ($)", min_value=0, step=1000, value=5000)
            priority = st.selectbox("Priority", ["Low", "Medium", "High"], index=1)
            expected_close = st.date_input("Expected Close Date", value=datetime.now() + timedelta(days=30))
            stage = st.selectbox("Initial Stage", ["Lead", "Qualified", "Proposal"], index=0)

        description = st.text_area("Description", placeholder="Brief description of the deal...")

        col_submit, col_cancel = st.columns(2)
        with col_submit:
            submitted = st.form_submit_button("Create Deal", type="primary", use_container_width=True)
        with col_cancel:
            cancelled = st.form_submit_button("Cancel", use_container_width=True)

        if submitted and title:
            deal_data = {
                "title": title,
                "contact_name": contact_name,
                "company_name": company_name,
                "source": source,
                "value": value,
                "priority": priority.lower(),
                "expected_close": expected_close.strftime("%Y-%m-%d"),
                "stage": stage.lower(),
                "description": description,
                "days_in_stage": 0,
                "labels": []
            }

            result = create_deal(deal_data)
            if result:
                st.success(f"Deal '{title}' created!")
                st.session_state.deals_need_refresh = True
                st.session_state.show_new_deal_form = False
                st.rerun()
            elif not db.is_connected:
                # Add to session state for demo purposes
                deal_data["id"] = f"local-{len(st.session_state.deals)+1}"
                st.session_state.deals.append(deal_data)
                st.success(f"Deal '{title}' created (local only - connect database to persist)")
                st.session_state.show_new_deal_form = False
                st.rerun()
            else:
                st.error("Failed to create deal")

        if cancelled:
            st.session_state.show_new_deal_form = False
            st.rerun()

# Function to display deal detail panel
def show_deal_detail(deal_id):
    deal = next((d for d in st.session_state.deals if d.get('id') == deal_id), None)
    if not deal:
        st.session_state.selected_deal = None
        return

    st.markdown("---")
    st.markdown(f"## {deal['title']}")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### Description")
        new_desc = st.text_area("Description", deal.get('description', ''), key=f"desc_{deal_id}", height=100, label_visibility="collapsed")
        if new_desc != deal.get('description', ''):
            deal['description'] = new_desc
            update_deal(deal_id, {"description": new_desc})

        # Tasks section (uses deal_tasks table)
        st.markdown("### Tasks")
        if db.is_connected and not deal_id.startswith("sample-"):
            # Load tasks from deal_tasks relationship if available
            tasks = deal.get('deal_tasks', [])
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
                        db.toggle_deal_task(task['id'], new_status)
                        st.rerun()
                with col_text:
                    st.markdown(f"~~{task['title']}~~" if task.get('is_complete') else task['title'])

        new_task = st.text_input("Add a task...", key=f"new_task_{deal_id}", placeholder="Type and press Enter")
        if new_task and db.is_connected and not deal_id.startswith("sample-"):
            db.add_deal_task(deal_id, new_task)
            st.session_state.deals_need_refresh = True
            st.rerun()

    with col2:
        st.markdown("### Deal Info")

        stages_list = ["lead", "qualified", "proposal", "negotiation", "contract", "won", "lost"]
        stage_names = ["Lead", "Qualified", "Proposal", "Negotiation", "Contract", "Won", "Lost"]
        current_idx = stages_list.index(deal.get('stage', 'lead')) if deal.get('stage') in stages_list else 0
        new_stage = st.selectbox("Stage", stage_names, index=current_idx, key=f"stage_{deal_id}")
        new_stage_id = stages_list[stage_names.index(new_stage)]
        if new_stage_id != deal.get('stage'):
            deal['stage'] = new_stage_id
            deal['days_in_stage'] = 0
            save_deal_stage(deal_id, new_stage_id)
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
        st.markdown(f"**Contact:** {deal.get('contact_name', 'N/A')}")
        st.markdown(f"**Company:** {deal.get('company_name', 'N/A')}")
        st.markdown(f"**Source:** {deal.get('source', 'N/A')}")
        if deal.get('expected_close'):
            st.markdown(f"**Expected Close:** {deal.get('expected_close')}")

    if st.button("Close", key=f"close_{deal_id}"):
        st.session_state.selected_deal = None
        st.rerun()

# Main content
st.title("Sales Pipeline")

# Toolbar
toolbar_col1, toolbar_col2, toolbar_col3, toolbar_col4 = st.columns([2, 1, 1, 1])

with toolbar_col1:
    search = st.text_input("Search deals...", placeholder="Search by name, company, or contact", label_visibility="collapsed")

with toolbar_col2:
    st.session_state.show_lost = st.checkbox("Show Lost Deals", st.session_state.show_lost)

with toolbar_col3:
    if st.button("🔄 Refresh", use_container_width=True):
        st.session_state.deals_need_refresh = True
        st.rerun()

with toolbar_col4:
    if st.button("➕ New Deal", type="primary", use_container_width=True):
        st.session_state.show_new_deal_form = True
        st.session_state.selected_deal = None

# Show new deal form if requested
if st.session_state.show_new_deal_form:
    show_new_deal_form()
# Show deal detail if selected
elif st.session_state.selected_deal:
    show_deal_detail(st.session_state.selected_deal)
else:
    # Filter deals
    filtered_deals = st.session_state.deals
    if search:
        search_lower = search.lower()
        filtered_deals = [d for d in filtered_deals if
            search_lower in d.get('title', '').lower() or
            search_lower in (d.get('company_name') or '').lower() or
            search_lower in (d.get('contact_name') or '').lower()]

    visible_stages = STAGES.copy()
    if st.session_state.show_lost:
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
        for stage_idx, stage in enumerate(visible_stages):
            new_items = sorted_board[stage_idx].get('items', [])
            for card_text in new_items:
                deal = find_deal_by_card(card_text)
                if deal and deal.get('stage') != stage['id']:
                    old_stage = deal.get('stage')
                    deal['stage'] = stage['id']
                    deal['days_in_stage'] = 0
                    # Save to database
                    save_deal_stage(deal.get('id'), stage['id'])
                    st.toast(f"Moved '{deal['title']}' to {stage['name']}")
                    changes_made = True

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
                    st.session_state.selected_deal = deal.get('id')
                    st.rerun()

    # Summary
    st.markdown("---")
    st.subheader("Pipeline Summary")
    metric_cols = st.columns(6)

    all_deals = st.session_state.deals
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
