"""
MPT-CRM Companies Page
Manage companies with centralized address management and associated contacts

Database operations are handled by db_service.py — the single source of truth.
"""

import streamlit as st
from datetime import datetime
import time
import db_service
from db_service import (
    db_is_connected,
    db_execute_query,
    db_fetch_all,
    db_fetch_one,
)
from auth import require_login

# Page load timing
_page_load_start = time.time()

st.set_page_config(
    page_title="MPT-CRM - Companies",
    page_icon="favicon.jpg",
    layout="wide"
)

require_login()

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
    "Companies": {"icon": "🏢", "path": "pages/01a_Companies.py"},
    "Sales Pipeline": {"icon": "🎯", "path": "pages/03_Pipeline.py"},
    "Projects": {"icon": "📁", "path": "pages/04_Projects.py"},
    "Service": {"icon": "\U0001f527", "path": "pages/10_Service.py"},
    "Tasks": {"icon": "✅", "path": "pages/05_Tasks.py"},
    "Time & Billing": {"icon": "💰", "path": "pages/06_Time_Billing.py"},
    "Marketing": {"icon": "📧", "path": "pages/07_Marketing.py"},
    "Reports": {"icon": "📈", "path": "pages/08_Reports.py"},
    "Settings": {"icon": "⚙️", "path": "pages/09_Settings.py"},
}

def render_sidebar(current_page="Companies"):
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
# COMPANY DATABASE FUNCTIONS
# ============================================
@st.cache_data(ttl=300, show_spinner=False)
def get_companies(_cache_key=None):
    """Get all companies from database with caching"""
    if not db_is_connected():
        return []
    
    query = """
        SELECT id, name, website, industry, phone, 
               physical_street, physical_city, physical_state, physical_zip,
               mailing_street, mailing_city, mailing_state, mailing_zip,
               billing_street, billing_city, billing_state, billing_zip,
               notes, created_at, updated_at
        FROM companies 
        ORDER BY name
    """
    
    try:
        return db_fetch_all(query) or []
    except Exception as e:
        st.error(f"Error loading companies: {str(e)}")
        return []

@st.cache_data(ttl=300, show_spinner=False)
def get_company_contacts(company_id, _cache_key=None):
    """Get contacts for a specific company with caching"""
    if not db_is_connected():
        return []
    
    query = """
        SELECT id, first_name, last_name, email, phone, role, 
               card_image_url, card_image_url_2, notes, created_at
        FROM contacts 
        WHERE company_id = %s
        ORDER BY role, last_name, first_name
    """
    
    try:
        return db_fetch_all(query, (company_id,)) or []
    except Exception as e:
        st.error(f"Error loading company contacts: {str(e)}")
        return []

def invalidate_companies_cache():
    """Clear the companies cache to force refresh"""
    get_companies.clear()
    get_company_contacts.clear()

def create_company(company_data):
    """Create a new company in the database"""
    if not db_is_connected():
        return None
    
    query = """
        INSERT INTO companies (name, website, industry, phone, 
                              physical_street, physical_city, physical_state, physical_zip,
                              mailing_street, mailing_city, mailing_state, mailing_zip,
                              billing_street, billing_city, billing_state, billing_zip, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """
    
    try:
        result = db_fetch_one(query, (
            company_data.get('name'),
            company_data.get('website'),
            company_data.get('industry'),
            company_data.get('phone'),
            company_data.get('physical_street'),
            company_data.get('physical_city'),
            company_data.get('physical_state'),
            company_data.get('physical_zip'),
            company_data.get('mailing_street'),
            company_data.get('mailing_city'),
            company_data.get('mailing_state'),
            company_data.get('mailing_zip'),
            company_data.get('billing_street'),
            company_data.get('billing_city'),
            company_data.get('billing_state'),
            company_data.get('billing_zip'),
            company_data.get('notes')
        ))
        invalidate_companies_cache()
        return result['id'] if result else None
    except Exception as e:
        st.error(f"Error creating company: {str(e)}")
        return None

def update_company(company_id, company_data):
    """Update a company in the database"""
    if not db_is_connected():
        return False
    
    query = """
        UPDATE companies 
        SET name = %s, website = %s, industry = %s, phone = %s,
            physical_street = %s, physical_city = %s, physical_state = %s, physical_zip = %s,
            mailing_street = %s, mailing_city = %s, mailing_state = %s, mailing_zip = %s,
            billing_street = %s, billing_city = %s, billing_state = %s, billing_zip = %s,
            notes = %s, updated_at = NOW()
        WHERE id = %s
    """
    
    try:
        db_execute_query(query, (
            company_data.get('name'),
            company_data.get('website'),
            company_data.get('industry'),
            company_data.get('phone'),
            company_data.get('physical_street'),
            company_data.get('physical_city'),
            company_data.get('physical_state'),
            company_data.get('physical_zip'),
            company_data.get('mailing_street'),
            company_data.get('mailing_city'),
            company_data.get('mailing_state'),
            company_data.get('mailing_zip'),
            company_data.get('billing_street'),
            company_data.get('billing_city'),
            company_data.get('billing_state'),
            company_data.get('billing_zip'),
            company_data.get('notes'),
            company_id
        ))
        invalidate_companies_cache()
        return True
    except Exception as e:
        st.error(f"Error updating company: {str(e)}")
        return False

def delete_company(company_id):
    """Delete a company from the database"""
    if not db_is_connected():
        return False
    
    # Check if company has contacts
    contacts = get_company_contacts(company_id)
    if contacts:
        st.error(f"Cannot delete company with {len(contacts)} contacts. Remove or reassign contacts first.")
        return False
    
    query = "DELETE FROM companies WHERE id = %s"
    
    try:
        db_execute_query(query, (company_id,))
        invalidate_companies_cache()
        return True
    except Exception as e:
        st.error(f"Error deleting company: {str(e)}")
        return False

# ============================================
# SESSION STATE INITIALIZATION
# ============================================
if 'companies_selected' not in st.session_state:
    st.session_state.companies_selected = None

if 'companies_show_new_form' not in st.session_state:
    st.session_state.companies_show_new_form = False

if 'companies_cache_version' not in st.session_state:
    st.session_state.companies_cache_version = 0

# ============================================
# COMPANY FORM COMPONENT
# ============================================
def render_company_form(company=None, form_key="company_form"):
    """Render company creation/edit form"""
    is_edit = company is not None
    title = "Edit Company" if is_edit else "Create New Company"
    
    with st.form(key=form_key, clear_on_submit=not is_edit):
        st.markdown(f"### {title}")
        
        # Basic Information
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Company Name *", 
                               value=company.get('name', '') if is_edit else '',
                               placeholder="e.g., Metro Point Technology")
            
            website = st.text_input("Website", 
                                  value=company.get('website', '') if is_edit else '',
                                  placeholder="https://example.com")
        
        with col2:
            industry = st.text_input("Industry", 
                                   value=company.get('industry', '') if is_edit else '',
                                   placeholder="e.g., Technology Services")
            
            phone = st.text_input("Phone", 
                                value=company.get('phone', '') if is_edit else '',
                                placeholder="(555) 123-4567")
        
        # Addresses Section
        st.markdown("---")
        
        # Physical Address
        with st.expander("📍 Physical Address", expanded=True):
            phys_col1, phys_col2 = st.columns(2)
            
            with phys_col1:
                physical_street = st.text_area("Street Address", 
                                             value=company.get('physical_street', '') if is_edit else '',
                                             height=60)
                physical_city = st.text_input("City", 
                                            value=company.get('physical_city', '') if is_edit else '')
            
            with phys_col2:
                physical_state = st.text_input("State", 
                                             value=company.get('physical_state', '') if is_edit else '')
                physical_zip = st.text_input("ZIP Code", 
                                           value=company.get('physical_zip', '') if is_edit else '')
        
        # Mailing Address
        with st.expander("📬 Mailing Address (if different)", expanded=False):
            mail_col1, mail_col2 = st.columns(2)
            
            with mail_col1:
                mailing_street = st.text_area("Street Address", 
                                            value=company.get('mailing_street', '') if is_edit else '',
                                            height=60)
                mailing_city = st.text_input("City", 
                                           value=company.get('mailing_city', '') if is_edit else '')
            
            with mail_col2:
                mailing_state = st.text_input("State", 
                                            value=company.get('mailing_state', '') if is_edit else '')
                mailing_zip = st.text_input("ZIP Code", 
                                          value=company.get('mailing_zip', '') if is_edit else '')
        
        # Billing Address
        with st.expander("💳 Billing Address (if different)", expanded=False):
            bill_col1, bill_col2 = st.columns(2)
            
            with bill_col1:
                billing_street = st.text_area("Street Address", 
                                            value=company.get('billing_street', '') if is_edit else '',
                                            height=60)
                billing_city = st.text_input("City", 
                                           value=company.get('billing_city', '') if is_edit else '')
            
            with bill_col2:
                billing_state = st.text_input("State", 
                                            value=company.get('billing_state', '') if is_edit else '')
                billing_zip = st.text_input("ZIP Code", 
                                          value=company.get('billing_zip', '') if is_edit else '')
        
        # Notes
        notes = st.text_area("Notes", 
                           value=company.get('notes', '') if is_edit else '',
                           height=100)
        
        # Form buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            submitted = st.form_submit_button("💾 Save Company", type="primary", use_container_width=True)
        
        with col2:
            if st.form_submit_button("❌ Cancel", use_container_width=True):
                st.session_state.companies_show_new_form = False
                st.session_state.companies_selected = None
                st.rerun()
        
        with col3:
            if is_edit and st.form_submit_button("🗑️ Delete", use_container_width=True):
                if delete_company(company['id']):
                    st.success("Company deleted successfully!")
                    st.session_state.companies_selected = None
                    time.sleep(1)
                    st.rerun()
        
        if submitted:
            if not name.strip():
                st.error("Company name is required!")
                return
            
            company_data = {
                'name': name.strip(),
                'website': website.strip() if website.strip() else None,
                'industry': industry.strip() if industry.strip() else None,
                'phone': phone.strip() if phone.strip() else None,
                'physical_street': physical_street.strip() if physical_street.strip() else None,
                'physical_city': physical_city.strip() if physical_city.strip() else None,
                'physical_state': physical_state.strip() if physical_state.strip() else None,
                'physical_zip': physical_zip.strip() if physical_zip.strip() else None,
                'mailing_street': mailing_street.strip() if mailing_street.strip() else None,
                'mailing_city': mailing_city.strip() if mailing_city.strip() else None,
                'mailing_state': mailing_state.strip() if mailing_state.strip() else None,
                'mailing_zip': mailing_zip.strip() if mailing_zip.strip() else None,
                'billing_street': billing_street.strip() if billing_street.strip() else None,
                'billing_city': billing_city.strip() if billing_city.strip() else None,
                'billing_state': billing_state.strip() if billing_state.strip() else None,
                'billing_zip': billing_zip.strip() if billing_zip.strip() else None,
                'notes': notes.strip() if notes.strip() else None
            }
            
            if is_edit:
                if update_company(company['id'], company_data):
                    st.success("Company updated successfully!")
                    time.sleep(1)
                    st.rerun()
            else:
                company_id = create_company(company_data)
                if company_id:
                    st.success("Company created successfully!")
                    st.session_state.companies_show_new_form = False
                    st.session_state.companies_selected = company_id
                    time.sleep(1)
                    st.rerun()

# ============================================
# MAIN PAGE CONTENT
# ============================================
st.title("🏢 Companies")

# Load companies data
cache_key = st.session_state.companies_cache_version
companies = get_companies(_cache_key=cache_key)

# Check if we should show new form or selected company
if st.session_state.companies_show_new_form:
    render_company_form()

elif st.session_state.companies_selected:
    # Show selected company details
    selected_company = next((c for c in companies if c['id'] == st.session_state.companies_selected), None)
    
    if selected_company:
        # Company header
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"## {selected_company['name']}")
            if selected_company.get('industry'):
                st.caption(f"🏭 {selected_company['industry']}")
        
        with col2:
            if st.button("✏️ Edit Company", type="primary", use_container_width=True):
                st.session_state.companies_show_new_form = False
                # Will show edit form below
        
        # Company details in tabs
        tab1, tab2, tab3 = st.tabs(["📋 Details", "📍 Addresses", "👥 Contacts"])
        
        with tab1:
            # Basic company information
            col1, col2 = st.columns(2)
            
            with col1:
                if selected_company.get('website'):
                    st.markdown(f"🌐 **Website:** [{selected_company['website']}]({selected_company['website']})")
                if selected_company.get('phone'):
                    st.markdown(f"📞 **Phone:** {selected_company['phone']}")
            
            with col2:
                if selected_company.get('industry'):
                    st.markdown(f"🏭 **Industry:** {selected_company['industry']}")
                st.markdown(f"📅 **Created:** {str(selected_company.get('created_at', '')).split('T')[0]}")
            
            if selected_company.get('notes'):
                st.markdown("**Notes:**")
                st.markdown(selected_company['notes'])
        
        with tab2:
            # Address information in expandable sections
            addresses = [
                ("📍 Physical Address", "physical"),
                ("📬 Mailing Address", "mailing"), 
                ("💳 Billing Address", "billing")
            ]
            
            for title, prefix in addresses:
                street = selected_company.get(f'{prefix}_street')
                city = selected_company.get(f'{prefix}_city')
                state = selected_company.get(f'{prefix}_state')
                zip_code = selected_company.get(f'{prefix}_zip')
                
                if any([street, city, state, zip_code]):
                    with st.expander(title, expanded=True):
                        if street:
                            st.markdown(f"**Street:** {street}")
                        if city or state or zip_code:
                            location_parts = [p for p in [city, state, zip_code] if p]
                            st.markdown(f"**Location:** {', '.join(location_parts)}")
                else:
                    with st.expander(title, expanded=False):
                        st.caption("No address information")
        
        with tab3:
            # Company contacts
            contacts = get_company_contacts(st.session_state.companies_selected, _cache_key=cache_key)
            
            if contacts:
                st.markdown(f"### {len(contacts)} Contact{'s' if len(contacts) != 1 else ''}")
                
                for contact in contacts:
                    with st.container(border=True):
                        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                        
                        with col1:
                            role_icon = "👑" if contact.get('role') == "Owner" else "💼" 
                            st.markdown(f"**{role_icon} {contact['first_name']} {contact['last_name']}**")
                            if contact.get('role'):
                                st.caption(f"Role: {contact['role']}")
                        
                        with col2:
                            if contact.get('email'):
                                st.markdown(f"📧 {contact['email']}")
                            if contact.get('phone'):
                                st.caption(f"📞 {contact['phone']}")
                        
                        with col3:
                            if contact.get('card_image_url'):
                                st.caption("📇 Business card available")
                            created = str(contact.get('created_at', '')).split('T')[0]
                            st.caption(f"Added: {created}")
                        
                        with col4:
                            if st.button("Open", key=f"contact_{contact['id']}"):
                                # Navigate to contacts page with this contact selected
                                st.session_state.selected_contact = contact['id']
                                st.switch_page("pages/02_Contacts.py")
                
            else:
                st.info("No contacts for this company yet.")
                if st.button("➕ Add Contact"):
                    # Navigate to contacts page to add new contact
                    st.switch_page("pages/02_Contacts.py")
        
        # Edit form below if editing
        if st.session_state.companies_selected and not st.session_state.companies_show_new_form:
            st.markdown("---")
            render_company_form(selected_company, f"edit_form_{selected_company['id']}")
    
    else:
        st.error("Selected company not found!")
        st.session_state.companies_selected = None

else:
    # Show companies list
    if not companies:
        st.info("No companies found. Create your first company!")
        if st.button("➕ Create First Company", type="primary"):
            st.session_state.companies_show_new_form = True
            st.rerun()
    else:
        # Toolbar
        toolbar_col1, toolbar_col2, toolbar_col3 = st.columns([2, 1, 1])

        with toolbar_col1:
            search = st.text_input("🔍 Search companies...", placeholder="Company name, industry, city", label_visibility="collapsed")

        with toolbar_col2:
            if st.button("🔄 Refresh", use_container_width=True):
                invalidate_companies_cache()
                st.rerun()

        with toolbar_col3:
            if st.button("➕ New Company", type="primary", use_container_width=True):
                st.session_state.companies_show_new_form = True
                st.session_state.companies_selected = None
                st.rerun()

        # Filter companies
        filtered_companies = companies

        if search:
            search_lower = search.lower()
            filtered_companies = [c for c in filtered_companies if
                search_lower in (c.get('name') or '').lower() or
                search_lower in (c.get('industry') or '').lower() or
                search_lower in (c.get('physical_city') or '').lower()]

        # Companies list
        st.markdown(f"### {len(filtered_companies)} Companies")

        for company in filtered_companies:
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

                with col1:
                    st.markdown(f"**🏢 {company['name']}**")
                    if company.get('industry'):
                        st.caption(f"🏭 {company['industry']}")

                with col2:
                    if company.get('website'):
                        st.markdown(f"🌐 [Website]({company['website']})")
                    if company.get('phone'):
                        st.caption(f"📞 {company['phone']}")

                with col3:
                    # Get contact count
                    contact_count = len(get_company_contacts(company['id'], _cache_key=cache_key))
                    st.markdown(f"👥 {contact_count} contact{'s' if contact_count != 1 else ''}")
                    
                    if company.get('physical_city'):
                        location_parts = [p for p in [company.get('physical_city'), company.get('physical_state')] if p]
                        st.caption(f"📍 {', '.join(location_parts)}")

                with col4:
                    if st.button("Open", key=f"open_{company['id']}"):
                        st.session_state.companies_selected = company['id']
                        st.rerun()

# Show page load time in sidebar (for debugging)
_page_load_time = time.time() - _page_load_start
st.sidebar.caption(f"⏱️ Page load: {_page_load_time:.2f}s")