"""
MPT-CRM Time & Billing Page
Track time entries, generate invoices, and manage billing
"""

import streamlit as st
from datetime import datetime, date, timedelta
import sys
from pathlib import Path

# Add project root to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.navigation import render_sidebar, render_sidebar_stats

st.set_page_config(
    page_title="MPT-CRM - Time & Billing",
    page_icon="💰",
    layout="wide"
)

# Render shared sidebar
render_sidebar("Time & Billing")

# Initialize session state
if 'invoices' not in st.session_state:
    st.session_state.invoices = [
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

# Use time_entries from Projects page if available
if 'time_entries' not in st.session_state:
    st.session_state.time_entries = []

if 'projects' not in st.session_state:
    st.session_state.projects = []

# Invoice status definitions
INVOICE_STATUS = {
    "draft": {"label": "Draft", "icon": "📝", "color": "#6c757d"},
    "sent": {"label": "Sent", "icon": "📨", "color": "#007bff"},
    "paid": {"label": "Paid", "icon": "✅", "color": "#28a745"},
    "overdue": {"label": "Overdue", "icon": "⚠️", "color": "#dc3545"},
    "cancelled": {"label": "Cancelled", "icon": "❌", "color": "#6c757d"},
}

# Main page
st.title("💰 Time & Billing")

# Tabs for different views
tab1, tab2, tab3 = st.tabs(["⏱️ Time Tracking", "📄 Invoices", "📊 Summary"])

# ============================================
# TIME TRACKING TAB
# ============================================
with tab1:
    st.markdown("### ⏱️ Time Entries")

    # Quick time entry
    with st.expander("➕ Log Time Entry", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            # Get project options
            project_options = ["-- Select Project --"] + [p['name'] for p in st.session_state.projects]
            selected_project = st.selectbox("Project", project_options, key="te_project")

            entry_date = st.date_input("Date", value=date.today(), key="te_date")
            entry_hours = st.number_input("Hours", min_value=0.0, max_value=24.0, step=0.25, value=1.0, key="te_hours")

        with col2:
            entry_desc = st.text_area("Description", height=100, key="te_desc", placeholder="What did you work on?")
            entry_billable = st.checkbox("Billable", value=True, key="te_billable")

        if st.button("Add Entry", type="primary"):
            if selected_project != "-- Select Project --" and entry_hours > 0:
                project = next((p for p in st.session_state.projects if p['name'] == selected_project), None)
                if project:
                    new_entry = {
                        "id": f"te-{len(st.session_state.time_entries) + 1}",
                        "project_id": project['id'],
                        "project_name": project['name'],
                        "date": entry_date.strftime("%Y-%m-%d"),
                        "hours": entry_hours,
                        "description": entry_desc,
                        "billable": entry_billable,
                        "invoiced": False
                    }
                    st.session_state.time_entries.append(new_entry)
                    project['hours_logged'] = project.get('hours_logged', 0) + entry_hours
                    st.success(f"Added {entry_hours} hours to {selected_project}")
                    st.rerun()
            else:
                st.warning("Please select a project and enter hours")

    # Filter options
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        date_range = st.selectbox("Date Range", ["This Week", "This Month", "Last 30 Days", "All Time"], key="te_filter_date")
    with filter_col2:
        project_filter = st.selectbox("Project", ["All Projects"] + [p['name'] for p in st.session_state.projects], key="te_filter_project")
    with filter_col3:
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
    filtered_entries = st.session_state.time_entries

    if start_date:
        filtered_entries = [e for e in filtered_entries if datetime.strptime(e['date'], "%Y-%m-%d").date() >= start_date]

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
                    project_name = entry.get('project_name', 'Unknown Project')
                    st.markdown(f"**{project_name}**")
                    st.caption(entry.get('description', 'No description'))

                with col3:
                    st.markdown(f"**{entry['hours']:.2f} hrs**")
                    if entry.get('billable'):
                        st.caption(f"💰 ${entry['hours'] * default_rate:.0f}")

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
            st.toast("Invoice creation wizard coming soon!")

    # Invoice stats
    draft_invoices = [i for i in st.session_state.invoices if i['status'] == 'draft']
    sent_invoices = [i for i in st.session_state.invoices if i['status'] == 'sent']
    paid_invoices = [i for i in st.session_state.invoices if i['status'] == 'paid']

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
    if st.session_state.invoices:
        for invoice in sorted(st.session_state.invoices, key=lambda x: x['created_at'], reverse=True):
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
    month_entries = [e for e in st.session_state.time_entries
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

    # By project breakdown
    st.markdown("#### By Project")

    project_summary = {}
    for entry in st.session_state.time_entries:
        proj_name = entry.get('project_name', 'Unknown')
        if proj_name not in project_summary:
            project_summary[proj_name] = {"hours": 0, "billable_hours": 0}
        project_summary[proj_name]["hours"] += entry['hours']
        if entry.get('billable', True):
            project_summary[proj_name]["billable_hours"] += entry['hours']

    if project_summary:
        for proj_name, data in project_summary.items():
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"**{proj_name}**")
                with col2:
                    st.metric("Hours", f"{data['hours']:.1f}")
                with col3:
                    st.metric("Revenue", f"${data['billable_hours'] * default_rate:,.0f}")
    else:
        st.info("No time tracked yet.")

# Sidebar stats
render_sidebar_stats({
    "Hours This Month": f"{month_hours:.1f}",
    "Revenue": f"${month_revenue:,.0f}",
    "Outstanding": f"${total_outstanding:,.0f}"
})
