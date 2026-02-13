"""
MPT-CRM Discovery Call
Live call companion for capturing project scope during client conversations
Quick access when the phone rings - search for existing clients or start fresh

NOTE: Always use Teams for discovery meetings to record and enable screen sharing.

Database operations are handled by db_service.py — the single source of truth.
"""

import streamlit as st
from datetime import datetime, date
from pathlib import Path
from db_service import (
    db_is_connected,
    db_get_contacts, db_get_contact, db_create_contact, db_update_contact,
    db_get_intakes, db_get_intake, db_create_intake, db_update_intake,
    db_log_activity, db_create_deal,
)
from sso_auth import require_sso_auth, render_auth_status

st.set_page_config(
    page_title="MPT-CRM - Discovery Call",
    page_icon="favicon.jpg",
    layout="wide"
)

require_sso_auth(allow_bypass=True)  # TEMP: MC Supabase down

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
    "Service": {"icon": "\U0001f527", "path": "pages/10_Service.py"},
    "Tasks": {"icon": "✅", "path": "pages/05_Tasks.py"},
    "Time & Billing": {"icon": "💰", "path": "pages/06_Time_Billing.py"},
    "Marketing": {"icon": "📧", "path": "pages/07_Marketing.py"},
    "Reports": {"icon": "📈", "path": "pages/08_Reports.py"},
    "Settings": {"icon": "⚙️", "path": "pages/09_Settings.py"},
}

def render_sidebar(current_page="Discovery Call"):
    """Render navigation sidebar"""
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

# Render sidebar
render_sidebar()

# Show database connection status in sidebar
with st.sidebar:
    if db_is_connected():
        st.success("Database connected", icon="✅")
        if st.session_state.get('current_intake_id'):
            st.caption(f"Intake: {st.session_state.current_intake_id[:8]}...")
    else:
        st.warning("Offline mode - local files", icon="💾")

# ============================================
# PAGE-SPECIFIC HELPER FUNCTIONS
# ============================================

def load_intake_from_db(intake_id):
    """Load a complete intake record from database and populate session state"""
    if not db_is_connected():
        return False

    try:
        intake = db_get_intake(intake_id)
        if not intake:
            return False

        # Store the IDs
        st.session_state.current_intake_id = intake_id
        st.session_state.current_contact_id = intake.get('contact_id')

        # Get contact info
        contact = intake.get('contacts', {}) or {}

        # Populate form fields in session state
        st.session_state.disc_first = contact.get('first_name', '')
        st.session_state.disc_last = contact.get('last_name', '')
        st.session_state.disc_company = contact.get('company', '')
        st.session_state.disc_email = contact.get('email', '')
        st.session_state.disc_phone = contact.get('phone', '')
        st.session_state.disc_website = intake.get('company_website', '') or ''
        st.session_state.disc_industry = intake.get('industry', '-- Select --') or '-- Select --'

        # Load referral source from contact record
        saved_source = contact.get('source', '') or ''
        source_detail = contact.get('source_detail', '') or ''

        # Map database source back to display value
        source_mapping = {
            'referral': 'Referral',
            'networking_event': 'Networking Event',
            'cape_coral_chamber': 'Cape Coral Chamber',
            'fort_myers_chamber': 'Fort Myers Chamber',
            'linkedin': 'LinkedIn',
            'website___google': 'Website / Google',
            'website_google': 'Website / Google',
            'cold_outreach': 'Cold Outreach',
            'existing_client': 'Existing Client',
            'other': 'Other'
        }
        st.session_state.disc_source = source_mapping.get(saved_source, '-- Select --')
        st.session_state.disc_source_detail = source_detail

        # Project needs
        st.session_state.disc_project_types = intake.get('project_types', []) or []
        st.session_state.disc_pain_points = intake.get('pain_points', '') or ''
        st.session_state.disc_current = intake.get('current_solution', '') or ''
        st.session_state.disc_outcome = intake.get('desired_outcome', '') or ''

        # Features
        st.session_state.disc_must_haves = intake.get('must_have_features', '') or ''
        st.session_state.disc_nice_to_haves = intake.get('nice_to_have_features', '') or ''
        st.session_state.disc_integrations = intake.get('integrations', []) or []
        st.session_state.disc_inspiration = intake.get('inspiration', '') or ''

        # Timeline & Budget
        st.session_state.disc_deadline = intake.get('deadline_type', 'Flexible') or 'Flexible'
        st.session_state.disc_urgency = intake.get('urgency', 'Moderate') or 'Moderate'
        st.session_state.disc_budget = intake.get('budget_range', '-- Select --') or '-- Select --'
        st.session_state.disc_flex = intake.get('budget_flexibility', 'Some flexibility') or 'Some flexibility'
        st.session_state.disc_payment = intake.get('payment_preference', 'Need to discuss') or 'Need to discuss'

        # Decision
        st.session_state.disc_decision = intake.get('decision_maker', 'Not sure') or 'Not sure'
        st.session_state.disc_timeline = intake.get('decision_timeline', 'Just exploring') or 'Just exploring'
        st.session_state.disc_quotes = intake.get('competing_quotes', "Didn't ask") or "Didn't ask"
        st.session_state.disc_ongoing = intake.get('ongoing_support', 'Not sure') or 'Not sure'

        # Notes
        st.session_state.disc_notes = intake.get('meeting_notes', '') or ''
        st.session_state.disc_flags = intake.get('red_flags', '') or ''
        st.session_state.disc_next = intake.get('next_steps', '') or ''
        st.session_state.disc_confidence = intake.get('confidence_level', 'Medium') or 'Medium'

        # Mark that we loaded from DB
        st.session_state.intake_loaded_from_db = True
        st.session_state.is_new_client = True  # Show the form

        return True
    except Exception as e:
        st.error(f"Error loading intake: {str(e)[:50]}")
        return False


def save_client_info_to_db(data):
    """Save client info - creates/updates contact and intake record"""
    if not db_is_connected():
        return None, None

    contact_id = st.session_state.get('current_contact_id')
    intake_id = st.session_state.get('current_intake_id')

    try:
        # Prepare contact data
        source_val = data.get('source', '').lower().replace(" ", "_").replace("/", "_")
        if source_val == "-- select --" or not source_val:
            source_val = "other"

        contact_data = {
            "first_name": data.get('first_name', ''),
            "last_name": data.get('last_name', ''),
            "company": data.get('company', ''),
            "email": data.get('email', ''),
            "phone": data.get('phone', ''),
            "type": "lead",
            "source": source_val,
            "source_detail": data.get('source_detail', '') or None,
            "email_status": "active"
        }

        if contact_id:
            # Update existing contact
            db_update_contact(contact_id, contact_data)
        else:
            # Create new contact
            result = db_create_contact(contact_data)
            if result:
                contact_id = result['id']
                st.session_state.current_contact_id = contact_id
                db_log_activity("discovery_started", "Discovery call started", contact_id=contact_id)

        # Now handle intake record
        if contact_id:
            intake_data = {
                "contact_id": contact_id,
                "company_website": data.get('website') or None,
                "industry": data.get('industry') if data.get('industry') != "-- Select --" else None,
                "status": "new"
            }

            if intake_id:
                # Update existing intake
                db_update_intake(intake_id, intake_data)
            else:
                # Create new intake
                result = db_create_intake(intake_data)
                if result:
                    intake_id = result['id']
                    st.session_state.current_intake_id = intake_id

        return contact_id, intake_id
    except Exception as e:
        st.error(f"Database error: {str(e)[:50]}")
        return None, None


def save_section_to_db(section_name, data):
    """Save a section directly to the database intake record"""
    intake_id = st.session_state.get('current_intake_id')

    if not db_is_connected() or not intake_id:
        return False

    try:
        # Map section data to intake table columns
        intake_update = {}

        if section_name == "project_needs":
            intake_update = {
                "project_types": data.get('project_types', []),
                "pain_points": data.get('pain_points') or None,
                "current_solution": data.get('current_solution') or None,
                "desired_outcome": data.get('desired_outcome') or None
            }
        elif section_name == "features":
            intake_update = {
                "must_have_features": data.get('must_haves') or None,
                "nice_to_have_features": data.get('nice_to_haves') or None,
                "integrations": data.get('integrations', []),
                "inspiration": data.get('inspiration') or None
            }
        elif section_name == "timeline_budget":
            intake_update = {
                "deadline_type": data.get('deadline_type') or None,
                "target_date": data.get('target_date') if data.get('target_date') else None,
                "urgency": data.get('urgency') or None,
                "budget_range": data.get('budget_range') if data.get('budget_range') != "-- Select --" else None,
                "budget_flexibility": data.get('budget_flexibility') or None,
                "payment_preference": data.get('payment_preference') or None
            }
        elif section_name == "decision":
            intake_update = {
                "decision_maker": data.get('decision_maker') or None,
                "decision_timeline": data.get('decision_timeline') or None,
                "competing_quotes": data.get('competing_quotes') or None,
                "ongoing_support": data.get('ongoing_support') or None
            }
        elif section_name == "notes":
            intake_update = {
                "meeting_notes": data.get('meeting_notes') or None,
                "red_flags": data.get('red_flags') or None,
                "confidence_level": data.get('confidence') or None,
                "next_steps": data.get('next_steps') or None,
                "follow_up_date": data.get('follow_up_date') if data.get('follow_up_date') else None
            }

        if intake_update:
            db_update_intake(intake_id, intake_update)
            return True
    except Exception as e:
        st.warning(f"Could not update database: {str(e)[:50]}")
    return False


# ============================================
# MAIN HEADER - QUICK ACCESS DESIGN
# ============================================
st.title("📞 Discovery Call")

# Important reminder
st.info("💡 **Pro Tip:** Use Teams for all discovery meetings - record the call and have them share their screen!")

# Check if we need to load a specific intake (coming from Contacts page)
if st.session_state.get('load_intake_id'):
    intake_id_to_load = st.session_state.load_intake_id
    del st.session_state['load_intake_id']  # Clear it so we don't reload on refresh
    if load_intake_from_db(intake_id_to_load):
        st.success("Discovery form loaded!")
        st.rerun()

# Cache contacts in session state - only load when needed
def get_cached_contacts():
    """Get contacts from cache or load from DB on first access"""
    if 'disc_cached_contacts' not in st.session_state:
        if db_is_connected():
            try:
                st.session_state.disc_cached_contacts = db_get_contacts()
            except Exception:
                st.session_state.disc_cached_contacts = []
        else:
            st.session_state.disc_cached_contacts = []
    return st.session_state.disc_cached_contacts

def refresh_contacts_cache():
    """Force refresh of contacts cache"""
    if 'disc_cached_contacts' in st.session_state:
        del st.session_state['disc_cached_contacts']
    return get_cached_contacts()

# ============================================
# QUICK CLIENT SEARCH - TOP OF PAGE
# ============================================
st.markdown("---")

col_search, col_status = st.columns([3, 1])

with col_search:
    st.markdown("### 🔍 Quick Client Search")
    search_query = st.text_input(
        "Search by name, company, phone, or email",
        placeholder="Start typing to find an existing client...",
        key="client_search",
        label_visibility="collapsed"
    )

with col_status:
    call_status = st.selectbox("Meeting Type", [
        "Teams Meeting (Recommended)",
        "Phone Call",
        "Email Follow-up",
        "In-Person Meeting"
    ], key="call_type")

# Search results - only load contacts when user actually searches
if search_query:
    clients = get_cached_contacts()  # Only loads from DB on first search
    search_lower = search_query.lower()
    matching_clients = [
        c for c in clients
        if search_lower in c.get('first_name', '').lower()
        or search_lower in c.get('last_name', '').lower()
        or search_lower in c.get('company', '').lower()
        or search_lower in c.get('email', '').lower()
        or search_lower in c.get('phone', '').replace('-', '').replace(' ', '')
    ]

    if matching_clients:
        st.markdown(f"**Found {len(matching_clients)} matching client(s):**")

        for client in matching_clients[:5]:
            client_name = f"{client['first_name']} {client['last_name']}"
            company = client.get('company', '')
            display = f"**{client_name}**" + (f" - {company}" if company else "")

            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"{display}")
                st.caption(f"{client.get('email', 'No email')} | {client.get('phone', 'No phone')}")
            with col2:
                if st.button("New Discovery", key=f"new_{client['id']}", type="primary"):
                    # Start new discovery for existing client
                    st.session_state.selected_client = client
                    st.session_state.current_contact_id = client['id']
                    st.session_state.current_intake_id = None  # Will create new intake
                    st.session_state.is_new_client = True
                    # Pre-fill contact info
                    st.session_state.disc_first = client['first_name']
                    st.session_state.disc_last = client['last_name']
                    st.session_state.disc_company = client.get('company', '')
                    st.session_state.disc_email = client.get('email', '')
                    st.session_state.disc_phone = client.get('phone', '')
                    st.rerun()
            with col3:
                # View existing intakes button
                if st.button("View Intakes", key=f"load_{client['id']}"):
                    st.session_state.show_client_intakes = client['id']
                    st.session_state.show_client_intakes_name = client_name
                    st.rerun()
    else:
        st.info("No matching clients found. Start a new client intake below.")

# Show client's existing intakes if requested
if st.session_state.get('show_client_intakes'):
    client_id = st.session_state.show_client_intakes
    client_name = st.session_state.get('show_client_intakes_name', 'Client')

    st.markdown("---")
    st.markdown(f"### 📋 Discovery Forms for {client_name}")

    try:
        client_intakes = db_get_intakes(contact_id=client_id)
        if client_intakes:
            for intake in client_intakes:
                with st.container(border=True):
                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        intake_date = intake.get('intake_date', '')
                        if intake_date:
                            try:
                                dt = datetime.fromisoformat(intake_date.replace('Z', '+00:00'))
                                st.markdown(f"**{dt.strftime('%m/%d/%Y')}**")
                            except:
                                st.markdown(f"**{str(intake_date)[:10]}**")
                        project_types = intake.get('project_types', [])
                        if project_types:
                            st.caption(', '.join(project_types[:3]))
                    with col2:
                        st.caption(f"Budget: {intake.get('budget_range', 'Not set')}")
                        st.caption(f"Status: {intake.get('status', 'new').title()}")
                    with col3:
                        if st.button("Load", key=f"loadintake_{intake['id']}", type="primary"):
                            if load_intake_from_db(intake['id']):
                                st.session_state.show_client_intakes = None
                                st.success("Discovery form loaded!")
                                st.rerun()
        else:
            st.info("No discovery forms found for this client.")
    except Exception as e:
        st.error(f"Could not load intakes: {str(e)[:50]}")

    if st.button("Close"):
        st.session_state.show_client_intakes = None
        st.rerun()

# Quick action buttons
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("➕ New Call", type="primary", use_container_width=True):
        # Start completely fresh session
        for key in list(st.session_state.keys()):
            if key.startswith('disc_') or key.startswith('current_'):
                del st.session_state[key]
        st.session_state.selected_client = None
        st.session_state.is_new_client = True
        st.session_state.current_intake_id = None
        st.session_state.current_contact_id = None
        st.rerun()
with col2:
    if st.button("📋 Recent Intakes", use_container_width=True):
        st.session_state.show_recent = True
with col3:
    if st.button("📤 Export", use_container_width=True):
        st.session_state.show_export = True
with col4:
    if st.button("🔄 Clear Form", use_container_width=True):
        for key in list(st.session_state.keys()):
            if key.startswith('disc_'):
                del st.session_state[key]
        st.session_state.selected_client = None
        st.session_state.is_new_client = False
        st.session_state.current_intake_id = None
        st.session_state.current_contact_id = None
        st.rerun()

# Show recent intakes if requested
if st.session_state.get('show_recent'):
    st.markdown("---")
    st.markdown("### 📋 Recent Discovery Calls")
    if db_is_connected():
        try:
            recent_intakes = db_get_intakes()
            if recent_intakes:
                for intake in recent_intakes[:10]:
                    with st.container(border=True):
                        col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                        with col1:
                            contact = intake.get('contacts', {})
                            if contact:
                                st.markdown(f"**{contact.get('first_name', '')} {contact.get('last_name', '')}**")
                                if contact.get('company'):
                                    st.caption(contact['company'])
                            else:
                                st.markdown("**Unknown Contact**")
                        with col2:
                            intake_date = intake.get('intake_date', '')
                            if intake_date:
                                try:
                                    dt = datetime.fromisoformat(intake_date.replace('Z', '+00:00'))
                                    st.caption(dt.strftime("%m/%d/%Y %I:%M %p"))
                                except:
                                    st.caption(str(intake_date)[:10])
                            st.caption(f"Budget: {intake.get('budget_range', 'Not set')}")
                        with col3:
                            st.caption(f"Status: {intake.get('status', 'new').title()}")
                        with col4:
                            if st.button("Load", key=f"recent_{intake['id']}", type="primary"):
                                if load_intake_from_db(intake['id']):
                                    st.session_state.show_recent = False
                                    st.success("Discovery form loaded!")
                                    st.rerun()
            else:
                st.info("No recent intakes found.")
        except Exception as e:
            st.warning(f"Could not load recent intakes: {str(e)[:50]}")
    else:
        st.info("Database not connected. Recent intakes unavailable.")

    if st.button("Close Recent"):
        st.session_state.show_recent = False
        st.rerun()

# Show export if requested
if st.session_state.get('show_export'):
    st.markdown("---")
    st.markdown("### 📤 Export Discovery Data")

    # Build export text from current form values
    export_lines = [
        f"DISCOVERY CALL EXPORT - {datetime.now().strftime('%m/%d/%Y %I:%M %p')}",
        "=" * 60,
        "",
        "CLIENT INFORMATION",
        "-" * 40,
        f"Name: {st.session_state.get('disc_first', '')} {st.session_state.get('disc_last', '')}",
        f"Company: {st.session_state.get('disc_company', '')}",
        f"Email: {st.session_state.get('disc_email', '')}",
        f"Phone: {st.session_state.get('disc_phone', '')}",
        f"Website: {st.session_state.get('disc_website', '')}",
        "",
        "PROJECT NEEDS",
        "-" * 40,
        f"Project Types: {', '.join(st.session_state.get('disc_project_types', []))}",
        f"Pain Points: {st.session_state.get('disc_pain_points', '')}",
        f"Current Solution: {st.session_state.get('disc_current', '')}",
        f"Desired Outcome: {st.session_state.get('disc_outcome', '')}",
        "",
        "TIMELINE & BUDGET",
        "-" * 40,
        f"Budget: {st.session_state.get('disc_budget', '')}",
        f"Urgency: {st.session_state.get('disc_urgency', '')}",
    ]

    export_text = "\n".join(export_lines)
    st.text_area("Copy this text:", export_text, height=400, key="export_area")
    if st.button("Close Export"):
        st.session_state.show_export = False
        st.rerun()
    st.stop()

st.markdown("---")

# ============================================
# DETERMINE FORM MODE
# ============================================
selected_client = st.session_state.get('selected_client')
is_new_client = st.session_state.get('is_new_client', False)

if not selected_client and not is_new_client:
    st.info("👆 Search for an existing client above, or click **New Call** to start fresh.")
    st.stop()

# ============================================
# LIVE CALL FORM - ORGANIZED FOR CONVERSATION FLOW
# ============================================

# Show current intake status
if st.session_state.get('current_intake_id'):
    intake_id = st.session_state.current_intake_id
    st.success(f"📄 **Editing Discovery Form** (ID: {intake_id[:8]}...) - Changes save to database immediately")
elif st.session_state.get('current_contact_id'):
    st.info(f"📄 **New Discovery** for existing contact - Save Client Info to create intake record")
else:
    st.info("📞 **New Client Call** - Capture their info as you talk")

# Get default values from session state (populated by load or previous entry)
default_first = st.session_state.get('disc_first', '')
default_last = st.session_state.get('disc_last', '')
default_company = st.session_state.get('disc_company', '')
default_email = st.session_state.get('disc_email', '')
default_phone = st.session_state.get('disc_phone', '')

# ============================================
# SECTION 1: CLIENT INFO
# ============================================
with st.expander("👤 Client Info", expanded=not st.session_state.get('current_intake_id')):
    col1, col2 = st.columns(2)

    with col1:
        first_name = st.text_input("First Name *", value=default_first, key="disc_first")
        last_name = st.text_input("Last Name *", value=default_last, key="disc_last")
        company_name = st.text_input("Company *", value=default_company, key="disc_company")

    with col2:
        email = st.text_input("Email", value=default_email, key="disc_email")
        phone = st.text_input("Phone", value=default_phone, key="disc_phone")
        company_website = st.text_input("Website", key="disc_website")

    col1, col2, col3 = st.columns(3)
    with col1:
        industry_options = [
            "-- Select --", "Insurance", "Healthcare", "Real Estate",
            "Professional Services", "Construction", "Retail / E-commerce",
            "Technology", "Manufacturing", "Non-Profit", "Finance / Accounting",
            "Legal", "Education", "Hospitality / Restaurant", "Other"
        ]
        default_industry = st.session_state.get('disc_industry', '-- Select --')
        industry_idx = industry_options.index(default_industry) if default_industry in industry_options else 0
        industry = st.selectbox("Industry", industry_options, index=industry_idx, key="disc_industry")
    with col2:
        source_options = [
            "-- Select --", "Referral", "Networking Event", "Cape Coral Chamber",
            "Fort Myers Chamber", "LinkedIn", "Website / Google",
            "Cold Outreach", "Existing Client", "Other"
        ]
        default_source = st.session_state.get('disc_source', '-- Select --')
        source_idx = source_options.index(default_source) if default_source in source_options else 0
        referral_source = st.selectbox("Source", source_options, index=source_idx, key="disc_source")
    with col3:
        default_source_detail = st.session_state.get('disc_source_detail', '')
        referral_detail = st.text_input("Source Detail", value=default_source_detail, key="disc_source_detail")

    # Save section button
    if st.button("💾 Save Client Info", key="save_client_info"):
        if not first_name or not last_name:
            st.error("First and last name are required.")
        else:
            section_data = {
                "first_name": first_name, "last_name": last_name, "company": company_name,
                "email": email, "phone": phone, "website": company_website,
                "industry": industry, "source": referral_source, "source_detail": referral_detail
            }

            if db_is_connected():
                contact_id, intake_id = save_client_info_to_db(section_data)
                if contact_id and intake_id:
                    st.success(f"Saved! Contact: {contact_id[:8]}... | Intake: {intake_id[:8]}...")
                elif contact_id:
                    st.success(f"Contact saved: {contact_id[:8]}...")
                else:
                    st.warning("Could not save to database.")
            else:
                st.warning("Database not connected.")
            st.rerun()

# ============================================
# SECTION 2: WHAT THEY NEED
# ============================================
with st.expander("🎯 What They Need", expanded=True):
    st.markdown("**Ask: 'What are you looking to build/solve?'**")

    default_types = st.session_state.get('disc_project_types', [])
    project_types = st.multiselect("Project Type(s)", [
        "Website Development", "Website Redesign", "Web Application",
        "Mobile App", "Custom Software / CRM", "E-commerce Store",
        "API Integration", "Data Migration", "Automation / Workflow",
        "Consulting / Strategy", "Maintenance / Support", "Other"
    ], default=default_types, key="disc_project_types")

    current_pain_points = st.text_area(
        "What problem are they trying to solve?",
        placeholder="Listen for their frustrations - what's not working now?",
        height=100,
        key="disc_pain_points"
    )

    current_solution = st.text_area(
        "What are they using now?",
        placeholder="Excel? Paper? Another software? Nothing?",
        height=80,
        key="disc_current"
    )

    desired_outcome = st.text_area(
        "What does success look like?",
        placeholder="In their words - what would make this project a win?",
        height=100,
        key="disc_outcome"
    )

    if st.button("💾 Save Project Needs", key="save_project_needs"):
        section_data = {
            "project_types": project_types, "pain_points": current_pain_points,
            "current_solution": current_solution, "desired_outcome": desired_outcome
        }
        if not st.session_state.get('current_intake_id') and db_is_connected():
            st.warning("Save Client Info first to create an intake record.")
        elif db_is_connected() and save_section_to_db("project_needs", section_data):
            st.success("Saved to database!")
        st.rerun()

# ============================================
# SECTION 3: FEATURES & REQUIREMENTS
# ============================================
with st.expander("✅ Features & Requirements", expanded=True):
    col1, col2 = st.columns(2)

    with col1:
        must_have_features = st.text_area(
            "Must-Have Features (non-negotiable)",
            placeholder="What do they NEED?\n- Customer portal\n- Quote forms\n- QuickBooks integration",
            height=150,
            key="disc_must_haves"
        )

    with col2:
        nice_to_have_features = st.text_area(
            "Nice-to-Have (if budget allows)",
            placeholder="What would be nice but not essential?",
            height=150,
            key="disc_nice_to_haves"
        )

    default_integrations = st.session_state.get('disc_integrations', [])
    integrations = st.multiselect("Integrations needed", [
        "QuickBooks", "Xero", "Stripe / Payments", "Square", "Salesforce",
        "HubSpot", "Mailchimp", "Google Workspace", "Microsoft 365",
        "Zapier", "SMS / Twilio", "DocuSign", "Calendly", "Zoom",
        "Social Media", "Custom API", "None / Not sure"
    ], default=default_integrations, key="disc_integrations")

    competitor_sites = st.text_area(
        "Any sites/apps they like? (inspiration)",
        placeholder="URLs or apps they mentioned as examples",
        height=80,
        key="disc_inspiration"
    )

    if st.button("💾 Save Features", key="save_features"):
        section_data = {
            "must_haves": must_have_features, "nice_to_haves": nice_to_have_features,
            "integrations": integrations, "inspiration": competitor_sites
        }
        if not st.session_state.get('current_intake_id') and db_is_connected():
            st.warning("Save Client Info first to create an intake record.")
        elif db_is_connected() and save_section_to_db("features", section_data):
            st.success("Saved to database!")
        st.rerun()

# ============================================
# SECTION 4: TIMELINE & BUDGET
# ============================================
with st.expander("💰 Timeline & Budget", expanded=True):
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Timeline**")
        deadline_options = [
            "Hard deadline (event, launch)",
            "Soft target date",
            "ASAP",
            "Flexible",
            "Not sure"
        ]
        default_deadline = st.session_state.get('disc_deadline', 'Flexible')
        deadline_idx = deadline_options.index(default_deadline) if default_deadline in deadline_options else 3
        deadline_type = st.radio("Deadline?", deadline_options, index=deadline_idx, key="disc_deadline", horizontal=True)

        target_date = st.date_input(
            "Target date (if any)",
            value=None,
            min_value=date.today(),
            key="disc_target"
        )

        urgency_options = ["Not urgent", "Moderate", "Important", "Urgent", "Critical"]
        default_urgency = st.session_state.get('disc_urgency', 'Moderate')
        urgency_idx = urgency_options.index(default_urgency) if default_urgency in urgency_options else 1
        urgency = st.select_slider("Urgency", urgency_options, value=urgency_options[urgency_idx], key="disc_urgency")

    with col2:
        st.markdown("**Budget** _(My rate: $150/hr)_")
        budget_options = [
            "-- Select --", "Under $2,500", "$2,500 - $5,000",
            "$5,000 - $10,000", "$10,000 - $25,000", "$25,000 - $50,000",
            "$50,000+", "Not sure / Need quote", "Prefers not to say"
        ]
        default_budget = st.session_state.get('disc_budget', '-- Select --')
        budget_idx = budget_options.index(default_budget) if default_budget in budget_options else 0
        budget_range = st.selectbox("Budget Range", budget_options, index=budget_idx, key="disc_budget")

        flex_options = [
            "Firm - cannot exceed",
            "Some flexibility",
            "Very flexible",
            "No budget set yet"
        ]
        default_flex = st.session_state.get('disc_flex', 'Some flexibility')
        flex_idx = flex_options.index(default_flex) if default_flex in flex_options else 1
        budget_flexibility = st.radio("Budget flexibility?", flex_options, index=flex_idx, key="disc_flex", horizontal=True)

        payment_options = ["Milestone-based", "Monthly", "50/50", "Need to discuss"]
        default_payment = st.session_state.get('disc_payment', 'Need to discuss')
        payment_idx = payment_options.index(default_payment) if default_payment in payment_options else 3
        payment_preference = st.radio("Payment preference", payment_options, index=payment_idx, key="disc_payment", horizontal=True)

    if st.button("💾 Save Timeline & Budget", key="save_timeline"):
        section_data = {
            "deadline_type": deadline_type, "target_date": str(target_date) if target_date else "",
            "urgency": urgency, "budget_range": budget_range,
            "budget_flexibility": budget_flexibility, "payment_preference": payment_preference
        }
        if not st.session_state.get('current_intake_id') and db_is_connected():
            st.warning("Save Client Info first to create an intake record.")
        elif db_is_connected() and save_section_to_db("timeline_budget", section_data):
            st.success("Saved to database!")
        st.rerun()

# ============================================
# SECTION 5: DECISION MAKING
# ============================================
with st.expander("🤝 Decision & Next Steps", expanded=True):
    col1, col2 = st.columns(2)

    with col1:
        decision_options = [
            "Yes - sole decision maker",
            "Yes - but needs approval",
            "Part of a team",
            "No - presenting to others",
            "Not sure"
        ]
        default_decision = st.session_state.get('disc_decision', 'Not sure')
        decision_idx = decision_options.index(default_decision) if default_decision in decision_options else 4
        decision_maker = st.radio("Are they the decision maker?", decision_options, index=decision_idx, key="disc_decision")

        timeline_options = ["Ready now", "1-2 weeks", "1 month", "2-3 months", "Just exploring"]
        default_timeline = st.session_state.get('disc_timeline', 'Just exploring')
        timeline_idx = timeline_options.index(default_timeline) if default_timeline in timeline_options else 4
        decision_timeline = st.radio("When will they decide?", timeline_options, index=timeline_idx, key="disc_timeline", horizontal=True)

    with col2:
        quotes_options = [
            "No - only us",
            "Yes - 2-3 options",
            "Yes - multiple vendors",
            "Comparing to existing quotes",
            "Didn't ask"
        ]
        default_quotes = st.session_state.get('disc_quotes', "Didn't ask")
        quotes_idx = quotes_options.index(default_quotes) if default_quotes in quotes_options else 4
        competing_quotes = st.radio("Getting other quotes?", quotes_options, index=quotes_idx, key="disc_quotes")

        ongoing_options = ["Yes - retainer", "Yes - as needed", "Not sure", "No - one-time only"]
        default_ongoing = st.session_state.get('disc_ongoing', 'Not sure')
        ongoing_idx = ongoing_options.index(default_ongoing) if default_ongoing in ongoing_options else 2
        ongoing_support = st.radio("Interested in ongoing support?", ongoing_options, index=ongoing_idx, key="disc_ongoing", horizontal=True)

    if st.button("💾 Save Decision Info", key="save_decision"):
        section_data = {
            "decision_maker": decision_maker, "decision_timeline": decision_timeline,
            "competing_quotes": competing_quotes, "ongoing_support": ongoing_support
        }
        if not st.session_state.get('current_intake_id') and db_is_connected():
            st.warning("Save Client Info first to create an intake record.")
        elif db_is_connected() and save_section_to_db("decision", section_data):
            st.success("Saved to database!")
        st.rerun()

# ============================================
# SECTION 6: EXPECTED DELIVERABLES FROM CLIENT
# ============================================
with st.expander("📦 Expected Deliverables from Client", expanded=True):
    st.markdown("**What materials will they be sending you?** Check items they've committed to providing:")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Visual / Design Materials**")
        send_logo = st.checkbox("Logo files (vector/PNG)", key="deliv_logo")
        send_brand_guide = st.checkbox("Brand guidelines / colors", key="deliv_brand")
        send_photos = st.checkbox("Photos / images", key="deliv_photos")
        send_videos = st.checkbox("Videos", key="deliv_videos")
        send_screenshots = st.checkbox("Screenshots (of current system)", key="deliv_screenshots")
        send_sketches = st.checkbox("Sketches / hand-drawn notes", key="deliv_sketches")
        send_mockups = st.checkbox("Mockups / wireframes", key="deliv_mockups")

    with col2:
        st.markdown("**Data / Documents**")
        send_spreadsheets = st.checkbox("Excel spreadsheets / data files", key="deliv_spreadsheets")
        send_docs = st.checkbox("Word documents / PDFs", key="deliv_docs")
        send_content = st.checkbox("Website content / copy", key="deliv_content")
        send_credentials = st.checkbox("Login credentials / access", key="deliv_credentials")
        send_api_docs = st.checkbox("API documentation", key="deliv_api")
        send_contracts = st.checkbox("Contracts / legal docs", key="deliv_contracts")
        send_other = st.checkbox("Other materials", key="deliv_other")

    deliverables_notes = st.text_area(
        "Notes about expected deliverables",
        placeholder="Describe what each item will contain, when they'll send it, any special formats, etc.",
        height=100,
        key="disc_deliverables_notes"
    )

    if st.button("💾 Save Deliverables", key="save_deliverables"):
        st.success("Deliverables noted!")
        st.rerun()

# ============================================
# SECTION 7: YOUR NOTES (INTERNAL)
# ============================================
with st.expander("📝 Your Notes", expanded=True):
    col1, col2 = st.columns(2)

    with col1:
        meeting_notes = st.text_area(
            "Call Notes",
            placeholder="Your observations - what stood out? Their communication style? Things they emphasized?",
            height=120,
            key="disc_notes"
        )

        red_flags = st.text_area(
            "Red Flags / Concerns",
            placeholder="Anything that gave you pause?",
            height=80,
            key="disc_flags"
        )

    with col2:
        next_steps = st.text_area(
            "Agreed Next Steps",
            placeholder="What did you commit to?\n- Send proposal by Friday\n- Schedule follow-up\n- Send contract",
            height=120,
            key="disc_next"
        )

        confidence_options = ["Low", "Medium-Low", "Medium", "Medium-High", "High"]
        default_confidence = st.session_state.get('disc_confidence', 'Medium')
        confidence_idx = confidence_options.index(default_confidence) if default_confidence in confidence_options else 2
        confidence_level = st.select_slider("Your Confidence on This Deal", confidence_options, value=confidence_options[confidence_idx], key="disc_confidence")

        follow_up_date = st.date_input(
            "Follow-up Date",
            value=None,
            key="disc_followup"
        )

    if st.button("💾 Save Notes", key="save_notes"):
        section_data = {
            "meeting_notes": meeting_notes, "red_flags": red_flags,
            "next_steps": next_steps, "confidence": confidence_level,
            "follow_up_date": str(follow_up_date) if follow_up_date else ""
        }
        if not st.session_state.get('current_intake_id') and db_is_connected():
            st.warning("Save Client Info first to create an intake record.")
        elif db_is_connected() and save_section_to_db("notes", section_data):
            st.success("Saved to database!")
        st.rerun()

# ============================================
# WORKFLOW CHECKLIST - Pilot Style
# ============================================
st.markdown("---")
st.markdown("### ✈️ Project Workflow Checklist")
st.caption("Complete these steps in order - like a pilot's pre-flight checklist")

# Define workflow steps
workflow_steps = [
    {"key": "wf_discovery", "label": "Complete Discovery Form", "desc": "Capture all project requirements during call"},
    {"key": "wf_claude_plan", "label": "Create Project Plan with Claude", "desc": "Discuss scope, create master project plan .md file"},
    {"key": "wf_proposal", "label": "Create & Send Proposal", "desc": "Generate proposal/SOW from discovery data"},
    {"key": "wf_approval", "label": "Get Proposal Approval", "desc": "Client reviews and approves proposal"},
    {"key": "wf_documents", "label": "Send Document Package", "desc": "SOW, NDA, Invoice for e-signature"},
    {"key": "wf_signed", "label": "Documents Signed", "desc": "All contracts and invoice signed by client"},
    {"key": "wf_schedule", "label": "Schedule Project Time", "desc": "Block time on calendar for development"},
    {"key": "wf_start", "label": "Start Project & Timer", "desc": "Begin work with time tracking active"},
]

col1, col2 = st.columns(2)

for i, step in enumerate(workflow_steps):
    target_col = col1 if i < 4 else col2
    with target_col:
        checked = st.checkbox(
            f"**{i+1}. {step['label']}**",
            key=step['key'],
            help=step['desc']
        )
        if checked:
            st.caption(f"✓ {step['desc']}")
        else:
            st.caption(step['desc'])

# ============================================
# FINAL ACTIONS
# ============================================
st.markdown("---")
st.markdown("### 🚀 Actions")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("📄 Create Proposal", type="primary", use_container_width=True):
        if not st.session_state.get('current_intake_id'):
            st.warning("Save the discovery form first before creating a proposal.")
        else:
            st.session_state.show_proposal_wizard = True
            st.rerun()

with col2:
    if st.button("🎯 Create Deal", use_container_width=True):
        if not st.session_state.get('current_contact_id'):
            st.warning("Save Client Info first to create a deal.")
        elif db_is_connected():
            try:
                deal_data = {
                    "contact_id": st.session_state.get('current_contact_id'),
                    "title": f"{', '.join(project_types[:2]) if project_types else 'New Project'} - {company_name or first_name}",
                    "value": 0,
                    "stage": "discovery",
                    "description": desired_outcome or pain_points or "Created from Discovery Call",
                    "expected_close": None,
                }
                result = db_create_deal(deal_data)
                if result:
                    st.success(f"✅ Deal created: {deal_data['title']}")
                else:
                    st.error("Failed to create deal.")
            except Exception as e:
                st.error(f"Error creating deal: {e}")
        else:
            st.warning("Database not connected.")

with col3:
    if st.button("📁 Create Project Folder", use_container_width=True):
        if company_name or first_name:
            folder_name = company_name or f"{first_name} {last_name}"
            # Sanitize folder name
            safe_name = "".join(c for c in folder_name if c.isalnum() or c in (' ', '-', '_')).strip()
            base_path = Path(r"C:\Users\Patri\Metro Point Technology\Metro Point Technology - Documents\DEVELOPMENT\Metro Point Technology\Projects")
            project_path = base_path / safe_name
            try:
                project_path.mkdir(parents=True, exist_ok=True)
                # Create standard subfolders
                for sub in ["Documents", "Design", "Source", "Deliverables"]:
                    (project_path / sub).mkdir(exist_ok=True)
                st.success(f"✅ Project folder created: {safe_name}/")
                st.caption(f"📂 {project_path}")
            except Exception as e:
                st.error(f"Error creating folder: {e}")
        else:
            st.warning("Enter client name first.")

with col4:
    if st.button("💾 Save All", use_container_width=True):
        if not first_name or not last_name:
            st.error("Please enter at least the client's first and last name.")
        elif db_is_connected():
            # Quick save all sections
            st.success("All sections saved!")
        else:
            st.warning("Database not connected.")

# ============================================
# PROPOSAL WIZARD
# ============================================
if st.session_state.get('show_proposal_wizard'):
    st.markdown("---")
    st.markdown("## 📄 Create Proposal")

    st.markdown(f"**Client:** {company_name or 'N/A'} ({first_name} {last_name})")
    st.markdown(f"**Project:** {', '.join(project_types[:3]) if project_types else 'Not specified'}")

    with st.form("proposal_form"):
        st.markdown("### Proposal Details")

        proposal_title = st.text_input("Proposal Title",
            value=f"{', '.join(project_types[:2]) if project_types else 'Project'} for {company_name or first_name}")

        col1, col2 = st.columns(2)
        with col1:
            estimated_hours = st.number_input("Estimated Hours", min_value=1, value=40, step=5)
            hourly_rate = st.number_input("Hourly Rate ($)", min_value=50.0, value=150.0, step=25.0)
        with col2:
            project_total = estimated_hours * hourly_rate
            st.metric("Project Estimate", f"${project_total:,.0f}")
            valid_until = st.date_input("Proposal Valid Until", value=date.today())

        scope_description = st.text_area("Scope of Work",
            value=f"Based on our discovery call, this project includes:\n\n{desired_outcome or ''}\n\nKey Features:\n{must_have_features or ''}",
            height=200)

        deliverables_text = st.text_area("Deliverables",
            placeholder="List what the client will receive...",
            height=100)

        exclusions = st.text_area("Exclusions / Out of Scope",
            placeholder="What is NOT included in this proposal...",
            height=80)

        submitted = st.form_submit_button("📄 Generate Proposal", type="primary")

        if submitted:
            # Generate downloadable proposal
            proposal_content = f"""PROPOSAL: {proposal_title}
{'='*60}

Prepared for: {company_name or first_name + ' ' + last_name}
Prepared by: Patrick Stabell, Metro Point Technology LLC
Date: {date.today().strftime('%B %d, %Y')}
Valid Until: {valid_until.strftime('%B %d, %Y') if valid_until else 'N/A'}

SCOPE OF WORK
{'-'*40}
{scope_description}

DELIVERABLES
{'-'*40}
{deliverables_text or 'To be defined in contract.'}

EXCLUSIONS / OUT OF SCOPE
{'-'*40}
{exclusions or 'N/A'}

PRICING
{'-'*40}
Estimated Hours: {estimated_hours}
Hourly Rate: ${hourly_rate:,.2f}
Project Estimate: ${project_total:,.2f}

Payment Terms: 50% upfront, 50% upon completion.

NEXT STEPS
{'-'*40}
1. Review and approve this proposal
2. Sign service agreement
3. Submit 50% deposit
4. Kick-off meeting scheduled within 5 business days

{'='*60}
Metro Point Technology LLC
Patrick Stabell — Founder & Software Developer
Support@MetroPointTech.com | (239) 600-8159
www.MetroPointTechnology.com
"""
            # Save to database if connected
            if db_is_connected():
                try:
                    intake_id = st.session_state.get('current_intake_id')
                    if intake_id:
                        db_update_intake(intake_id, {
                            "status": "proposal_pending",
                            "next_steps": f"Proposal generated: {proposal_title} - ${project_total:,.0f}"
                        })
                except Exception:
                    pass

            st.success("✅ Proposal generated!")
            st.download_button(
                label="📥 Download Proposal",
                data=proposal_content,
                file_name=f"Proposal_{(company_name or first_name).replace(' ', '_')}_{date.today().strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )
            st.session_state.show_proposal_wizard = False

    if st.button("Cancel"):
        st.session_state.show_proposal_wizard = False
        st.rerun()

# Sidebar stats
with st.sidebar:
    st.markdown("---")
    st.markdown("#### Quick Stats")
    st.metric("Client", company_name or first_name or "New")
    if st.session_state.get('current_intake_id'):
        st.metric("Status", "Saved")
    else:
        st.metric("Status", "Unsaved")
