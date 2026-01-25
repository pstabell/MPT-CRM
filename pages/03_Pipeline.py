"""
MPT-CRM Sales Pipeline
Drag-and-drop Kanban board for Metro Point Technology
Using streamlit-sortables for draggable cards between columns
"""

import streamlit as st
from streamlit_sortables import sort_items
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.navigation import render_sidebar, render_sidebar_stats

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

# Initialize session state
if 'deals' not in st.session_state:
    st.session_state.deals = [
        {
            "id": "deal-1",
            "title": "Cape Coral Chamber Contact",
            "stage": "lead",
            "value": 5000,
            "contact": "John Smith",
            "company": "Smith Consulting",
            "source": "Networking",
            "days_in_stage": 1,
            "priority": "medium",
            "due_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "labels": ["New Lead"],
            "description": "Met at Cape Coral Chamber Networking at Noon event.",
            "comments": [],
            "tasks": [
                {"id": "t1", "text": "Send follow-up email", "complete": False},
                {"id": "t2", "text": "Schedule discovery call", "complete": False}
            ]
        },
        {
            "id": "deal-2",
            "title": "Website Redesign",
            "stage": "qualified",
            "value": 12000,
            "contact": "Sarah Johnson",
            "company": "Johnson & Co",
            "source": "Referral",
            "days_in_stage": 5,
            "priority": "high",
            "due_date": (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d"),
            "labels": ["Referral", "Website"],
            "description": "Referral from Mike Williams. Needs modern website with client portal.",
            "comments": [],
            "tasks": [
                {"id": "t1", "text": "Send portfolio examples", "complete": True},
                {"id": "t2", "text": "Create proposal", "complete": False}
            ]
        },
        {
            "id": "deal-3",
            "title": "Custom CRM Development",
            "stage": "proposal",
            "value": 45000,
            "contact": "Mike Williams",
            "company": "Williams Insurance",
            "source": "Website",
            "days_in_stage": 12,
            "priority": "high",
            "due_date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
            "labels": ["CRM", "Insurance"],
            "description": "Full custom CRM for insurance agency.",
            "comments": [],
            "tasks": [
                {"id": "t1", "text": "Create proposal document", "complete": True},
                {"id": "t2", "text": "Send proposal", "complete": True},
                {"id": "t3", "text": "Follow up call", "complete": False}
            ]
        },
        {
            "id": "deal-4",
            "title": "AMS Integration",
            "stage": "proposal",
            "value": 25000,
            "contact": "Lisa Brown",
            "company": "Brown Agency",
            "source": "Referral",
            "days_in_stage": 8,
            "priority": "medium",
            "due_date": (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d"),
            "labels": ["Integration"],
            "description": "Integration between their existing AMS and carrier portals.",
            "comments": [],
            "tasks": []
        },
        {
            "id": "deal-5",
            "title": "Mobile App",
            "stage": "negotiation",
            "value": 35000,
            "contact": "David Chen",
            "company": "Chen Enterprises",
            "source": "LinkedIn",
            "days_in_stage": 3,
            "priority": "high",
            "due_date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
            "labels": ["Mobile"],
            "description": "Cross-platform mobile app for field service team.",
            "comments": [],
            "tasks": []
        },
        {
            "id": "deal-6",
            "title": "SaaS License",
            "stage": "contract",
            "value": 18000,
            "contact": "Amanda White",
            "company": "White Insurance",
            "source": "Cold Outreach",
            "days_in_stage": 2,
            "priority": "high",
            "due_date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
            "labels": ["SaaS"],
            "description": "Annual license for AMS-APP SaaS platform.",
            "comments": [],
            "tasks": []
        },
        {
            "id": "deal-7",
            "title": "Data Migration",
            "stage": "won",
            "value": 8500,
            "contact": "Robert Taylor",
            "company": "Taylor & Associates",
            "source": "Referral",
            "days_in_stage": 0,
            "priority": "medium",
            "due_date": None,
            "labels": ["Migration"],
            "description": "One-time data migration from legacy system.",
            "comments": [],
            "tasks": []
        },
        {
            "id": "deal-8",
            "title": "E-commerce Platform",
            "stage": "lost",
            "value": 30000,
            "contact": "Jennifer Adams",
            "company": "Adams Retail",
            "source": "Website",
            "days_in_stage": 5,
            "priority": "low",
            "due_date": None,
            "labels": ["E-commerce"],
            "description": "Custom e-commerce platform. Lost to competitor.",
            "lost_reason": "Went with cheaper offshore option",
            "comments": [],
            "tasks": []
        },
    ]

if 'selected_deal' not in st.session_state:
    st.session_state.selected_deal = None

if 'show_lost' not in st.session_state:
    st.session_state.show_lost = False

# Render shared sidebar
render_sidebar("Sales Pipeline")

# Calculate stats for sidebar
active_deals = [d for d in st.session_state.deals if d['stage'] not in ['won', 'lost']]
total_value = sum(d['value'] for d in active_deals)
won_value = sum(d['value'] for d in st.session_state.deals if d['stage'] == 'won')

render_sidebar_stats({
    "Active Deals": str(len(active_deals)),
    "Pipeline Value": f"${total_value:,}",
    "Won This Month": f"${won_value:,}"
})

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
    return f"{priority_icon} {deal['title']} (${deal['value']:,})"

def find_deal_by_card(card_text):
    """Find deal matching the card text"""
    for deal in st.session_state.deals:
        if format_deal_card(deal) == card_text:
            return deal
    return None

# Function to display deal detail panel
def show_deal_detail(deal_id):
    deal = next((d for d in st.session_state.deals if d['id'] == deal_id), None)
    if not deal:
        return

    st.markdown("---")
    st.markdown(f"## {deal['title']}")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### Description")
        new_desc = st.text_area("Description", deal.get('description', ''), key=f"desc_{deal_id}", height=100, label_visibility="collapsed")
        if new_desc != deal.get('description', ''):
            deal['description'] = new_desc

        st.markdown("### Tasks")
        tasks = deal.get('tasks', [])
        completed = sum(1 for t in tasks if t['complete'])
        if tasks:
            st.progress(completed / len(tasks), text=f"{completed}/{len(tasks)} complete")

        for task in tasks:
            col_check, col_text = st.columns([0.1, 0.9])
            with col_check:
                new_status = st.checkbox("", task['complete'], key=f"task_{deal_id}_{task['id']}", label_visibility="collapsed")
                if new_status != task['complete']:
                    task['complete'] = new_status
                    st.rerun()
            with col_text:
                st.markdown(f"~~{task['text']}~~" if task['complete'] else task['text'])

        new_task = st.text_input("Add a task...", key=f"new_task_{deal_id}", placeholder="Type and press Enter")
        if new_task:
            deal['tasks'].append({"id": f"t{len(deal['tasks'])+1}", "text": new_task, "complete": False})
            st.rerun()

    with col2:
        st.markdown("### Deal Info")

        stages_list = ["lead", "qualified", "proposal", "negotiation", "contract", "won", "lost"]
        stage_names = ["Lead", "Qualified", "Proposal", "Negotiation", "Contract", "Won", "Lost"]
        current_idx = stages_list.index(deal['stage'])
        new_stage = st.selectbox("Stage", stage_names, index=current_idx, key=f"stage_{deal_id}")
        new_stage_id = stages_list[stage_names.index(new_stage)]
        if new_stage_id != deal['stage']:
            deal['stage'] = new_stage_id
            deal['days_in_stage'] = 0
            st.rerun()

        new_value = st.number_input("Value ($)", value=deal['value'], step=1000, key=f"value_{deal_id}")
        if new_value != deal['value']:
            deal['value'] = new_value

        priorities = ["low", "medium", "high"]
        priority_names = ["Low", "Medium", "High"]
        current_priority = priorities.index(deal.get('priority', 'medium'))
        new_priority = st.selectbox("Priority", priority_names, index=current_priority, key=f"priority_{deal_id}")
        deal['priority'] = priorities[priority_names.index(new_priority)]

        st.markdown("---")
        st.markdown(f"**Contact:** {deal['contact']}")
        st.markdown(f"**Company:** {deal['company']}")
        st.markdown(f"**Source:** {deal['source']}")

    if st.button("Close", key=f"close_{deal_id}"):
        st.session_state.selected_deal = None
        st.rerun()

# Main content
st.title("Sales Pipeline")

# Toolbar
toolbar_col1, toolbar_col2, toolbar_col3 = st.columns([2, 1, 1])

with toolbar_col1:
    search = st.text_input("Search deals...", placeholder="Search by name, company, or contact", label_visibility="collapsed")

with toolbar_col2:
    st.session_state.show_lost = st.checkbox("Show Lost Deals", st.session_state.show_lost)

with toolbar_col3:
    if st.button("New Deal", type="primary"):
        st.toast("New deal form coming soon!")

# Filter deals
filtered_deals = st.session_state.deals
if search:
    search_lower = search.lower()
    filtered_deals = [d for d in filtered_deals if
        search_lower in d['title'].lower() or
        search_lower in d['company'].lower() or
        search_lower in d['contact'].lower()]

# Show deal detail if selected
if st.session_state.selected_deal:
    show_deal_detail(st.session_state.selected_deal)
else:
    visible_stages = STAGES.copy()
    if st.session_state.show_lost:
        visible_stages.append({"id": "lost", "name": "Lost", "color": "#dc3545"})

    # Build the sortable board data
    board_data = []
    for stage in visible_stages:
        stage_deals = [d for d in filtered_deals if d['stage'] == stage['id']]
        stage_value = sum(d['value'] for d in stage_deals)
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
                if deal and deal['stage'] != stage['id']:
                    deal['stage'] = stage['id']
                    deal['days_in_stage'] = 0
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
            stage_deals = [d for d in filtered_deals if d['stage'] == stage['id']]
            for deal in stage_deals:
                if st.button(deal['title'][:18], key=f"view_{deal['id']}", use_container_width=True):
                    st.session_state.selected_deal = deal['id']
                    st.rerun()

    # Summary
    st.markdown("---")
    st.subheader("Pipeline Summary")
    metric_cols = st.columns(6)

    with metric_cols[0]:
        st.metric("Leads", f"${sum(d['value'] for d in st.session_state.deals if d['stage'] == 'lead'):,}")
    with metric_cols[1]:
        st.metric("In Progress", f"${sum(d['value'] for d in st.session_state.deals if d['stage'] in ['qualified', 'proposal']):,}")
    with metric_cols[2]:
        st.metric("Closing", f"${sum(d['value'] for d in st.session_state.deals if d['stage'] in ['negotiation', 'contract']):,}")
    with metric_cols[3]:
        st.metric("Won", f"${sum(d['value'] for d in st.session_state.deals if d['stage'] == 'won'):,}")
    with metric_cols[4]:
        st.metric("Lost", f"${sum(d['value'] for d in st.session_state.deals if d['stage'] == 'lost'):,}")
    with metric_cols[5]:
        closed = [d for d in st.session_state.deals if d['stage'] in ['won', 'lost']]
        won = [d for d in st.session_state.deals if d['stage'] == 'won']
        win_rate = (len(won) / len(closed) * 100) if closed else 0
        st.metric("Win Rate", f"{win_rate:.0f}%")
