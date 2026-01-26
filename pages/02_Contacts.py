"""
MPT-CRM Contacts Page
Manage contacts with types, tags, and full detail views
SELF-CONTAINED - No imports from services/ or shared/ folders
"""

import streamlit as st
from datetime import datetime
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Try to import supabase
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

st.set_page_config(
    page_title="MPT-CRM - Contacts",
    page_icon="favicon.jpg",
    layout="wide"
)

# ============================================
# DATABASE CONNECTION (self-contained)
# ============================================
@st.cache_resource(show_spinner=False)
def get_db():
    """Create and cache Supabase client"""
    if not SUPABASE_AVAILABLE:
        return None

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")

    if url and key:
        try:
            return create_client(url, key)
        except Exception:
            return None
    return None

def db_is_connected():
    """Check if database is connected"""
    return get_db() is not None

# ============================================
# PAGE-SPECIFIC DATABASE FUNCTIONS
# ============================================
def db_get_contacts(include_archived=False):
    """Get all contacts from database"""
    db = get_db()
    if not db:
        return None

    try:
        query = db.table("contacts").select("*").order("created_at", desc=True)
        if not include_archived:
            query = query.neq("archived", True)
        response = query.execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error getting contacts: {e}")
        return None

def db_get_contact(contact_id):
    """Get a single contact by ID"""
    db = get_db()
    if not db:
        return None

    try:
        response = db.table("contacts").select("*").eq("id", contact_id).single().execute()
        return response.data
    except Exception:
        return None

def db_create_contact(contact_data):
    """Create a new contact"""
    db = get_db()
    if not db:
        return None

    try:
        response = db.table("contacts").insert(contact_data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error creating contact: {e}")
        return None

def db_update_contact(contact_id, contact_data):
    """Update a contact"""
    db = get_db()
    if not db:
        return None

    try:
        response = db.table("contacts").update(contact_data).eq("id", contact_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error updating contact: {e}")
        return None

def db_delete_contact(contact_id):
    """Delete a contact"""
    db = get_db()
    if not db:
        return False

    try:
        db.table("contacts").delete().eq("id", contact_id).execute()
        return True
    except Exception:
        return False

def db_archive_contact(contact_id):
    """Archive a contact (soft delete)"""
    db = get_db()
    if not db:
        return None

    try:
        response = db.table("contacts").update({
            "archived": True,
            "archived_at": datetime.now().isoformat()
        }).eq("id", contact_id).execute()
        return response.data[0] if response.data else None
    except Exception:
        return None

def db_unarchive_contact(contact_id):
    """Restore an archived contact"""
    db = get_db()
    if not db:
        return None

    try:
        response = db.table("contacts").update({
            "archived": False,
            "archived_at": None
        }).eq("id", contact_id).execute()
        return response.data[0] if response.data else None
    except Exception:
        return None

def db_get_archived_contacts():
    """Get archived contacts"""
    db = get_db()
    if not db:
        return []

    try:
        response = db.table("contacts").select("*").eq("archived", True).order("archived_at", desc=True).execute()
        return response.data if response.data else []
    except Exception:
        return []

def db_find_potential_duplicates(contact_id):
    """
    Find potential duplicate contacts for a given contact.
    Matching priority: name -> company -> email
    Returns list of potential matches with match_reason
    """
    db = get_db()
    if not db:
        return []

    # Get the source contact
    try:
        response = db.table("contacts").select("*").eq("id", contact_id).single().execute()
        source = response.data
        if not source:
            return []
    except Exception:
        return []

    potential_duplicates = []
    seen_ids = {contact_id}  # Don't include the source contact

    first_name = (source.get('first_name') or '').strip().lower()
    last_name = (source.get('last_name') or '').strip().lower()
    company = (source.get('company') or '').strip().lower()
    email = (source.get('email') or '').strip().lower()

    try:
        # Get all non-archived contacts
        all_contacts = db.table("contacts").select("*").neq("archived", True).execute()
        contacts = all_contacts.data if all_contacts.data else []

        for c in contacts:
            if c['id'] in seen_ids:
                continue

            c_first = (c.get('first_name') or '').strip().lower()
            c_last = (c.get('last_name') or '').strip().lower()
            c_company = (c.get('company') or '').strip().lower()
            c_email = (c.get('email') or '').strip().lower()

            match_reasons = []

            # Priority 1: Name match (first AND last)
            if first_name and last_name and c_first and c_last:
                if first_name == c_first and last_name == c_last:
                    match_reasons.append("Same name")

            # Priority 2: Company match
            if company and c_company and len(company) > 2:
                if company == c_company:
                    match_reasons.append("Same company")
                elif company in c_company or c_company in company:
                    match_reasons.append("Similar company")

            # Priority 3: Email match
            if email and c_email and '@' in email:
                if email == c_email:
                    match_reasons.append("Same email")

            if match_reasons:
                c['match_reasons'] = match_reasons
                potential_duplicates.append(c)
                seen_ids.add(c['id'])

        # Sort by number of match reasons (more matches = more likely duplicate)
        potential_duplicates.sort(key=lambda x: len(x.get('match_reasons', [])), reverse=True)

        return potential_duplicates
    except Exception as e:
        print(f"Error finding duplicates: {e}")
        return []

def db_merge_contacts(primary_id, secondary_id):
    """
    Merge secondary contact INTO primary contact.
    - Transfers all related records (deals, intakes, activities) to primary
    - Merges notes from both contacts
    - Deletes secondary contact after transfer
    Returns: {"success": True/False, "message": "...", "merged_counts": {...}}
    """
    db = get_db()
    if not db:
        return {"success": False, "message": "Database not connected"}

    try:
        # Get both contacts
        primary = db.table("contacts").select("*").eq("id", primary_id).single().execute().data
        secondary = db.table("contacts").select("*").eq("id", secondary_id).single().execute().data

        if not primary:
            return {"success": False, "message": "Primary contact not found"}
        if not secondary:
            return {"success": False, "message": "Secondary contact not found"}

        merged_counts = {
            "deals": 0,
            "intakes": 0,
            "activities": 0,
            "notes_merged": False
        }

        # 1. Transfer all deals from secondary to primary
        try:
            deals_response = db.table("deals").select("id").eq("contact_id", secondary_id).execute()
            if deals_response.data:
                for deal in deals_response.data:
                    db.table("deals").update({"contact_id": primary_id}).eq("id", deal['id']).execute()
                    merged_counts["deals"] += 1
        except Exception as e:
            print(f"Error transferring deals: {e}")

        # 2. Transfer all intakes (discovery forms) from secondary to primary
        try:
            intakes_response = db.table("client_intakes").select("id").eq("contact_id", secondary_id).execute()
            if intakes_response.data:
                for intake in intakes_response.data:
                    db.table("client_intakes").update({"contact_id": primary_id}).eq("id", intake['id']).execute()
                    merged_counts["intakes"] += 1
        except Exception as e:
            print(f"Error transferring intakes: {e}")

        # 3. Transfer all activities from secondary to primary
        try:
            activities_response = db.table("activities").select("id").eq("contact_id", secondary_id).execute()
            if activities_response.data:
                for activity in activities_response.data:
                    db.table("activities").update({"contact_id": primary_id}).eq("id", activity['id']).execute()
                    merged_counts["activities"] += 1
        except Exception as e:
            print(f"Error transferring activities: {e}")

        # 4. Transfer campaign enrollments from secondary to primary
        try:
            enrollments_response = db.table("campaign_enrollments").select("id").eq("contact_id", secondary_id).execute()
            if enrollments_response.data:
                for enrollment in enrollments_response.data:
                    db.table("campaign_enrollments").update({"contact_id": primary_id}).eq("id", enrollment['id']).execute()
        except Exception:
            pass  # Table might not exist

        # 5. Merge notes - prepend secondary's notes to primary's notes with timestamp
        primary_notes = primary.get('notes') or ''
        secondary_notes = secondary.get('notes') or ''

        if secondary_notes:
            merge_timestamp = datetime.now().strftime("%m/%d/%Y %I:%M %p")
            secondary_name = f"{secondary.get('first_name', '')} {secondary.get('last_name', '')}".strip()
            merge_header = f"**[{merge_timestamp}] Notes merged from: {secondary_name}**"

            if primary_notes:
                merged_notes = f"{merge_header}\n{secondary_notes}\n\n---\n\n{primary_notes}"
            else:
                merged_notes = f"{merge_header}\n{secondary_notes}"

            db.table("contacts").update({"notes": merged_notes}).eq("id", primary_id).execute()
            merged_counts["notes_merged"] = True

        # 6. Fill in any missing fields on primary from secondary
        fields_to_fill = ['phone', 'company', 'source', 'source_detail']
        update_data = {}
        for field in fields_to_fill:
            if not primary.get(field) and secondary.get(field):
                update_data[field] = secondary.get(field)

        # Merge tags
        primary_tags = primary.get('tags') or []
        secondary_tags = secondary.get('tags') or []
        if secondary_tags:
            combined_tags = list(set(primary_tags + secondary_tags))
            update_data['tags'] = combined_tags

        if update_data:
            db.table("contacts").update(update_data).eq("id", primary_id).execute()

        # 7. Log the merge activity
        try:
            secondary_name = f"{secondary.get('first_name', '')} {secondary.get('last_name', '')}".strip()
            db.table("activities").insert({
                "type": "contact_merged",
                "description": f"Merged contact '{secondary_name}' into this contact. Transferred: {merged_counts['deals']} deals, {merged_counts['intakes']} discovery forms, {merged_counts['activities']} activities.",
                "contact_id": primary_id
            }).execute()
        except Exception:
            pass

        # 8. Delete the secondary contact (all data has been transferred)
        db.table("contacts").delete().eq("id", secondary_id).execute()

        return {
            "success": True,
            "message": f"Successfully merged contacts. Transferred: {merged_counts['deals']} deals, {merged_counts['intakes']} discovery forms, {merged_counts['activities']} activities.",
            "merged_counts": merged_counts
        }

    except Exception as e:
        return {"success": False, "message": f"Merge failed: {str(e)}"}

def db_get_intakes(contact_id=None):
    """Get client intakes for a contact"""
    db = get_db()
    if not db:
        return []

    try:
        query = db.table("client_intakes").select("*, contacts(first_name, last_name, company)").order("intake_date", desc=True)
        if contact_id:
            query = query.eq("contact_id", contact_id)
        response = query.execute()
        return response.data if response.data else []
    except Exception:
        return []

def db_log_activity(activity_type, description, contact_id=None):
    """Log an activity"""
    db = get_db()
    if not db:
        return None

    try:
        response = db.table("activities").insert({
            "type": activity_type,
            "description": description,
            "contact_id": contact_id
        }).execute()
        return response.data[0] if response.data else None
    except Exception:
        return None

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

def render_sidebar(current_page="Contacts"):
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

# ============================================
# SAMPLE CONTACTS (for demo when no database)
# ============================================
SAMPLE_CONTACTS = [
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
        "notes": "Met at Monarca's Mexican restaurant networking event.",
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
]

# ============================================
# PAGE-SPECIFIC HELPER FUNCTIONS
# ============================================
def load_contacts():
    """Load contacts from database or return sample data"""
    if db_is_connected():
        try:
            contacts = db_get_contacts()
            if contacts is not None and len(contacts) > 0:
                return contacts
            elif contacts is not None and len(contacts) == 0:
                return []
            else:
                return SAMPLE_CONTACTS
        except Exception as e:
            st.warning(f"Could not load from database: {str(e)[:50]}...")
            return SAMPLE_CONTACTS
    return SAMPLE_CONTACTS

def save_contact(contact_id, contact_data):
    """Save contact updates to database"""
    if db_is_connected() and not contact_id.startswith("c-") and not contact_id.startswith("local-"):
        try:
            db_update_contact(contact_id, contact_data)
            return True
        except Exception as e:
            st.error(f"Failed to save: {str(e)[:50]}")
    return False

def create_contact(contact_data):
    """Create a new contact in the database"""
    if db_is_connected():
        try:
            return db_create_contact(contact_data)
        except Exception as e:
            st.error(f"Database error: {str(e)[:50]}")
    return None

def delete_contact(contact_id):
    """Delete a contact from the database"""
    if db_is_connected() and not contact_id.startswith("c-") and not contact_id.startswith("local-"):
        try:
            return db_delete_contact(contact_id)
        except Exception as e:
            st.error(f"Failed to delete: {str(e)[:50]}")
    return False

def archive_contact(contact_id):
    """Archive a contact (soft delete)"""
    if db_is_connected() and not contact_id.startswith("c-") and not contact_id.startswith("local-"):
        try:
            result = db_archive_contact(contact_id)
            if result:
                db_log_activity("contact_archived", "Contact archived", contact_id=contact_id)
            return result
        except Exception as e:
            st.error(f"Failed to archive: {str(e)[:50]}")
    return None

def unarchive_contact(contact_id):
    """Restore an archived contact"""
    if db_is_connected() and not contact_id.startswith("c-") and not contact_id.startswith("local-"):
        try:
            result = db_unarchive_contact(contact_id)
            if result:
                db_log_activity("contact_restored", "Contact restored from archive", contact_id=contact_id)
            return result
        except Exception as e:
            st.error(f"Failed to restore: {str(e)[:50]}")
    return None

def load_archived_contacts():
    """Load archived contacts from database"""
    if db_is_connected():
        try:
            return db_get_archived_contacts()
        except Exception as e:
            st.warning(f"Could not load archived contacts: {str(e)[:50]}...")
    return []

# ============================================
# SESSION STATE INITIALIZATION
# ============================================
if 'contacts_list' not in st.session_state or st.session_state.get('contacts_need_refresh', True):
    loaded = load_contacts()
    if db_is_connected() and loaded == SAMPLE_CONTACTS:
        loaded = load_contacts()
    st.session_state.contacts_list = loaded
    st.session_state.contacts_need_refresh = False

# Use contacts_list to avoid conflicts with other pages
if 'contacts' not in st.session_state:
    st.session_state.contacts = st.session_state.contacts_list
else:
    st.session_state.contacts = st.session_state.contacts_list

if 'contacts_selected' not in st.session_state:
    st.session_state.contacts_selected = None

# Sync with old key for compatibility
if 'selected_contact' in st.session_state and st.session_state.selected_contact:
    st.session_state.contacts_selected = st.session_state.selected_contact

# ============================================
# CONTACT TYPE AND TAG DEFINITIONS
# ============================================
CONTACT_TYPES = {
    "lead": {"label": "Lead", "icon": "🔥", "color": "#fd7e14"},
    "prospect": {"label": "Prospect", "icon": "🎯", "color": "#17a2b8"},
    "client": {"label": "Client", "icon": "⭐", "color": "#28a745"},
    "former_client": {"label": "Former Client", "icon": "📦", "color": "#6f42c1"},
    "partner": {"label": "Partner", "icon": "🤝", "color": "#20c997"},
    "vendor": {"label": "Vendor", "icon": "🏢", "color": "#adb5bd"},
    "networking": {"label": "Networking", "icon": "🤝", "color": "#6c757d"},
}

SOURCE_TAGS = ["Cape Coral Chamber", "Fort Myers Chamber", "LinkedIn", "Referral", "Website Inquiry", "Cold Outreach", "Conference"]
INDUSTRY_TAGS = ["Insurance", "Healthcare", "Retail", "Professional Services", "Construction", "Real Estate", "Technology"]
INTEREST_TAGS = ["Custom Software", "Website Development", "Mobile App", "SaaS Product", "Integration", "Automation", "CRM"]
STATUS_TAGS = ["Hot Lead", "Warm", "Cold", "Nurture", "Do Not Contact", "VIP"]

ALL_TAGS = SOURCE_TAGS + INDUSTRY_TAGS + INTEREST_TAGS + STATUS_TAGS

# ============================================
# MERGE INTERFACE
# ============================================
def show_merge_interface(primary_contact):
    """Show interface for merging duplicate contacts"""
    st.markdown("---")

    with st.container(border=True):
        st.markdown("#### 🔗 Merge Duplicate Contacts")

        primary_name = f"{primary_contact.get('first_name', '')} {primary_contact.get('last_name', '')}".strip()
        st.info(f"**Primary Contact (will KEEP):** {primary_name}")
        st.caption("The contact below will be absorbed into this one. All their notes, deals, discovery forms, and activities will be transferred.")

        # Find potential duplicates
        duplicates = db_find_potential_duplicates(primary_contact['id'])

        if not duplicates:
            st.warning("No potential duplicates found based on name, company, or email.")
            if st.button("Close", key="close_merge_no_dups"):
                st.session_state.contacts_show_merge = False
                st.rerun()
        else:
            st.markdown(f"**Found {len(duplicates)} potential duplicate(s):**")

            for dup in duplicates:
                dup_name = f"{dup.get('first_name', '')} {dup.get('last_name', '')}".strip()
                dup_company = dup.get('company', 'No company')
                dup_email = dup.get('email', 'No email')
                match_reasons = dup.get('match_reasons', [])

                with st.container(border=True):
                    col_info, col_action = st.columns([3, 1])

                    with col_info:
                        st.markdown(f"**{dup_name}**")
                        st.caption(f"🏢 {dup_company} | 📧 {dup_email}")
                        st.markdown(f"Match: {', '.join(match_reasons)}")

                    with col_action:
                        if st.button("Merge Into Primary", key=f"merge_{dup['id']}", type="primary"):
                            st.session_state[f"confirm_merge_{dup['id']}"] = True
                            st.rerun()

                # Confirmation dialog
                if st.session_state.get(f"confirm_merge_{dup['id']}"):
                    st.warning(f"⚠️ **Confirm Merge**")
                    st.markdown(f"""
                    **This will:**
                    - Transfer all deals, discovery forms, and activities from **{dup_name}** to **{primary_name}**
                    - Merge notes from both contacts
                    - Fill in any missing info on {primary_name} from {dup_name}
                    - **DELETE** the contact **{dup_name}** permanently

                    **{dup_name} will disappear. {primary_name} will remain with all merged data.**
                    """)

                    col_yes, col_no = st.columns(2)
                    with col_yes:
                        if st.button(f"Yes, Merge {dup_name} → {primary_name}", key=f"confirm_yes_{dup['id']}", type="primary"):
                            result = db_merge_contacts(primary_contact['id'], dup['id'])
                            if result['success']:
                                st.success(result['message'])
                                st.session_state.contacts_need_refresh = True
                                st.session_state.contacts_show_merge = False
                                st.session_state[f"confirm_merge_{dup['id']}"] = False
                                st.rerun()
                            else:
                                st.error(result['message'])

                    with col_no:
                        if st.button("Cancel", key=f"confirm_no_{dup['id']}"):
                            st.session_state[f"confirm_merge_{dup['id']}"] = False
                            st.rerun()

            st.markdown("---")

            # Option to manually select any contact to merge
            st.markdown("**Or select any contact to merge:**")

            # Get all contacts except the primary
            all_contacts = st.session_state.contacts
            other_contacts = [c for c in all_contacts if c['id'] != primary_contact['id']]

            if other_contacts:
                contact_options = ["Select a contact..."] + [
                    f"{c.get('first_name', '')} {c.get('last_name', '')} ({c.get('company', 'No company')})"
                    for c in other_contacts
                ]

                selected_option = st.selectbox(
                    "Contact to merge into primary:",
                    contact_options,
                    key="manual_merge_select"
                )

                if selected_option != "Select a contact...":
                    selected_idx = contact_options.index(selected_option) - 1
                    selected_contact = other_contacts[selected_idx]
                    selected_name = f"{selected_contact.get('first_name', '')} {selected_contact.get('last_name', '')}".strip()

                    if st.button(f"Merge {selected_name} → {primary_name}", key="manual_merge_btn", type="primary"):
                        st.session_state.manual_merge_confirm = selected_contact['id']
                        st.rerun()

                # Manual merge confirmation
                if st.session_state.get('manual_merge_confirm'):
                    manual_id = st.session_state.manual_merge_confirm
                    manual_contact = next((c for c in other_contacts if c['id'] == manual_id), None)
                    if manual_contact:
                        manual_name = f"{manual_contact.get('first_name', '')} {manual_contact.get('last_name', '')}".strip()
                        st.warning(f"⚠️ **Confirm:** Merge **{manual_name}** into **{primary_name}**?")
                        st.caption(f"**{manual_name}** will be deleted. All data will be transferred to **{primary_name}**.")

                        col_yes, col_no = st.columns(2)
                        with col_yes:
                            if st.button("Yes, Merge", key="manual_confirm_yes", type="primary"):
                                result = db_merge_contacts(primary_contact['id'], manual_id)
                                if result['success']:
                                    st.success(result['message'])
                                    st.session_state.contacts_need_refresh = True
                                    st.session_state.contacts_show_merge = False
                                    st.session_state.manual_merge_confirm = None
                                    st.rerun()
                                else:
                                    st.error(result['message'])
                        with col_no:
                            if st.button("Cancel", key="manual_confirm_no"):
                                st.session_state.manual_merge_confirm = None
                                st.rerun()

            if st.button("Close Merge Panel", key="close_merge"):
                st.session_state.contacts_show_merge = False
                st.session_state.manual_merge_confirm = None
                st.rerun()

# ============================================
# CONTACT DETAIL VIEW
# ============================================
def show_contact_detail(contact_id):
    """Display full contact detail view"""
    contact = next((c for c in st.session_state.contacts if c['id'] == contact_id), None)
    if not contact:
        st.session_state.contacts_selected = None
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
            st.session_state.contacts_selected = None
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

        # Save button for contact info
        if st.button("💾 Save Contact Info", type="primary", key="save_contact_info"):
            # Get source_detail from session state (will be set in col2)
            new_source_detail = st.session_state.get('edit_source_detail', contact.get('source_detail', ''))
            update_data = {
                "first_name": new_first,
                "last_name": new_last,
                "email": new_email,
                "phone": new_phone,
                "company": new_company,
                "source_detail": new_source_detail
            }
            contact.update(update_data)
            if save_contact(contact['id'], update_data):
                st.success("Contact saved!")
            elif not db_is_connected():
                st.info("Changes saved locally (connect database to persist)")

        # Activity Timeline
        st.markdown("### 📅 Recent Activity")
        with st.container(border=True):
            st.caption(f"📧 Email sent - {contact.get('last_contacted', 'N/A')}")
            st.caption(f"📝 Contact created - {contact.get('created_at', 'N/A')}")
            st.caption("_More activity tracking coming soon..._")

        # Deals section
        st.markdown("### 🎯 Deals")
        contact_deals = []
        # Check session state for deals linked to this contact
        if 'pipeline_deals' in st.session_state:
            contact_deals = [d for d in st.session_state.pipeline_deals if d.get('contact_id') == contact['id']]

        if contact_deals:
            for deal in contact_deals:
                with st.container(border=True):
                    col_info, col_action = st.columns([4, 1])
                    with col_info:
                        deal_title = deal.get('title', 'Untitled Deal')
                        st.markdown(f"**{deal_title}**")

                        deal_value = deal.get('value', 0) or 0
                        deal_stage = deal.get('stage', 'lead').replace('_', ' ').title()
                        value_str = f"${deal_value:,.0f}" if deal_value else "No value"
                        st.caption(f"💰 {value_str} | Stage: {deal_stage}")

                    with col_action:
                        if st.button("Open", key=f"deal_{deal['id']}", type="primary"):
                            st.session_state.pipeline_selected_deal = deal['id']
                            st.switch_page("pages/03_Pipeline.py")
        else:
            st.caption("_No deals yet_")
            if st.button("➕ Create Deal", key="create_deal_from_contact_section"):
                st.session_state.new_deal_contact_id = contact['id']
                st.session_state.new_deal_contact_name = f"{contact['first_name']} {contact['last_name']}"
                st.session_state.new_deal_company_name = contact.get('company', '')
                st.session_state.pipeline_show_new_deal = True
                st.switch_page("pages/03_Pipeline.py")

        # Discovery Forms section
        st.markdown("### 📞 Discovery Forms")
        if db_is_connected():
            try:
                contact_intakes = db_get_intakes(contact_id=contact['id'])
                if contact_intakes:
                    for intake in contact_intakes:
                        with st.container(border=True):
                            col_info, col_action = st.columns([4, 1])
                            with col_info:
                                project_types = intake.get('project_types', [])
                                if project_types:
                                    label = ', '.join(project_types[:3])
                                    if len(project_types) > 3:
                                        label += f" +{len(project_types) - 3}"
                                else:
                                    label = "No project type specified"
                                st.markdown(f"**{label}**")

                                intake_date = intake.get('intake_date', '')
                                if intake_date:
                                    try:
                                        dt = datetime.fromisoformat(str(intake_date).replace('Z', '+00:00'))
                                        date_str = dt.strftime('%m/%d/%Y')
                                    except:
                                        date_str = str(intake_date)[:10]
                                else:
                                    date_str = 'N/A'

                                status = intake.get('status', 'new').title()
                                budget = intake.get('budget_range', 'Not set')
                                st.caption(f"📅 {date_str} | Status: {status} | Budget: {budget}")

                            with col_action:
                                if st.button("Open", key=f"intake_{intake['id']}", type="primary"):
                                    st.session_state.load_intake_id = intake['id']
                                    st.switch_page("pages/01_Discovery.py")
                else:
                    st.caption("_No discovery forms yet_")
                    if st.button("➕ Start Discovery", key="start_discovery_from_contact"):
                        st.session_state.current_contact_id = contact['id']
                        st.session_state.current_intake_id = None
                        st.session_state.is_new_client = True
                        st.session_state.disc_first = contact['first_name']
                        st.session_state.disc_last = contact['last_name']
                        st.session_state.disc_company = contact.get('company', '')
                        st.session_state.disc_email = contact.get('email', '')
                        st.session_state.disc_phone = contact.get('phone', '')
                        st.switch_page("pages/01_Discovery.py")
            except Exception as e:
                st.caption(f"_Could not load discovery forms: {str(e)[:30]}_")
        else:
            st.caption("_Database required to view discovery forms_")

        st.markdown("---")

        # Notes section
        st.markdown("### 📝 Notes")
        existing_notes = contact.get('notes', '')

        if existing_notes:
            with st.container(border=True):
                st.markdown(existing_notes)
        else:
            st.caption("_No notes yet_")

        new_note_text = st.text_area("Add a note:", placeholder="Type your note here...", key="new_note_input", height=100)
        if st.button("📝 Add Note", key="add_note_btn"):
            if new_note_text.strip():
                timestamp = datetime.now().strftime("%m/%d/%Y %I:%M %p")
                new_note_entry = f"**[{timestamp}]** {new_note_text.strip()}"

                if existing_notes:
                    updated_notes = f"{new_note_entry}\n\n---\n\n{existing_notes}"
                else:
                    updated_notes = new_note_entry

                contact['notes'] = updated_notes

                if save_contact(contact['id'], {"notes": updated_notes}):
                    st.success("Note added!")
                    st.rerun()
                elif not db_is_connected():
                    st.info("Note saved locally")
                    st.rerun()
            else:
                st.warning("Please enter a note")

    with col2:
        # Business Card Image
        card_image_url = contact.get('card_image_url')
        if card_image_url:
            st.markdown("### 📇 Business Card")
            with st.container(border=True):
                try:
                    st.image(card_image_url, use_container_width=True, caption="Original Card")
                except Exception as e:
                    st.caption(f"_Could not load card image: {str(e)[:50]}_")

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
        current_source = contact.get('source', 'networking')
        current_source_idx = sources.index(current_source) if current_source in sources else 0
        new_source_label = st.selectbox("Source", source_labels, index=current_source_idx, key="edit_source_type")
        contact['source'] = sources[source_labels.index(new_source_label)]

        # Source Detail - right below Source
        new_source_detail = st.text_input("Source Detail", contact.get('source_detail', ''), key="edit_source_detail")

        # Tags
        st.markdown("### 🏷️ Tags")
        current_tags = contact.get('tags', [])

        if current_tags:
            for tag in current_tags:
                col_tag, col_remove = st.columns([4, 1])
                with col_tag:
                    st.markdown(f"`{tag}`")
                with col_remove:
                    if st.button("✕", key=f"remove_tag_{tag}"):
                        contact['tags'].remove(tag)
                        st.rerun()

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

        # Send Email - opens mailto: link
        email_addr = contact.get('email', '')
        if email_addr:
            mailto_link = f"mailto:{email_addr}?subject=Following%20Up"
            st.markdown(f'<a href="{mailto_link}" target="_blank" style="text-decoration: none;"><button style="width: 100%; padding: 0.5rem; background-color: #262730; color: white; border: 1px solid #3d3d4d; border-radius: 0.5rem; cursor: pointer; margin-bottom: 0.5rem;">📧 Send Email</button></a>', unsafe_allow_html=True)
        else:
            if st.button("📧 Send Email", use_container_width=True, disabled=True):
                pass
            st.caption("_No email address_")

        # Log Call - creates activity entry
        if st.button("📞 Log Call", use_container_width=True, key="log_call_btn"):
            st.session_state[f"show_log_call_{contact['id']}"] = True

        # Show call log form if toggled
        if st.session_state.get(f"show_log_call_{contact['id']}"):
            with st.container(border=True):
                call_notes = st.text_area("Call notes:", key=f"call_notes_{contact['id']}", height=80, placeholder="What was discussed?")
                call_outcome = st.selectbox("Outcome:", ["Connected", "Left Voicemail", "No Answer", "Wrong Number"], key=f"call_outcome_{contact['id']}")
                col_save, col_cancel = st.columns(2)
                with col_save:
                    if st.button("Save", key=f"save_call_{contact['id']}", type="primary", use_container_width=True):
                        if db_is_connected():
                            description = f"Call ({call_outcome}): {call_notes}" if call_notes else f"Call ({call_outcome})"
                            db_log_activity("call", description, contact_id=contact['id'])
                            # Update last_contacted
                            save_contact(contact['id'], {"last_contacted": datetime.now().isoformat()})
                            contact['last_contacted'] = datetime.now().strftime("%Y-%m-%d")
                        st.success("Call logged!")
                        st.session_state[f"show_log_call_{contact['id']}"] = False
                        st.rerun()
                with col_cancel:
                    if st.button("Cancel", key=f"cancel_call_{contact['id']}", use_container_width=True):
                        st.session_state[f"show_log_call_{contact['id']}"] = False
                        st.rerun()

        # Add Task - navigates to Tasks page with contact pre-filled
        if st.button("📝 Add Task", use_container_width=True, key="add_task_btn"):
            st.session_state.new_task_contact_id = contact['id']
            st.session_state.new_task_contact_name = f"{contact['first_name']} {contact['last_name']}"
            st.session_state.tasks_show_new_form = True
            st.switch_page("pages/05_Tasks.py")

        # Create Deal - navigates to Pipeline with form pre-filled
        if st.button("🎯 Create Deal", use_container_width=True, key="create_deal_btn"):
            st.session_state.pipeline_show_new_deal_form = True
            st.session_state.new_deal_contact_id = contact['id']
            st.session_state.new_deal_contact_name = f"{contact['first_name']} {contact['last_name']}"
            st.session_state.new_deal_company_name = contact.get('company', '')
            st.switch_page("pages/03_Pipeline.py")

        # Enroll in Campaign - navigates to Marketing page
        if st.button("📧 Enroll in Campaign", use_container_width=True, key="enroll_campaign_btn"):
            st.session_state.mkt_enroll_contact_id = contact['id']
            st.session_state.mkt_enroll_contact_name = f"{contact['first_name']} {contact['last_name']}"
            st.session_state.mkt_enroll_contact_email = contact.get('email', '')
            st.switch_page("pages/07_Marketing.py")

        # Merge section
        st.markdown("### 🔗 Merge Contacts")
        is_db_contact = db_is_connected() and not contact['id'].startswith("c-") and not contact['id'].startswith("local-")

        if is_db_contact:
            if st.button("🔗 Find Duplicates & Merge", use_container_width=True):
                st.session_state.contacts_show_merge = True
                st.session_state.contacts_merge_primary_id = contact['id']
                st.rerun()
        else:
            st.caption("_Merge available for database contacts only_")

        # Show merge interface if active
        if st.session_state.get('contacts_show_merge') and st.session_state.get('contacts_merge_primary_id') == contact['id']:
            show_merge_interface(contact)

        # Archive section
        st.markdown("### 📦 Archive")

        if is_db_contact:
            if st.button("📦 Archive Contact", use_container_width=True, type="secondary"):
                if archive_contact(contact['id']):
                    st.success("Contact archived!")
                    st.session_state.contacts_need_refresh = True
                    st.session_state.contacts_selected = None
                    st.session_state.selected_contact = None
                    st.rerun()
        else:
            st.caption("_Archive available for database contacts only_")

# ============================================
# NEW CONTACT FORM
# ============================================
if 'contacts_show_new_form' not in st.session_state:
    st.session_state.contacts_show_new_form = False

if 'contacts_show_archived' not in st.session_state:
    st.session_state.contacts_show_archived = False

if 'contacts_show_merge' not in st.session_state:
    st.session_state.contacts_show_merge = False

if 'contacts_merge_primary_id' not in st.session_state:
    st.session_state.contacts_merge_primary_id = None

def show_new_contact_form():
    """Display the new contact form"""
    st.markdown("---")
    st.markdown("## New Contact")

    with st.form("new_contact_form"):
        col1, col2 = st.columns(2)

        with col1:
            first_name = st.text_input("First Name *", placeholder="e.g., John")
            last_name = st.text_input("Last Name *", placeholder="e.g., Smith")
            email = st.text_input("Email", placeholder="e.g., john@company.com")
            phone = st.text_input("Phone", placeholder="e.g., (239) 555-0100")

        with col2:
            company = st.text_input("Company", placeholder="e.g., Smith Consulting")
            type_options = list(CONTACT_TYPES.keys())
            type_labels = [f"{CONTACT_TYPES[t]['icon']} {CONTACT_TYPES[t]['label']}" for t in type_options]
            contact_type = st.selectbox("Contact Type", type_labels, index=1)
            source = st.selectbox("Source", ["Networking", "Referral", "Website", "LinkedIn", "Cold Outreach", "Conference"])
            source_detail = st.text_input("Source Detail", placeholder="e.g., Cape Coral Chamber event")

        notes = st.text_area("Notes", placeholder="Any initial notes about this contact...")

        col_submit, col_cancel = st.columns(2)
        with col_submit:
            submitted = st.form_submit_button("Create Contact", type="primary", use_container_width=True)
        with col_cancel:
            cancelled = st.form_submit_button("Cancel", use_container_width=True)

        if submitted and first_name and last_name:
            contact_data = {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "phone": phone,
                "company": company,
                "type": type_options[type_labels.index(contact_type)],
                "source": source.lower().replace(" ", "_"),
                "source_detail": source_detail,
                "notes": notes,
                "tags": [],
                "email_status": "active"
            }

            result = create_contact(contact_data)
            if result:
                st.success(f"Contact '{first_name} {last_name}' created!")
                st.session_state.contacts_need_refresh = True
                st.session_state.contacts_show_new_form = False
                st.rerun()
            elif not db_is_connected():
                contact_data["id"] = f"local-{len(st.session_state.contacts)+1}"
                contact_data["created_at"] = datetime.now().strftime("%Y-%m-%d")
                contact_data["last_contacted"] = datetime.now().strftime("%Y-%m-%d")
                st.session_state.contacts.append(contact_data)
                st.success(f"Contact '{first_name} {last_name}' created (local only)")
                st.session_state.contacts_show_new_form = False
                st.rerun()
            else:
                st.error("Failed to create contact")

        if cancelled:
            st.session_state.contacts_show_new_form = False
            st.rerun()

# ============================================
# MAIN PAGE
# ============================================
st.title("👥 Contacts")

# Show database connection status in sidebar
with st.sidebar:
    if db_is_connected():
        st.success("Database connected", icon="✅")
    else:
        st.warning("Using sample data", icon="⚠️")

# Show detail view if contact selected
if st.session_state.contacts_selected:
    show_contact_detail(st.session_state.contacts_selected)
elif st.session_state.contacts_show_new_form:
    show_new_contact_form()
else:
    # View toggle (Active vs Archived)
    view_col1, view_col2 = st.columns([4, 1])
    with view_col2:
        if db_is_connected():
            if st.session_state.contacts_show_archived:
                if st.button("← Back to Active Contacts", use_container_width=True):
                    st.session_state.contacts_show_archived = False
                    st.rerun()
            else:
                if st.button("📦 View Archived", use_container_width=True):
                    st.session_state.contacts_show_archived = True
                    st.rerun()

    # Archived contacts view
    if st.session_state.contacts_show_archived and db_is_connected():
        st.markdown("## 📦 Archived Contacts")
        st.caption("These contacts have been archived and are no longer shown in the active list.")

        archived_contacts = load_archived_contacts()

        if not archived_contacts:
            st.info("No archived contacts. Archive contacts you no longer need from the contact detail view.")
        else:
            st.markdown(f"**{len(archived_contacts)} archived contacts**")
            st.markdown("---")

            for contact in archived_contacts:
                contact_type = contact.get('type', 'prospect')
                type_info = CONTACT_TYPES.get(contact_type, CONTACT_TYPES['prospect'])

                with st.container(border=True):
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

                    with col1:
                        st.markdown(f"**{type_info['icon']} {contact['first_name']} {contact['last_name']}**")
                        st.caption(f"🏢 {contact.get('company', 'N/A')}")

                    with col2:
                        st.markdown(f"📧 {contact.get('email', 'N/A')}")
                        archived_at = contact.get('archived_at', '')
                        if archived_at and 'T' in str(archived_at):
                            archived_at = str(archived_at).split('T')[0]
                        st.caption(f"Archived: {archived_at}")

                    with col3:
                        tags = contact.get('tags', [])[:2]
                        if tags:
                            st.markdown(" ".join([f"`{t}`" for t in tags]))

                    with col4:
                        if st.button("🔄 Restore", key=f"restore_{contact['id']}"):
                            if unarchive_contact(contact['id']):
                                st.success(f"Restored {contact['first_name']} {contact['last_name']}")
                                st.session_state.contacts_need_refresh = True
                                st.rerun()

    else:
        # Active contacts view
        # Toolbar
        toolbar_col1, toolbar_col2, toolbar_col3, toolbar_col4, toolbar_col5 = st.columns([2, 1, 1, 1, 1])

        with toolbar_col1:
            search = st.text_input("🔍 Search contacts...", placeholder="Name, company, or email", label_visibility="collapsed")

        with toolbar_col2:
            type_filter = st.selectbox("Type", ["All Types"] + [CONTACT_TYPES[t]['label'] for t in CONTACT_TYPES], label_visibility="collapsed")

        with toolbar_col3:
            tag_filter = st.selectbox("Tag", ["All Tags"] + ALL_TAGS, label_visibility="collapsed")

        with toolbar_col4:
            if st.button("🔄 Refresh", use_container_width=True):
                st.session_state.contacts_need_refresh = True
                st.rerun()

        with toolbar_col5:
            if st.button("➕ New Contact", type="primary", use_container_width=True):
                st.session_state.contacts_show_new_form = True
                st.session_state.contacts_selected = None
                st.rerun()

        # Filter contacts
        filtered_contacts = st.session_state.contacts

        if search:
            search_lower = search.lower()
            filtered_contacts = [c for c in filtered_contacts if
                search_lower in c['first_name'].lower() or
                search_lower in c['last_name'].lower() or
                search_lower in c.get('company', '').lower() or
                search_lower in c.get('email', '').lower()]

        if type_filter != "All Types":
            type_key = next(k for k, v in CONTACT_TYPES.items() if v['label'] == type_filter)
            filtered_contacts = [c for c in filtered_contacts if c.get('type') == type_key]

        if tag_filter != "All Tags":
            filtered_contacts = [c for c in filtered_contacts if tag_filter in c.get('tags', [])]

        # Stats row
        stat_cols = st.columns(7)
        for i, (type_key, type_info) in enumerate(CONTACT_TYPES.items()):
            count = len([c for c in st.session_state.contacts if c.get('type') == type_key])
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
                    st.caption(f"🏢 {contact.get('company', 'N/A')}")

                with col2:
                    st.markdown(f"📧 {contact.get('email', 'N/A')}")
                    st.caption(f"📞 {contact.get('phone', 'N/A')}")

                with col3:
                    tags = contact.get('tags', [])[:3]
                    if tags:
                        st.markdown(" ".join([f"`{t}`" for t in tags]))
                    last_contacted = contact.get('last_contacted') or contact.get('created_at', 'N/A')
                    if last_contacted and 'T' in str(last_contacted):
                        last_contacted = str(last_contacted).split('T')[0]
                    st.caption(f"Last contact: {last_contacted}")

                with col4:
                    if st.button("Open", key=f"open_{contact['id']}"):
                        st.session_state.contacts_selected = contact['id']
                        st.session_state.selected_contact = contact['id']
                        st.rerun()
