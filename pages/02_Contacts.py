"""
MPT-CRM Contacts Page
Manage contacts with types, tags, and full detail views
"""

import streamlit as st
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.navigation import render_sidebar, render_sidebar_stats

st.set_page_config(
    page_title="MPT-CRM - Contacts",
    page_icon="👥",
    layout="wide"
)

# Render shared sidebar (includes all styling)
render_sidebar("Contacts")

# Initialize session state for contacts
if 'contacts' not in st.session_state:
    st.session_state.contacts = [
        {
            "id": "c-1",
            "type": "networking",
            "first_name": "John",
            "last_name": "Smith",
            "company": "Smith Consulting",
            "email": "john@smithconsulting.com",
            "phone": "(239) 555-0101",
            "source": "networking",
            "source_detail": "Cape Coral Chamber - Networking at Noon",
            "tags": ["Cape Coral Chamber", "Professional Services"],
            "notes": "Met at Monarca's Mexican restaurant networking event. Interested in workflow automation.",
            "email_status": "active",
            "created_at": "2026-01-23",
            "last_contacted": "2026-01-23"
        },
        {
            "id": "c-2",
            "type": "lead",
            "first_name": "Sarah",
            "last_name": "Johnson",
            "company": "Johnson & Co",
            "email": "sarah@johnsonco.com",
            "phone": "(239) 555-0102",
            "source": "referral",
            "source_detail": "Referred by Mike Williams",
            "tags": ["Referral", "Website Development", "Hot Lead"],
            "notes": "Looking for website redesign with client portal.",
            "email_status": "active",
            "created_at": "2026-01-10",
            "last_contacted": "2026-01-20"
        },
        {
            "id": "c-3",
            "type": "lead",
            "first_name": "Mike",
            "last_name": "Williams",
            "company": "Williams Insurance",
            "email": "mike@williamsins.com",
            "phone": "(239) 555-0103",
            "source": "website",
            "source_detail": "Contact form submission",
            "tags": ["Insurance", "Custom Software", "CRM"],
            "notes": "Needs custom CRM for insurance agency operations.",
            "email_status": "active",
            "created_at": "2026-01-05",
            "last_contacted": "2026-01-15"
        },
        {
            "id": "c-4",
            "type": "client",
            "first_name": "Robert",
            "last_name": "Taylor",
            "company": "Taylor & Associates",
            "email": "robert@taylorassoc.com",
            "phone": "(239) 555-0104",
            "source": "referral",
            "source_detail": "Referred by Cape Coral Chamber member",
            "tags": ["Referral", "Data Migration", "VIP"],
            "notes": "Data migration project signed. Great communicator.",
            "email_status": "active",
            "created_at": "2025-12-15",
            "last_contacted": "2026-01-23"
        },
        {
            "id": "c-5",
            "type": "networking",
            "first_name": "Lisa",
            "last_name": "Martinez",
            "company": "Martinez Realty",
            "email": "lisa@martinezrealty.com",
            "phone": "(239) 555-0105",
            "source": "networking",
            "source_detail": "Cape Coral Chamber - Networking at Noon",
            "tags": ["Cape Coral Chamber", "Real Estate", "Warm"],
            "notes": "Real estate agent. Might need website or CRM in future.",
            "email_status": "active",
            "created_at": "2026-01-23",
            "last_contacted": "2026-01-23"
        },
        {
            "id": "c-6",
            "type": "prospect",
            "first_name": "David",
            "last_name": "Chen",
            "company": "Chen Enterprises",
            "email": "david@chenent.com",
            "phone": "(239) 555-0106",
            "source": "linkedin",
            "source_detail": "LinkedIn connection",
            "tags": ["LinkedIn", "Mobile App", "Nurture"],
            "notes": "Connected on LinkedIn. Interested in mobile app for field team.",
            "email_status": "active",
            "created_at": "2026-01-08",
            "last_contacted": "2026-01-12"
        },
        {
            "id": "c-7",
            "type": "partner",
            "first_name": "Amanda",
            "last_name": "White",
            "company": "White Marketing Agency",
            "email": "amanda@whitemarketing.com",
            "phone": "(239) 555-0107",
            "source": "networking",
            "source_detail": "Fort Myers Chamber",
            "tags": ["Fort Myers Chamber", "Partner", "Referral Source"],
            "notes": "Marketing agency. Could be good referral partner for web projects.",
            "email_status": "active",
            "created_at": "2025-11-20",
            "last_contacted": "2026-01-10"
        },
    ]

if 'selected_contact' not in st.session_state:
    st.session_state.selected_contact = None

# Contact type definitions
CONTACT_TYPES = {
    "networking": {"label": "Networking", "icon": "🤝", "color": "#6c757d"},
    "prospect": {"label": "Prospect", "icon": "🎯", "color": "#17a2b8"},
    "lead": {"label": "Lead", "icon": "🔥", "color": "#fd7e14"},
    "client": {"label": "Client", "icon": "⭐", "color": "#28a745"},
    "former_client": {"label": "Former Client", "icon": "📦", "color": "#6f42c1"},
    "partner": {"label": "Partner", "icon": "🤝", "color": "#20c997"},
    "vendor": {"label": "Vendor", "icon": "🏢", "color": "#adb5bd"},
}

# Available tags
SOURCE_TAGS = ["Cape Coral Chamber", "Fort Myers Chamber", "LinkedIn", "Referral", "Website Inquiry", "Cold Outreach", "Conference"]
INDUSTRY_TAGS = ["Insurance", "Healthcare", "Retail", "Professional Services", "Construction", "Real Estate", "Technology"]
INTEREST_TAGS = ["Custom Software", "Website Development", "Mobile App", "SaaS Product", "Integration", "Automation", "CRM"]
STATUS_TAGS = ["Hot Lead", "Warm", "Cold", "Nurture", "Do Not Contact", "VIP"]

ALL_TAGS = SOURCE_TAGS + INDUSTRY_TAGS + INTEREST_TAGS + STATUS_TAGS


def show_contact_detail(contact_id):
    """Display full contact detail view"""
    contact = next((c for c in st.session_state.contacts if c['id'] == contact_id), None)
    if not contact:
        st.session_state.selected_contact = None
        st.rerun()
        return

    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        contact_type = contact.get('type', 'prospect')
        type_info = CONTACT_TYPES.get(contact_type, CONTACT_TYPES['prospect'])
        st.markdown(f"## {type_info['icon']} {contact['first_name']} {contact['last_name']}")
        st.markdown(f"**{contact['company']}**")
    with col2:
        if st.button("← Back to List"):
            st.session_state.selected_contact = None
            st.rerun()

    st.markdown("---")

    # Two column layout
    col1, col2 = st.columns([2, 1])

    with col1:
        # Contact Info Section
        st.markdown("### 📋 Contact Information")

        edit_col1, edit_col2 = st.columns(2)
        with edit_col1:
            new_first = st.text_input("First Name", contact['first_name'], key="edit_first")
            new_email = st.text_input("Email", contact['email'], key="edit_email")
            new_company = st.text_input("Company", contact['company'], key="edit_company")
        with edit_col2:
            new_last = st.text_input("Last Name", contact['last_name'], key="edit_last")
            new_phone = st.text_input("Phone", contact['phone'], key="edit_phone")
            new_source_detail = st.text_input("Source Detail", contact.get('source_detail', ''), key="edit_source")

        # Update contact if changed
        if (new_first != contact['first_name'] or new_last != contact['last_name'] or
            new_email != contact['email'] or new_phone != contact['phone'] or
            new_company != contact['company']):
            contact['first_name'] = new_first
            contact['last_name'] = new_last
            contact['email'] = new_email
            contact['phone'] = new_phone
            contact['company'] = new_company
            contact['source_detail'] = new_source_detail

        # Notes
        st.markdown("### 📝 Notes")
        new_notes = st.text_area("Notes", contact.get('notes', ''), height=150, key="edit_notes", label_visibility="collapsed")
        if new_notes != contact.get('notes', ''):
            contact['notes'] = new_notes

        # Activity Timeline (placeholder)
        st.markdown("### 📅 Recent Activity")
        with st.container(border=True):
            st.caption(f"📧 Email sent - {contact['last_contacted']}")
            st.caption(f"📝 Contact created - {contact['created_at']}")
            st.caption("_More activity tracking coming soon..._")

    with col2:
        # Type selector
        st.markdown("### 🏷️ Contact Type")
        type_options = list(CONTACT_TYPES.keys())
        type_labels = [f"{CONTACT_TYPES[t]['icon']} {CONTACT_TYPES[t]['label']}" for t in type_options]
        current_type = contact.get('type', 'prospect')
        current_type_idx = type_options.index(current_type) if current_type in type_options else 0
        new_type_label = st.selectbox("Type", type_labels, index=current_type_idx, key="edit_type")
        new_type = type_options[type_labels.index(new_type_label)]
        if new_type != current_type:
            contact['type'] = new_type
            st.rerun()

        # Source
        st.markdown("### 📍 Source")
        sources = ["networking", "referral", "website", "linkedin", "cold_outreach", "conference"]
        source_labels = ["Networking Event", "Referral", "Website", "LinkedIn", "Cold Outreach", "Conference"]
        current_source_idx = sources.index(contact['source']) if contact['source'] in sources else 0
        new_source_label = st.selectbox("Source", source_labels, index=current_source_idx, key="edit_source_type")
        contact['source'] = sources[source_labels.index(new_source_label)]

        # Tags
        st.markdown("### 🏷️ Tags")
        current_tags = contact.get('tags', [])

        # Display current tags
        if current_tags:
            for tag in current_tags:
                col_tag, col_remove = st.columns([4, 1])
                with col_tag:
                    st.markdown(f"`{tag}`")
                with col_remove:
                    if st.button("✕", key=f"remove_tag_{tag}"):
                        contact['tags'].remove(tag)
                        st.rerun()

        # Add new tag
        new_tag = st.selectbox("Add tag:", [""] + [t for t in ALL_TAGS if t not in current_tags], key="add_tag")
        if new_tag:
            contact['tags'].append(new_tag)
            st.rerun()

        # Email status
        st.markdown("### 📧 Email Status")
        email_statuses = ["active", "unsubscribed", "bounced"]
        status_labels = ["✅ Active", "🚫 Unsubscribed", "⚠️ Bounced"]
        current_status_idx = email_statuses.index(contact.get('email_status', 'active'))
        new_status = st.selectbox("Status", status_labels, index=current_status_idx, key="email_status")
        contact['email_status'] = email_statuses[status_labels.index(new_status)]

        # Quick actions
        st.markdown("### ⚡ Quick Actions")
        if st.button("📧 Send Email", use_container_width=True):
            st.toast("Email feature coming with SendGrid integration!")
        if st.button("📞 Log Call", use_container_width=True):
            st.toast("Call logging coming soon!")
        if st.button("📝 Add Task", use_container_width=True):
            st.toast("Task creation coming soon!")
        if st.button("🎯 Create Deal", use_container_width=True):
            st.toast("Deal creation coming soon!")
        if st.button("📧 Enroll in Campaign", use_container_width=True):
            st.toast("Campaign enrollment coming soon!")


# Main page
st.title("👥 Contacts")

# Show detail view if contact selected
if st.session_state.selected_contact:
    show_contact_detail(st.session_state.selected_contact)
else:
    # Toolbar
    toolbar_col1, toolbar_col2, toolbar_col3, toolbar_col4 = st.columns([2, 1, 1, 1])

    with toolbar_col1:
        search = st.text_input("🔍 Search contacts...", placeholder="Name, company, or email", label_visibility="collapsed")

    with toolbar_col2:
        type_filter = st.selectbox("Type", ["All Types"] + [CONTACT_TYPES[t]['label'] for t in CONTACT_TYPES], label_visibility="collapsed")

    with toolbar_col3:
        tag_filter = st.selectbox("Tag", ["All Tags"] + ALL_TAGS, label_visibility="collapsed")

    with toolbar_col4:
        if st.button("➕ New Contact", type="primary"):
            st.toast("New contact form coming soon!")

    # Filter contacts
    filtered_contacts = st.session_state.contacts

    if search:
        search_lower = search.lower()
        filtered_contacts = [c for c in filtered_contacts if
            search_lower in c['first_name'].lower() or
            search_lower in c['last_name'].lower() or
            search_lower in c['company'].lower() or
            search_lower in c['email'].lower()]

    if type_filter != "All Types":
        type_key = next(k for k, v in CONTACT_TYPES.items() if v['label'] == type_filter)
        filtered_contacts = [c for c in filtered_contacts if c['type'] == type_key]

    if tag_filter != "All Tags":
        filtered_contacts = [c for c in filtered_contacts if tag_filter in c.get('tags', [])]

    # Stats row
    stat_cols = st.columns(7)
    for i, (type_key, type_info) in enumerate(CONTACT_TYPES.items()):
        count = len([c for c in st.session_state.contacts if c['type'] == type_key])
        with stat_cols[i]:
            st.metric(f"{type_info['icon']} {type_info['label']}", count)

    st.markdown("---")

    # Contact list
    st.markdown(f"### Showing {len(filtered_contacts)} contacts")

    for contact in filtered_contacts:
        contact_type = contact.get('type', 'prospect')
        type_info = CONTACT_TYPES.get(contact_type, CONTACT_TYPES['prospect'])

        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

            with col1:
                st.markdown(f"**{type_info['icon']} {contact['first_name']} {contact['last_name']}**")
                st.caption(f"🏢 {contact['company']}")

            with col2:
                st.markdown(f"📧 {contact['email']}")
                st.caption(f"📞 {contact['phone']}")

            with col3:
                tags = contact.get('tags', [])[:3]  # Show first 3 tags
                if tags:
                    st.markdown(" ".join([f"`{t}`" for t in tags]))
                st.caption(f"Last contact: {contact['last_contacted']}")

            with col4:
                if st.button("Open", key=f"open_{contact['id']}"):
                    st.session_state.selected_contact = contact['id']
                    st.rerun()
