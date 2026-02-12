"""
MPT-CRM Contacts Page
Manage contacts with types, tags, and full detail views

Database operations are handled by db_service.py — the single source of truth.
"""

import streamlit as st
from datetime import datetime
import os
import requests
from PIL import Image
from io import BytesIO
import base64
import time
import uuid
import json
import db_service
from db_service import (
    db_is_connected,
    db_get_contact, db_create_contact, db_update_contact,
    db_delete_contact, db_archive_contact, db_unarchive_contact,
    db_get_archived_contacts, db_find_potential_duplicates,
    db_merge_contacts, db_log_activity,
    db_get_contact_email_sends, db_get_contact_activities,
    upload_card_image_to_supabase,
    db_update_contact_and_switch_campaign,
)
from db_service import db_get_contacts as _raw_get_contacts
from db_service import db_get_intakes as _raw_get_intakes
from sso_auth import require_sso_auth, render_auth_status

# Page load timing
_page_load_start = time.time()

st.set_page_config(
    page_title="MPT-CRM - Contacts",
    page_icon="favicon.jpg",
    layout="wide"
)

require_sso_auth()

# ============================================
# CACHING LAYER — wraps db_service functions
# ============================================
@st.cache_data(ttl=300, show_spinner=False)
def cached_get_contacts(include_archived=False, _cache_key=None):
    """Get all contacts from database with caching"""
    return _raw_get_contacts(include_archived)

def invalidate_contacts_cache():
    """Clear the contacts cache to force refresh"""
    cached_get_contacts.clear()

def db_get_contacts(include_archived=False):
    """Get all contacts from database (uses cache)"""
    cache_key = st.session_state.get('contacts_cache_version', 0)
    return cached_get_contacts(include_archived, _cache_key=cache_key)

@st.cache_data(ttl=1800, show_spinner=False)
def cached_get_intakes(contact_id=None, _cache_key=None):
    """Get client intakes for a contact (cached)"""
    return _raw_get_intakes(contact_id)

def db_get_intakes(contact_id=None):
    """Get client intakes for a contact"""
    cache_key = st.session_state.get('intakes_cache_version', 0)
    return cached_get_intakes(contact_id, _cache_key=cache_key)

# ============================================
# IMAGE HELPERS
# ============================================
@st.cache_data(ttl=3600, show_spinner=False)  # Cache for 1 hour
def get_rotated_image(image_url, rotation_degrees):
    """Fetch image from URL and rotate it by specified degrees (cached)"""
    try:
        print(f"[DEBUG] Rotating image (cache miss): {image_url[:50]}... by {rotation_degrees}°")
        import time
        start_time = time.time()

        # Fetch the image with shorter timeout and no retries
        response = requests.get(image_url, timeout=(3, 10))  # 3s connection, 10s read
        fetch_time = time.time() - start_time
        print(f"[DEBUG] Fetch took {fetch_time:.2f}s")
        if response.status_code != 200:
            print(f"[DEBUG] Failed to fetch image: HTTP {response.status_code}")
            return None

        # Open with PIL
        img = Image.open(BytesIO(response.content))
        print(f"[DEBUG] Original image size: {img.size}")

        # Rotate the image (PIL rotate: positive = counter-clockwise)
        # For 90° clockwise rotation (portrait to landscape), we need -90
        if rotation_degrees != 0:
            img = img.rotate(-rotation_degrees, expand=True)
            print(f"[DEBUG] Rotated image size: {img.size}")

        # Convert to bytes for Streamlit
        buf = BytesIO()
        img.save(buf, format='JPEG', quality=85)
        buf.seek(0)

        print(f"[DEBUG] Successfully rotated image")
        return buf.getvalue()  # Return bytes instead of BytesIO for caching
    except Exception as e:
        print(f"[ERROR] Error rotating image: {e}")
        import traceback
        traceback.print_exc()
        return None

# ============================================
# BUSINESS CARD SCANNER FUNCTIONS (AI/Vision — NOT database operations)
# ============================================

def extract_contact_from_business_card(image_bytes, image_type="image/png"):
    """
    Use Claude Vision API to extract contact info from a business card image.
    Returns dict with first_name, last_name, company, email, phone, title, confidence, raw_text.
    """
    try:
        import anthropic
    except ImportError:
        return {"error": "anthropic package not installed. Run: pip install anthropic"}

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return {"error": "ANTHROPIC_API_KEY not configured in environment variables"}

    # Optimize image size to avoid timeouts
    try:
        img = Image.open(BytesIO(image_bytes))

        # Resize if image is very large (max 1600px on longest side)
        max_size = 1600
        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        # Convert to JPEG with quality 85 to reduce size
        output = BytesIO()
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")
        img.save(output, format="JPEG", quality=85, optimize=True)
        image_bytes = output.getvalue()
        image_type = "image/jpeg"
    except Exception as e:
        print(f"[Contact Extraction] Image optimization failed: {e}, using original")

    # Encode image to base64
    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    extraction_prompt = """Analyze this business card image and extract the contact information.

Return a JSON object with these fields (use null for any field not found):
{
    "first_name": "extracted first name",
    "last_name": "extracted last name",
    "company": "company/organization name",
    "email": "email address",
    "phone": "phone number (preserve formatting)",
    "title": "job title/position",
    "website": "website URL if present",
    "address": "physical address if present",
    "confidence": 0.0 to 1.0 rating of extraction confidence,
    "raw_text": "all text visible on the card"
}

Important:
- Extract the primary contact's name, not company name as the person's name
- If multiple phone numbers, prefer mobile/cell
- If multiple emails, prefer personal over generic (info@, contact@)
- Clean up any OCR artifacts in the text
- Return ONLY the JSON object, no other text"""

    try:
        client = anthropic.Anthropic(api_key=api_key, timeout=60.0)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": image_type,
                                "data": image_b64
                            }
                        },
                        {
                            "type": "text",
                            "text": extraction_prompt
                        }
                    ]
                }
            ]
        )

        result_text = response.content[0].text

        # Handle markdown code blocks
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0]
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0]

        return json.loads(result_text.strip())
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse response: {e}", "raw_text": result_text if 'result_text' in dir() else ""}
    except Exception as e:
        return {"error": str(e)}

# upload_card_image_to_supabase is imported from db_service

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
    "Help": {"icon": "❓", "path": "pages/11_Help.py"},
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
# NO SAMPLE DATA - Database only

# ============================================
# PAGE-SPECIFIC HELPER FUNCTIONS
# ============================================
def load_contacts():
    """Load contacts from database only - no sample data"""
    if db_is_connected():
        try:
            contacts = db_get_contacts()
            return contacts if contacts is not None else []
        except Exception as e:
            st.error(f"Database error: {str(e)[:50]}...")
            return []
    else:
        st.error("Database not connected. Check your .env file.")
        return []

def save_contact(contact_id, contact_data):
    """Save contact updates to database"""
    if db_is_connected() and not contact_id.startswith("c-") and not contact_id.startswith("local-"):
        try:
            db_update_contact(contact_id, contact_data)
            # Invalidate cache after update
            st.session_state.contacts_cache_version = st.session_state.get('contacts_cache_version', 0) + 1
            return True
        except Exception as e:
            st.error(f"Failed to save: {str(e)[:50]}")
    return False

def create_contact(contact_data):
    """Create a new contact in the database"""
    if db_is_connected():
        try:
            result = db_create_contact(contact_data)
            # Invalidate cache after creation
            st.session_state.contacts_cache_version = st.session_state.get('contacts_cache_version', 0) + 1
            return result
        except Exception as e:
            st.error(f"Database error: {str(e)[:50]}")
    return None

def delete_contact(contact_id):
    """Delete a contact from the database"""
    if db_is_connected() and not contact_id.startswith("c-") and not contact_id.startswith("local-"):
        try:
            result = db_delete_contact(contact_id)
            # Invalidate cache after deletion
            st.session_state.contacts_cache_version = st.session_state.get('contacts_cache_version', 0) + 1
            return result
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
                                st.session_state.contacts_cache_version = st.session_state.get('contacts_cache_version', 0) + 1
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
    import time
    detail_start = time.time()

    contact = next((c for c in st.session_state.contacts if c['id'] == contact_id), None)
    if not contact:
        st.session_state.contacts_selected = None
        st.session_state.selected_contact = None
        st.rerun()
        return

    # Store original type for detecting changes (used by auto-campaign-switch)
    original_type_key = f'_original_type_{contact_id}'
    if original_type_key not in st.session_state:
        st.session_state[original_type_key] = contact.get('type', 'prospect')

    lookup_time = time.time() - detail_start
    st.sidebar.caption(f"⏱️ Lookup: {lookup_time:.2f}s")

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
    header_time = time.time() - detail_start
    st.sidebar.caption(f"⏱️ Header: {header_time:.2f}s")

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
            new_title = st.text_input("Title", contact.get('title', ''), key="edit_title")

        # Check if delete confirmation is pending
        if st.session_state.get('delete_confirm_contact_id') == contact['id']:
            # Show confirmation dialog - prominently at the top
            st.error(f"⚠️ **DELETE CONFIRMATION REQUIRED**")
            st.warning(f"Are you sure you want to permanently delete **{contact['first_name']} {contact['last_name']}**? This cannot be undone!")
            confirm_col1, confirm_col2 = st.columns(2)
            with confirm_col1:
                if st.button("✅ Yes, Delete", key="confirm_delete_final", type="primary", use_container_width=True):
                    if db_is_connected():
                        try:
                            # Delete the contact
                            db_delete_contact(contact['id'])

                            # Invalidate cache
                            if 'contacts_cache_version' in st.session_state:
                                st.session_state.contacts_cache_version += 1
                            if 'intakes_cache_version' in st.session_state:
                                st.session_state.intakes_cache_version += 1

                            # Clear session state
                            if 'selected_contact_id' in st.session_state:
                                del st.session_state.selected_contact_id
                            if 'delete_confirm_contact_id' in st.session_state:
                                del st.session_state.delete_confirm_contact_id

                            st.success(f"✅ Contact deleted!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting contact: {e}")
                            if 'delete_confirm_contact_id' in st.session_state:
                                del st.session_state.delete_confirm_contact_id
                    else:
                        st.error("Database not connected")
            with confirm_col2:
                if st.button("❌ Cancel", key="cancel_delete_btn", use_container_width=True):
                    del st.session_state.delete_confirm_contact_id
                    st.rerun()
        else:
            # Show action buttons
            btn_col1, btn_col2 = st.columns([3, 1])
            with btn_col1:
                save_btn = st.button("💾 Save Contact Info", type="primary", key="save_contact_info", use_container_width=True)
            with btn_col2:
                delete_btn = st.button("🗑️ Delete", key="delete_contact_btn", use_container_width=True)

            if save_btn:
                # Get source_detail from session state (will be set in col2)
                new_source_detail = st.session_state.get('edit_source_detail', contact.get('source_detail', ''))
                update_data = {
                    "first_name": new_first,
                    "last_name": new_last,
                    "email": new_email,
                    "phone": new_phone,
                    "title": new_title,
                    "company": new_company,
                    "source_detail": new_source_detail,
                    "type": contact.get('type', 'prospect'),
                    "source": contact.get('source', 'networking'),
                    "tags": contact.get('tags', []),
                    "email_status": contact.get('email_status', 'active'),
                }

                # Detect contact type change and auto-switch campaign
                original_type = st.session_state.get(f'_original_type_{contact["id"]}', '')
                new_type = update_data['type']
                if original_type and original_type != new_type:
                    # Type changed — use campaign-switching update
                    switch_result = db_update_contact_and_switch_campaign(
                        contact['id'], new_type, old_type=original_type
                    )
                    if switch_result.get('success'):
                        contact.update(update_data)
                        st.session_state.contacts_cache_version = st.session_state.get('contacts_cache_version', 0) + 1
                        st.success(f"Contact saved! {switch_result.get('message', '')}")
                    else:
                        st.error(f"Error: {switch_result.get('message', 'Unknown error')}")
                else:
                    contact.update(update_data)
                    if save_contact(contact['id'], update_data):
                        st.success("Contact saved!")
                    elif not db_is_connected():
                        st.info("Changes saved locally (connect database to persist)")

            if delete_btn:
                # Set delete confirmation flag
                st.session_state.delete_confirm_contact_id = contact['id']
                st.rerun()

        # Activity Timeline
        st.markdown("### 📅 Recent Activity")
        with st.container(border=True):
            # Pull real activities from database
            activities = []
            if db_is_connected():
                try:
                    # Get email sends
                    sends_data = db_get_contact_email_sends(contact['id'], limit=5)
                    if sends_data:
                        for send in sends_data:
                            sent_date = send.get('sent_at', 'Unknown')
                            if sent_date and sent_date != 'Unknown':
                                try:
                                    sent_date = datetime.fromisoformat(sent_date.replace('Z', '+00:00')).strftime('%b %d, %Y %I:%M %p')
                                except Exception:
                                    pass
                            activities.append(f"📧 Email sent — {send.get('subject', 'No subject')} — {sent_date}")

                    # Get activities table
                    act_data = db_get_contact_activities(contact['id'], limit=5)
                    if act_data:
                        for act in act_data:
                            act_date = act.get('created_at', '')
                            if act_date:
                                try:
                                    act_date = datetime.fromisoformat(act_date.replace('Z', '+00:00')).strftime('%b %d, %Y')
                                except Exception:
                                    pass
                            activities.append(f"📋 {act.get('type', 'Activity')} — {act.get('description', '')} — {act_date}")
                except Exception:
                    pass

            # Always show contact creation and last contacted
            if contact.get('last_contacted'):
                lc = contact['last_contacted']
                try:
                    lc = datetime.fromisoformat(lc.replace('Z', '+00:00')).strftime('%b %d, %Y')
                except Exception:
                    pass
                activities.append(f"📧 Last contacted — {lc}")

            created = contact.get('created_at', 'N/A')
            try:
                created = datetime.fromisoformat(created.replace('Z', '+00:00')).strftime('%b %d, %Y')
            except Exception:
                pass
            activities.append(f"📝 Contact created — {created}")

            if activities:
                for act in activities:
                    st.caption(act)
            else:
                st.caption("No activity recorded yet.")

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

        # Projects section
        st.markdown("### 📁 Projects")
        if db_is_connected():
            try:
                # Import the projects function
                from db_service import db_get_projects_by_contact
                contact_projects = db_get_projects_by_contact(contact['id'])
                
                if contact_projects:
                    for project in contact_projects:
                        with st.container(border=True):
                            col_info, col_action = st.columns([4, 1])
                            with col_info:
                                project_name = project.get('name', 'Untitled Project')
                                st.markdown(f"**{project_name}**")
                                
                                # Show project status and value
                                status = project.get('status', 'active').replace('_', ' ').title()
                                hours_logged = project.get('hours_logged', 0) or 0
                                estimated_hours = project.get('estimated_hours', 0) or 0
                                hourly_rate = project.get('hourly_rate', 150) or 150
                                value = estimated_hours * hourly_rate
                                
                                status_icons = {
                                    'Planning': '📋', 'Active': '🚀', 'On Hold': '⏸️',
                                    'Completed': '✅', 'Maintenance': '🛠️', 'Cancelled': '❌'
                                }
                                status_icon = status_icons.get(status, '📁')
                                
                                if value > 0:
                                    st.caption(f"{status_icon} {status} | ${value:,.0f} | {hours_logged}/{estimated_hours} hrs")
                                else:
                                    st.caption(f"{status_icon} {status} | {hours_logged} hrs logged")
                                
                                # Show source deal if available
                                if project.get('deal_id'):
                                    st.caption(f"🎯 Source Deal: {project['deal_id'][:8]}...")
                            
                            with col_action:
                                if st.button("Open", key=f"project_{project['id']}", type="primary"):
                                    st.session_state.proj_selected_project = project['id']
                                    st.switch_page("pages/04_Projects.py")
                else:
                    st.caption("_No projects yet_")
                    
                    # Check if this contact has won deals available for project creation
                    from db_service import db_get_won_deals_by_contact
                    won_deals = db_get_won_deals_by_contact(contact['id'])
                    if won_deals:
                        # Filter out deals already linked to projects
                        from db_service import db_check_deal_project_link
                        available_deals = []
                        for deal in won_deals:
                            if not db_check_deal_project_link(deal['id']):
                                available_deals.append(deal)
                        
                        if available_deals:
                            if st.button("➕ Create Project", key="create_project_from_contact"):
                                # Pre-select this contact for project creation
                                st.session_state.new_project_contact_id = contact['id']
                                st.session_state.new_project_client = f"{contact.get('company', '')} ({contact['first_name']} {contact['last_name']})"
                                st.session_state.proj_show_new_form = True
                                st.switch_page("pages/04_Projects.py")
                        else:
                            st.caption("_All Won deals already have projects_")
                    else:
                        st.caption("_Win a deal first to create projects_")
                        
            except Exception as e:
                st.caption(f"_Could not load projects: {str(e)[:30]}_")
        else:
            st.caption("_Database required to view projects_")

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

    col1_time = time.time() - detail_start
    st.sidebar.caption(f"⏱️ Col1 done: {col1_time:.2f}s")

    with col2:
        # Business Card Section - with upload capability
        st.markdown("### 📇 Business Card")
        card_image_url = contact.get('card_image_url')

        with st.container(border=True):
            if card_image_url:
                try:
                    # Initialize session state for card image index and rotation
                    if 'card_image_index' not in st.session_state:
                        st.session_state.card_image_index = 0
                    if 'card_image_enlarged' not in st.session_state:
                        st.session_state.card_image_enlarged = False
                    if f'card_rotation_{contact_id}' not in st.session_state:
                        st.session_state[f'card_rotation_{contact_id}'] = {}

                    # Get all card images for this contact from storage
                    card_images = []
                    cid = contact['id']

                    # Try to list all card images from Supabase Storage
                    try:
                        from db_service import db_list_card_images, db_get_card_image_url
                        storage_files = db_list_card_images(cid)
                        if storage_files:
                            card_images = [db_get_card_image_url(f['name']) for f in storage_files if f.get('name')]
                            card_images = [url for url in card_images if url]  # filter None
                    except Exception:
                        pass

                    # Fallback to single image if no images found in storage
                    if not card_images and card_image_url:
                        card_images = [card_image_url]

                    # Only display if we have images
                    if not card_images:
                        raise Exception("No card image found")

                    # Ensure index is valid
                    if st.session_state.card_image_index >= len(card_images):
                        st.session_state.card_image_index = 0

                    # Display current card image
                    current_img = card_images[st.session_state.card_image_index]
                    current_img_key = f"img_{st.session_state.card_image_index}"

                    # Get rotation for current image (default 270 for landscape right-side-up)
                    rotation_dict = st.session_state.get(f'card_rotation_{cid}', {})
                    current_rotation = rotation_dict.get(current_img_key, 270)

                    # Get rotated image (cached - should be instant after first load)
                    start = time.time()
                    rotated_img = get_rotated_image(current_img, current_rotation)
                    elapsed = time.time() - start
                    if elapsed > 1:
                        st.caption(f"⚠️ Image load took {elapsed:.1f}s (should be cached)")

                    # Display image at full container width (always)
                    if rotated_img:
                        st.image(rotated_img, use_container_width=True)
                    else:
                        st.image(current_img, use_container_width=True)

                    # Pagination if multiple images
                    if len(card_images) > 1:
                        st.caption(f"📄 {st.session_state.card_image_index + 1} of {len(card_images)}")
                        col_prev, col_next = st.columns(2)
                        with col_prev:
                            if st.button("◀ Previous", key="prev_card", disabled=st.session_state.card_image_index == 0, use_container_width=True):
                                st.session_state.card_image_index -= 1
                                st.rerun()
                        with col_next:
                            if st.button("Next ▶", key="next_card", disabled=st.session_state.card_image_index == len(card_images) - 1, use_container_width=True):
                                st.session_state.card_image_index += 1
                                st.rerun()

                    # Rotation button
                    if st.button("↷ Rotate 90°", key="rotate_card", use_container_width=True):
                        rotation_dict[current_img_key] = (current_rotation + 90) % 360
                        st.session_state[f'card_rotation_{cid}'] = rotation_dict
                        st.rerun()

                except Exception as e:
                    st.caption(f"_Could not load card image: {str(e)[:50]}_")

            # Upload/Replace Card option
            with st.expander("📤 Upload New Card" if card_image_url else "📤 Add Business Card"):
                uploaded_card = st.file_uploader(
                    "Upload card image",
                    type=["png", "jpg", "jpeg", "webp"],
                    key=f"card_upload_{contact['id']}",
                    label_visibility="collapsed"
                )

                if uploaded_card is not None:
                    st.image(uploaded_card, caption="Preview", use_container_width=True)

                    col_upload, col_scan = st.columns(2)
                    with col_upload:
                        if st.button("💾 Save Card", type="primary", use_container_width=True, key="save_card_btn"):
                            with st.spinner("Uploading..."):
                                image_bytes = uploaded_card.getvalue()
                                card_url = upload_card_image_to_supabase(image_bytes, contact['id'])
                                if card_url:
                                    db_update_contact(contact['id'], {"card_image_url": card_url})
                                    st.success("Card saved!")
                                    st.session_state.contacts_need_refresh = True
                                    st.rerun()
                                else:
                                    st.error("Upload failed")

                    with col_scan:
                        if st.button("🔍 Scan & Update", use_container_width=True, key="scan_update_btn"):
                            with st.spinner("Scanning with AI..."):
                                image_bytes = uploaded_card.getvalue()
                                image_type = f"image/{uploaded_card.type.split('/')[-1]}" if uploaded_card.type and '/' in uploaded_card.type else "image/png"

                                result = extract_contact_from_business_card(image_bytes, image_type)

                                if "error" in result:
                                    st.error(f"Scan failed: {result['error']}")
                                else:
                                    # Upload the image
                                    card_url = upload_card_image_to_supabase(image_bytes, contact['id'])

                                    # Update contact with scanned data + card URL
                                    update_data = {}
                                    if card_url:
                                        update_data["card_image_url"] = card_url
                                    if result.get('phone') and not contact.get('phone'):
                                        update_data["phone"] = result['phone']
                                    if result.get('email') and not contact.get('email'):
                                        update_data["email"] = result['email']
                                    if result.get('title') and not contact.get('title'):
                                        update_data["title"] = result['title']
                                    if result.get('company') and not contact.get('company'):
                                        update_data["company"] = result['company']

                                    if update_data:
                                        db_update_contact(contact['id'], update_data)
                                        st.success(f"Card saved & info updated!")
                                        st.session_state.contacts_need_refresh = True
                                        st.rerun()
                                    else:
                                        st.success("Card saved (no new info to update)")
                                        st.rerun()

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
        email_statuses = ["pending", "active", "unsubscribed", "bounced"]
        status_labels = ["⏳ Pending", "✅ Active", "🚫 Unsubscribed", "⚠️ Bounced"]
        current_email_status = contact.get('email_status', 'active')
        # Handle case where email_status is not in the list
        current_status_idx = email_statuses.index(current_email_status) if current_email_status in email_statuses else 1  # Default to 'active'
        new_status = st.selectbox("Status", status_labels, index=current_status_idx, key="email_status")
        contact['email_status'] = email_statuses[status_labels.index(new_status)]

        # Quick actions
        st.markdown("### ⚡ Quick Actions")

        # Send Email - opens Outlook Web compose with business account
        email_addr = contact.get('email', '')
        from_email = os.getenv("SENDGRID_FROM_EMAIL", "patrick@metropointtechnology.com")
        if email_addr:
            import urllib.parse
            subject = urllib.parse.quote("Following Up")
            to_encoded = urllib.parse.quote(email_addr)
            # Use Outlook Web App (OWA) to compose from business account
            owa_link = f"https://outlook.office.com/mail/deeplink/compose?to={to_encoded}&subject={subject}"
            st.markdown(f'<a href="{owa_link}" target="_blank" style="text-decoration: none;"><button style="width: 100%; padding: 0.5rem; background-color: #262730; color: white; border: 1px solid #3d3d4d; border-radius: 0.5rem; cursor: pointer; margin-bottom: 0.5rem;">📧 Send Email</button></a>', unsafe_allow_html=True)
            st.caption(f"_Opens Outlook Web as {from_email}_")
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

    col2_time = time.time() - detail_start
    st.sidebar.caption(f"⏱️ Col2 done: {col2_time:.2f}s")

    # Show total render time
    total_time = time.time() - detail_start
    st.sidebar.caption(f"⏱️ Total render: {total_time:.2f}s")

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
    """Display the new contact form with business card scanning option"""
    st.markdown("---")
    st.markdown("## New Contact")

    # Initialize session state for scanned card data
    if 'scanned_card_data' not in st.session_state:
        st.session_state.scanned_card_data = None
    if 'scanned_card_image' not in st.session_state:
        st.session_state.scanned_card_image = None

    # Business Card Upload Section (outside form for immediate processing)
    with st.container(border=True):
        st.markdown("#### 📇 Scan Business Card")
        st.caption("Upload a business card image to auto-fill contact information")

        uploaded_card = st.file_uploader(
            "Upload business card",
            type=["png", "jpg", "jpeg", "webp"],
            key="new_contact_card_upload",
            label_visibility="collapsed"
        )

        if uploaded_card is not None:
            col_img, col_action = st.columns([2, 1])
            with col_img:
                st.image(uploaded_card, caption="Uploaded Card", use_container_width=True)

            with col_action:
                if st.button("🔍 Extract Info", type="primary", use_container_width=True):
                    with st.spinner("Scanning card with AI..."):
                        image_bytes = uploaded_card.getvalue()
                        image_type = f"image/{uploaded_card.type.split('/')[-1]}" if uploaded_card.type and '/' in uploaded_card.type else "image/png"

                        result = extract_contact_from_business_card(image_bytes, image_type)

                        if "error" in result:
                            st.error(f"Scan failed: {result['error']}")
                        else:
                            st.session_state.scanned_card_data = result
                            st.session_state.scanned_card_image = image_bytes
                            st.success("Card scanned!")
                            st.rerun()

        if st.session_state.scanned_card_data:
            data = st.session_state.scanned_card_data
            confidence = data.get('confidence', 0)
            confidence_pct = int(confidence * 100) if confidence else 0
            st.success(f"Extracted ({confidence_pct}%): **{data.get('first_name', '')} {data.get('last_name', '')}** - {data.get('company', '')}")
            if st.button("Clear Scanned Data", key="clear_scan"):
                st.session_state.scanned_card_data = None
                st.session_state.scanned_card_image = None
                st.rerun()

    st.markdown("---")

    # Get pre-filled values from scanned card
    scanned = st.session_state.scanned_card_data or {}

    with st.form("new_contact_form"):
        col1, col2 = st.columns(2)

        with col1:
            first_name = st.text_input("First Name *", value=scanned.get('first_name', '') or '', placeholder="e.g., John")
            last_name = st.text_input("Last Name *", value=scanned.get('last_name', '') or '', placeholder="e.g., Smith")
            email = st.text_input("Email", value=scanned.get('email', '') or '', placeholder="e.g., john@company.com")
            phone = st.text_input("Phone", value=scanned.get('phone', '') or '', placeholder="e.g., (239) 555-0100")

        with col2:
            company = st.text_input("Company", value=scanned.get('company', '') or '', placeholder="e.g., Smith Consulting")
            type_options = list(CONTACT_TYPES.keys())
            type_labels = [f"{CONTACT_TYPES[t]['icon']} {CONTACT_TYPES[t]['label']}" for t in type_options]
            contact_type = st.selectbox("Contact Type", type_labels, index=1)
            source = st.selectbox("Source", ["Networking", "Referral", "Website", "LinkedIn", "Cold Outreach", "Conference"])
            source_detail = st.text_input("Source Detail", placeholder="e.g., Cape Coral Chamber event")

        title = st.text_input("Title", value=scanned.get('title', '') or '', placeholder="e.g., CEO, Sales Manager")
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
                "title": title,
                "type": type_options[type_labels.index(contact_type)],
                "source": source.lower().replace(" ", "_"),
                "source_detail": source_detail,
                "notes": notes,
                "tags": [],
                "email_status": "active"
            }

            result = create_contact(contact_data)
            if result:
                # Upload card image if we have one
                if st.session_state.scanned_card_image and result.get('id'):
                    card_url = upload_card_image_to_supabase(st.session_state.scanned_card_image, result['id'])
                    if card_url:
                        db_update_contact(result['id'], {"card_image_url": card_url})

                st.success(f"Contact '{first_name} {last_name}' created!")
                st.session_state.scanned_card_data = None
                st.session_state.scanned_card_image = None
                st.session_state.contacts_need_refresh = True
                st.session_state.contacts_show_new_form = False
                st.rerun()
            elif not db_is_connected():
                contact_data["id"] = f"local-{len(st.session_state.contacts)+1}"
                contact_data["created_at"] = datetime.now().strftime("%Y-%m-%d")
                contact_data["last_contacted"] = datetime.now().strftime("%Y-%m-%d")
                st.session_state.contacts.append(contact_data)
                st.success(f"Contact '{first_name} {last_name}' created (local only)")
                st.session_state.scanned_card_data = None
                st.session_state.scanned_card_image = None
                st.session_state.contacts_show_new_form = False
                st.rerun()
            else:
                st.error("Failed to create contact")

        if cancelled:
            st.session_state.scanned_card_data = None
            st.session_state.scanned_card_image = None
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
        st.error("Database not connected - check .env file", icon="❌")

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
                search_lower in (c.get('first_name') or '').lower() or
                search_lower in (c.get('last_name') or '').lower() or
                search_lower in (c.get('company') or '').lower() or
                search_lower in (c.get('email') or '').lower()]

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

# Show page load time in sidebar (for debugging)
_page_load_time = time.time() - _page_load_start
st.sidebar.caption(f"⏱️ Page load: {_page_load_time:.2f}s")
