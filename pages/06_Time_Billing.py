"""
MPT-CRM Time & Billing Page
Track time entries, generate invoices, and manage billing

Database operations are handled by db_service.py — the single source of truth.
"""

import streamlit as st
from datetime import datetime, date, timedelta
from db_service import (
    db_is_connected,
    db_get_contacts, db_get_projects, db_get_time_entries,
    db_create_time_entry, db_get_invoices, db_update_invoice,
    db_create_invoice,
)

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
    "Contacts": {"icon": "👥", "path": "pages/02_Contacts.py"},
    "Sales Pipeline": {"icon": "🎯", "path": "pages/03_Pipeline.py"},
    "Projects": {"icon": "📁", "path": "pages/04_Projects.py"},
    "Tasks": {"icon": "✅", "path": "pages/05_Tasks.py"},
    "Time & Billing": {"icon": "💰", "path": "pages/06_Time_Billing.py"},
    "Marketing": {"icon": "📧", "path": "pages/07_Marketing.py"},
    "Reports": {"icon": "📈", "path": "pages/08_Reports.py"},
    "Settings": {"icon": "⚙️", "path": "pages/09_Settings.py"},
}

def render_sidebar(current_page="Time & Billing"):
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
    page_title="MPT-CRM - Time & Billing",
    page_icon="favicon.jpg",
    layout="wide"
)

# ============================================
# RENDER SIDEBAR
# ============================================
render_sidebar("Time & Billing")

# Show database connection status in sidebar
with st.sidebar:
    if db_is_connected():
        st.success("Database connected", icon="✅")
    else:
        st.error("Database not connected - check .env file", icon="❌")

# ============================================
# INITIALIZE SESSION STATE
# ============================================
if 'tb_invoices' not in st.session_state:
    st.session_state.tb_invoices = [
        {
            "id": "inv-1",
            "invoice_number": "INV-2026-001",
            "client": "Taylor & Associates",
            "client_id": "c-4",
            "project": "Taylor Data Migration",
            "project_id": "proj-2",
            "status": "sent",
            "subtotal": 2700,
            "tax_rate": 0,
            "total": 2700,
            "due_date": "2026-02-15",
            "created_at": "2026-01-20",
            "sent_at": "2026-01-20"
        },
    ]

# Use time_entries with page-specific prefix
if 'tb_time_entries' not in st.session_state:
    st.session_state.tb_time_entries = []

if 'tb_projects' not in st.session_state:
    st.session_state.tb_projects = []

# Invoice status definitions
INVOICE_STATUS = {
    "draft": {"label": "Draft", "icon": "📝", "color": "#6c757d"},
    "sent": {"label": "Sent", "icon": "📨", "color": "#007bff"},
    "paid": {"label": "Paid", "icon": "✅", "color": "#28a745"},
    "overdue": {"label": "Overdue", "icon": "⚠️", "color": "#dc3545"},
    "cancelled": {"label": "Cancelled", "icon": "❌", "color": "#6c757d"},
}

# ============================================
# CACHED DATA LOADERS
# ============================================
def get_cached_clients():
    """Get clients from cache or load on first access"""
    if 'tb_cached_clients' not in st.session_state:
        if db_is_connected():
            all_contacts = db_get_contacts()
            st.session_state.tb_cached_clients = [c for c in all_contacts if c.get('type') == 'client']
        else:
            st.session_state.tb_cached_clients = []
    return st.session_state.tb_cached_clients

def get_cached_projects():
    """Get projects from cache or load on first access"""
    if 'tb_cached_projects' not in st.session_state:
        if db_is_connected():
            st.session_state.tb_cached_projects = db_get_projects()
        else:
            st.session_state.tb_cached_projects = st.session_state.tb_projects
    return st.session_state.tb_cached_projects

# ============================================
# MAIN PAGE
# ============================================
st.title("💰 Time & Billing")

# Tabs for different views
tab1, tab2, tab3 = st.tabs(["⏱️ Time Tracking", "📄 Invoices", "📊 Summary"])

# ============================================
# TIME TRACKING TAB
# ============================================
with tab1:
    st.markdown("### ⏱️ Time Entries")

    # Quick time entry - only load data when expander is opened
    with st.expander("➕ Log Time Entry", expanded=False):
        # Load cached data only when this section is visible
        clients = get_cached_clients()
        all_projects = get_cached_projects()

        col1, col2 = st.columns(2)

        with col1:
            # Step 1: Select Client first
            client_options = ["-- Select Client --"] + [
                f"{c.get('company', '')} ({c['first_name']} {c['last_name']})" if c.get('company')
                else f"{c['first_name']} {c['last_name']}"
                for c in clients
            ]
            selected_client_display = st.selectbox("Client *", client_options, key="te_client")

            # Get selected client ID
            selected_client = None
            if selected_client_display != "-- Select Client --":
                client_idx = client_options.index(selected_client_display) - 1
                if 0 <= client_idx < len(clients):
                    selected_client = clients[client_idx]

            # Step 2: Filter projects by selected client
            if selected_client:
                client_projects = [p for p in all_projects if p.get('client_id') == selected_client['id']]
                if client_projects:
                    project_options = ["-- Select Project --"] + [p['name'] for p in client_projects]
                else:
                    project_options = ["-- No projects for this client --"]
            else:
                project_options = ["-- Select Client First --"]

            selected_project = st.selectbox("Project *", project_options, key="te_project")

            entry_date = st.date_input("Date", value=date.today(), key="te_date")
            entry_hours = st.number_input("Hours", min_value=0.0, max_value=24.0, step=0.25, value=1.0, key="te_hours")

        with col2:
            entry_desc = st.text_area("Description", height=100, key="te_desc", placeholder="What did you work on?")
            entry_billable = st.checkbox("Billable", value=True, key="te_billable")
            hourly_rate = st.number_input("Hourly Rate ($)", min_value=0.0, step=25.0, value=150.0, key="te_rate")

        if st.button("Add Entry", type="primary"):
            if selected_client and selected_project not in ["-- Select Project --", "-- Select Client First --", "-- No projects for this client --"] and entry_hours > 0:
                # Find the project
                project = next((p for p in all_projects if p['name'] == selected_project), None)
                if project:
                    # Get client display name
                    client_name = selected_client.get('company') or f"{selected_client['first_name']} {selected_client['last_name']}"

                    new_entry = {
                        "id": f"te-{len(st.session_state.tb_time_entries) + 1}",
                        "project_id": project['id'],
                        "project_name": project['name'],
                        "client_id": selected_client['id'],
                        "client_name": client_name,
                        "date": entry_date.strftime("%Y-%m-%d"),
                        "hours": entry_hours,
                        "hourly_rate": hourly_rate,
                        "description": entry_desc,
                        "billable": entry_billable,
                        "invoiced": False
                    }

                    # Save to database if connected
                    if db_is_connected():
                        db_create_time_entry({
                            "project_id": project['id'],
                            "description": entry_desc,
                            "hours": entry_hours,
                            "hourly_rate": hourly_rate,
                            "date": entry_date.strftime("%Y-%m-%d"),
                            "is_billable": entry_billable,
                            "is_invoiced": False
                        })

                    st.session_state.tb_time_entries.append(new_entry)
                    st.success(f"Added {entry_hours} hours to {client_name} - {selected_project}")
                    st.rerun()
            else:
                st.warning("Please select a client, project, and enter hours")

    # Filter options
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
    with filter_col1:
        date_range = st.selectbox("Date Range", ["This Week", "This Month", "Last 30 Days", "All Time"], key="te_filter_date")
    with filter_col2:
        # Client filter
        client_filter_options = ["All Clients"] + list(set(e.get('client_name', 'Unknown') for e in st.session_state.tb_time_entries if e.get('client_name')))
        client_filter = st.selectbox("Client", client_filter_options, key="te_filter_client")
    with filter_col3:
        # Get projects for filter dropdown
        filter_projects = get_cached_projects()
        project_filter = st.selectbox("Project", ["All Projects"] + [p['name'] for p in filter_projects], key="te_filter_project")
    with filter_col4:
        billable_filter = st.selectbox("Type", ["All", "Billable Only", "Non-Billable Only"], key="te_filter_billable")

    # Calculate date filter
    today = date.today()
    if date_range == "This Week":
        start_date = today - timedelta(days=today.weekday())
    elif date_range == "This Month":
        start_date = today.replace(day=1)
    elif date_range == "Last 30 Days":
        start_date = today - timedelta(days=30)
    else:
        start_date = None

    # Filter entries
    filtered_entries = st.session_state.tb_time_entries

    if start_date:
        filtered_entries = [e for e in filtered_entries if datetime.strptime(e['date'], "%Y-%m-%d").date() >= start_date]

    if client_filter != "All Clients":
        filtered_entries = [e for e in filtered_entries if e.get('client_name') == client_filter]

    if project_filter != "All Projects":
        filtered_entries = [e for e in filtered_entries if e.get('project_name') == project_filter]

    if billable_filter == "Billable Only":
        filtered_entries = [e for e in filtered_entries if e.get('billable', True)]
    elif billable_filter == "Non-Billable Only":
        filtered_entries = [e for e in filtered_entries if not e.get('billable', True)]

    # Sort by date descending
    filtered_entries = sorted(filtered_entries, key=lambda x: x['date'], reverse=True)

    # Summary stats
    total_hours = sum(e['hours'] for e in filtered_entries)
    billable_hours = sum(e['hours'] for e in filtered_entries if e.get('billable', True))
    default_rate = 150
    billable_amount = billable_hours * default_rate

    stat_col1, stat_col2, stat_col3 = st.columns(3)
    with stat_col1:
        st.metric("Total Hours", f"{total_hours:.1f}")
    with stat_col2:
        st.metric("Billable Hours", f"{billable_hours:.1f}")
    with stat_col3:
        st.metric("Billable Amount", f"${billable_amount:,.0f}")

    st.markdown("---")

    # Time entries list
    if filtered_entries:
        for entry in filtered_entries:
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([1, 3, 1, 1])

                with col1:
                    st.markdown(f"**{entry['date']}**")

                with col2:
                    client_name = entry.get('client_name', '')
                    project_name = entry.get('project_name', 'Unknown Project')
                    if client_name:
                        st.markdown(f"**{client_name}**")
                        st.caption(f"📁 {project_name}")
                    else:
                        st.markdown(f"**{project_name}**")
                    if entry.get('description'):
                        st.caption(entry.get('description'))

                with col3:
                    rate = entry.get('hourly_rate', default_rate)
                    st.markdown(f"**{entry['hours']:.2f} hrs**")
                    if entry.get('billable'):
                        st.caption(f"💰 ${entry['hours'] * rate:.0f}")

                with col4:
                    if entry.get('billable'):
                        if entry.get('invoiced'):
                            st.markdown("✅ Invoiced")
                        else:
                            st.markdown("💰 Billable")
                    else:
                        st.markdown("⬜ Non-billable")
    else:
        st.info("No time entries found. Log your first entry above!")

# ============================================
# INVOICES TAB
# ============================================
with tab2:
    st.markdown("### 📄 Invoices")

    # New invoice button
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("➕ Create Invoice", type="primary"):
            st.session_state.tb_show_invoice_wizard = True
            st.rerun()

    # Invoice creation wizard
    if st.session_state.get('tb_show_invoice_wizard'):
        with st.container(border=True):
            st.markdown("### ➕ New Invoice")
            with st.form("create_invoice_form"):
                inv_col1, inv_col2 = st.columns(2)
                with inv_col1:
                    inv_client = st.text_input("Client Name *")
                    inv_number = st.text_input("Invoice Number", value=f"INV-{datetime.now().strftime('%Y%m%d')}-{len(st.session_state.get('tb_invoices', [])) + 1:03d}")
                with inv_col2:
                    inv_amount = st.number_input("Total Amount ($)", min_value=0.0, step=100.0)
                    inv_due_date = st.date_input("Due Date", value=date.today() + timedelta(days=30))

                inv_description = st.text_area("Description / Line Items", height=100)

                inv_col_a, inv_col_b = st.columns(2)
                with inv_col_a:
                    inv_submit = st.form_submit_button("📄 Create Invoice", type="primary")
                with inv_col_b:
                    inv_cancel = st.form_submit_button("Cancel")

                if inv_submit and inv_client:
                    new_invoice = {
                        "invoice_number": inv_number,
                        "client": inv_client,
                        "total": inv_amount,
                        "status": "draft",
                        "created_at": datetime.now().isoformat(),
                        "due_date": inv_due_date.isoformat(),
                        "description": inv_description,
                    }
                    # Save to database if connected
                    if db_is_connected():
                        db_create_invoice(new_invoice)
                    # Add to session state
                    if 'tb_invoices' not in st.session_state:
                        st.session_state.tb_invoices = []
                    st.session_state.tb_invoices.append(new_invoice)
                    st.session_state.tb_show_invoice_wizard = False
                    st.success(f"✅ Invoice {inv_number} created for {inv_client}")
                    st.rerun()
                elif inv_cancel:
                    st.session_state.tb_show_invoice_wizard = False
                    st.rerun()

    # Invoice stats
    draft_invoices = [i for i in st.session_state.tb_invoices if i['status'] == 'draft']
    sent_invoices = [i for i in st.session_state.tb_invoices if i['status'] == 'sent']
    paid_invoices = [i for i in st.session_state.tb_invoices if i['status'] == 'paid']

    total_outstanding = sum(i['total'] for i in sent_invoices)
    total_paid = sum(i['total'] for i in paid_invoices)

    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
    with stat_col1:
        st.metric("📝 Draft", len(draft_invoices))
    with stat_col2:
        st.metric("📨 Sent", len(sent_invoices))
    with stat_col3:
        st.metric("Outstanding", f"${total_outstanding:,.0f}")
    with stat_col4:
        st.metric("Paid (All Time)", f"${total_paid:,.0f}")

    st.markdown("---")

    # Invoice list
    if st.session_state.tb_invoices:
        for invoice in sorted(st.session_state.tb_invoices, key=lambda x: x['created_at'], reverse=True):
            status_info = INVOICE_STATUS.get(invoice['status'], INVOICE_STATUS['draft'])

            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

                with col1:
                    st.markdown(f"**{invoice['invoice_number']}**")
                    st.caption(f"🏢 {invoice['client']}")

                with col2:
                    st.markdown(f"📁 {invoice['project']}")
                    st.caption(f"Due: {invoice['due_date']}")

                with col3:
                    st.markdown(f"**${invoice['total']:,.0f}**")

                with col4:
                    st.markdown(f"{status_info['icon']} {status_info['label']}")

                    if invoice['status'] == 'draft':
                        if st.button("Send", key=f"send_{invoice['id']}"):
                            invoice['status'] = 'sent'
                            invoice['sent_at'] = date.today().strftime("%Y-%m-%d")
                            st.rerun()
                    elif invoice['status'] == 'sent':
                        if st.button("Mark Paid", key=f"paid_{invoice['id']}"):
                            invoice['status'] = 'paid'
                            st.rerun()
    else:
        st.info("No invoices yet. Create your first invoice!")

# ============================================
# SUMMARY TAB
# ============================================
with tab3:
    st.markdown("### 📊 Billing Summary")

    # This month's summary
    st.markdown("#### This Month")

    this_month = date.today().replace(day=1)
    month_entries = [e for e in st.session_state.tb_time_entries
                     if datetime.strptime(e['date'], "%Y-%m-%d").date() >= this_month]

    month_hours = sum(e['hours'] for e in month_entries)
    month_billable = sum(e['hours'] for e in month_entries if e.get('billable', True))
    month_revenue = month_billable * default_rate

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Hours Worked", f"{month_hours:.1f}")
    with col2:
        st.metric("Billable Hours", f"{month_billable:.1f}")
    with col3:
        st.metric("Revenue", f"${month_revenue:,.0f}")

    st.markdown("---")

    # By client breakdown
    st.markdown("#### By Client")

    client_summary = {}
    for entry in st.session_state.tb_time_entries:
        client_name = entry.get('client_name', 'Unknown Client')
        proj_name = entry.get('project_name', 'Unknown Project')
        rate = entry.get('hourly_rate', default_rate)

        if client_name not in client_summary:
            client_summary[client_name] = {"hours": 0, "billable_hours": 0, "revenue": 0, "projects": set()}

        client_summary[client_name]["hours"] += entry['hours']
        client_summary[client_name]["projects"].add(proj_name)
        if entry.get('billable', True):
            client_summary[client_name]["billable_hours"] += entry['hours']
            client_summary[client_name]["revenue"] += entry['hours'] * rate

    if client_summary:
        for client_name, data in sorted(client_summary.items()):
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.markdown(f"**{client_name}**")
                    projects_list = ", ".join(list(data['projects'])[:3])
                    if len(data['projects']) > 3:
                        projects_list += f" +{len(data['projects']) - 3} more"
                    st.caption(f"📁 {projects_list}")
                with col2:
                    st.metric("Hours", f"{data['hours']:.1f}")
                with col3:
                    st.metric("Billable", f"{data['billable_hours']:.1f}")
                with col4:
                    st.metric("Revenue", f"${data['revenue']:,.0f}")
    else:
        st.info("No time tracked yet.")

# ============================================
# SIDEBAR STATS
# ============================================
render_sidebar_stats({
    "Hours This Month": f"{month_hours:.1f}",
    "Revenue": f"${month_revenue:,.0f}",
    "Outstanding": f"${total_outstanding:,.0f}"
})
