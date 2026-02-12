"""
MPT-CRM Settings Page
Configure integrations, user preferences, and system settings

Database operations are handled by db_service.py — the single source of truth.
"""

import streamlit as st
import os
from datetime import datetime
from pathlib import Path
from db_service import db_is_connected, db_test_connection, db_export_all_tables
from sso_auth import require_sso_auth, render_auth_status, render_change_password_form
from help_system import inject_help_styles, help_header, help_coin_inline

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

def render_sidebar(current_page="Settings"):
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

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="MPT-CRM - Settings",
    page_icon="favicon.jpg",
    layout="wide"
)

require_sso_auth(allow_bypass=False)

# ============================================
# RENDER SIDEBAR
# ============================================
render_sidebar("Settings")

# ============================================
# INITIALIZE SESSION STATE
# ============================================
if 'settings_data' not in st.session_state:
    st.session_state.settings_data = {
        "company_name": "Metro Point Technology, LLC",
        "owner_name": "Patrick Stabell",
        "email": "patrick@metropointtechnology.com",
        "phone": "(239) 600-8159",
        "address": "4021 NE 8th Place, Cape Coral, FL 33909",
        "website": "www.MetroPointTechnology.com",
        "default_hourly_rate": 150.0,
        "tax_rate": 0.0,
        "invoice_prefix": "INV",
        "invoice_due_days": 30,
        "supabase_connected": db_is_connected(),
        "sendgrid_connected": False,
    }

# ============================================
# MAIN PAGE
# ============================================
st.title("⚙️ Settings")

# Inject help coin styles
inject_help_styles()

# Top-level tabs
general_tab, security_tab = st.tabs(["General", "Security"])

with general_tab:

    # Tabs for different settings sections
    tab1, tab2, tab3, tab4 = st.tabs(["🏢 Company", "🔗 Integrations", "💰 Billing", "📧 Email"])

    # ============================================
    # COMPANY SETTINGS TAB
    # ============================================
    with tab1:
        help_header("Company Information", "company_info")

        settings = st.session_state.settings_data

        col1, col2 = st.columns(2)

        with col1:
            new_company = st.text_input("Company Name", settings['company_name'])
            new_owner = st.text_input("Owner Name", settings['owner_name'])
            new_email = st.text_input("Email", settings['email'])
            new_phone = st.text_input("Phone", settings['phone'])

        with col2:
            new_address = st.text_area("Address", settings['address'], height=100)
            new_website = st.text_input("Website", settings['website'])

        if st.button("Save Company Settings", type="primary"):
            settings['company_name'] = new_company
            settings['owner_name'] = new_owner
            settings['email'] = new_email
            settings['phone'] = new_phone
            settings['address'] = new_address
            settings['website'] = new_website
            st.success("Company settings saved!")

    # ============================================
    # INTEGRATIONS TAB
    # ============================================
    with tab2:
        help_header("Integrations", "integrations")

        # Supabase
        help_header("🗄️ Supabase (Database)", "supabase", level="####")

        with st.container(border=True):
            if db_is_connected():
                st.success("✅ Connected to Supabase")
                if st.button("Test Connection"):
                    success, message = db_test_connection()
                    if success:
                        st.success("Connection test passed!")
                    else:
                        st.error(f"Connection test failed: {message[:100]}")
            else:
                st.warning("⚠️ Not connected")
                st.markdown("Enter your Supabase credentials to enable persistent data storage.")

                supabase_url = st.text_input("Supabase URL", placeholder="https://xxxxx.supabase.co")
                supabase_key = st.text_input("Supabase Anon Key", type="password", placeholder="eyJ...")

                if st.button("Connect Supabase"):
                    if supabase_url and supabase_key:
                        # Save to .env file
                        env_path = Path(__file__).parent.parent / ".env"
                        with open(env_path, "a") as f:
                            f.write(f"\nSUPABASE_URL={supabase_url}")
                            f.write(f"\nSUPABASE_ANON_KEY={supabase_key}")
                        settings['supabase_connected'] = True
                        st.success("Supabase connected! Restart the app to apply changes.")
                    else:
                        st.error("Please enter both URL and Key")

        st.markdown("---")

        # SendGrid
        help_header("📧 SendGrid (Email)", "sendgrid", level="####")

        with st.container(border=True):
            if settings['sendgrid_connected']:
                st.success("✅ Connected to SendGrid")
                if st.button("Disconnect SendGrid"):
                    settings['sendgrid_connected'] = False
                    st.rerun()
            else:
                st.warning("⚠️ Not connected")
                st.markdown("Enter your SendGrid API key to enable email sending.")

                sendgrid_key = st.text_input("SendGrid API Key", type="password", placeholder="SG.xxxxx...")
                sendgrid_from = st.text_input("From Email", value=settings['email'])
                sendgrid_name = st.text_input("From Name", value=settings['owner_name'])

                if st.button("Connect SendGrid"):
                    if sendgrid_key:
                        # Save to .env file
                        env_path = Path(__file__).parent.parent / ".env"
                        with open(env_path, "a") as f:
                            f.write(f"\nSENDGRID_API_KEY={sendgrid_key}")
                            f.write(f"\nSENDGRID_FROM_EMAIL={sendgrid_from}")
                            f.write(f"\nSENDGRID_FROM_NAME={sendgrid_name}")
                        settings['sendgrid_connected'] = True
                        st.success("SendGrid connected! Restart the app to apply changes.")
                    else:
                        st.error("Please enter an API key")

        st.markdown("---")

        # Microsoft Graph
        help_header("📅 Microsoft 365 Integration", "microsoft_365", level="####")

        with st.container(border=True):
            st.success("✅ Microsoft Graph API is configured via Metro Bot (Clawdbot)")
            st.markdown("""
            **Active Integrations:**
            - ✅ Email — Support@MetroPointTech.com via Graph API
            - ✅ Calendar — Outlook calendar sync (read/write)
            - ✅ Planner — MPT Mission Control board
            - ✅ Tasks — To-Do lists for task tracking
            - ✅ Contacts — Directory access

            **Bot Account:** Support@MetroPointTech.com
            **App:** MetroPointBot (e9ea4d08-1047-4588-bf07-70aa7befa62f)

            *Managed by Metro Bot — changes via Teams chat.*
            """)

    # ============================================
    # BILLING SETTINGS TAB
    # ============================================
    with tab3:
        help_header("Billing & Invoicing", "billing")

        col1, col2 = st.columns(2)

        with col1:
            new_rate = st.number_input("Default Hourly Rate ($)", value=float(settings['default_hourly_rate']), min_value=0.0, step=25.0)
            new_tax = st.number_input("Tax Rate (%)", value=float(settings['tax_rate']), min_value=0.0, max_value=100.0, step=0.5)

        with col2:
            new_prefix = st.text_input("Invoice Number Prefix", value=settings['invoice_prefix'])
            new_due_days = st.number_input("Payment Due (days)", value=settings['invoice_due_days'], min_value=0, max_value=90)

        st.markdown("---")

        st.markdown("#### Invoice Template Preview")

        with st.container(border=True):
            st.markdown(f"""
            **{settings['company_name']}**
            {settings['address']}
            {settings['phone']} | {settings['email']}

            ---

            **Invoice:** {settings['invoice_prefix']}-2026-001
            **Date:** {datetime.now().strftime('%Y-%m-%d')}
            **Due:** Net {settings['invoice_due_days']} days

            ---

            | Description | Hours | Rate | Amount |
            |-------------|-------|------|--------|
            | Development work | 10.0 | ${settings['default_hourly_rate']} | ${10 * settings['default_hourly_rate']:,.0f} |

            **Subtotal:** ${10 * settings['default_hourly_rate']:,.0f}
            **Tax ({settings['tax_rate']}%):** ${10 * settings['default_hourly_rate'] * settings['tax_rate'] / 100:,.0f}
            **Total:** ${10 * settings['default_hourly_rate'] * (1 + settings['tax_rate'] / 100):,.0f}
            """)

        if st.button("Save Billing Settings", type="primary"):
            settings['default_hourly_rate'] = new_rate
            settings['tax_rate'] = new_tax
            settings['invoice_prefix'] = new_prefix
            settings['invoice_due_days'] = new_due_days
            st.success("Billing settings saved!")

    # ============================================
    # EMAIL SETTINGS TAB
    # ============================================
    with tab4:
        help_header("Email Settings", "email_settings")

        st.markdown("#### Default Signature")

        default_signature = f"""Best,
    {settings['owner_name']}
    {settings['company_name']}
    {settings['phone']}
    {settings['email']}
    {settings['website']}"""

        new_signature = st.text_area("Email Signature", value=default_signature, height=150)

        st.markdown("---")

        st.markdown("#### Email Preferences")

        col1, col2 = st.columns(2)

        with col1:
            track_opens = st.checkbox("Track email opens", value=True)
            track_clicks = st.checkbox("Track link clicks", value=True)

        with col2:
            auto_bcc = st.checkbox("BCC yourself on all emails", value=False)
            daily_summary = st.checkbox("Send daily activity summary", value=False)

        st.markdown("---")

        st.markdown("#### Unsubscribe Settings")

        st.text_input("Unsubscribe Link Text", value="Click here to unsubscribe")
        st.caption("This text will appear at the bottom of marketing emails.")

        if st.button("Save Email Settings", type="primary"):
            st.success("Email settings saved!")

    # ============================================
    # DANGER ZONE
    # ============================================
    st.markdown("---")

    with st.expander("⚠️ Danger Zone"):
        help_header("Data Management", "danger_zone")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Export Data**")
            if st.button("📥 Export All Data (JSON)"):
                if db_is_connected():
                    try:
                        import json
                        export = db_export_all_tables()
                        export_json = json.dumps(export, indent=2, default=str)
                        st.download_button(
                            label="📥 Download Export",
                            data=export_json,
                            file_name=f"mpt_crm_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                        st.success(f"✅ Exported {sum(len(v) for v in export.values())} total records")
                    except Exception as e:
                        st.error(f"Export failed: {e}")
                else:
                    st.warning("Database not connected.")

        with col2:
            st.markdown("**Reset Data**")
            if st.button("🗑️ Clear All Session Data", type="secondary"):
                for key in ['contacts', 'pipeline_deals', 'proj_projects', 'tasks_list', 'tb_time_entries', 'tb_invoices', 'mkt_campaigns', 'mkt_email_templates']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.success("Session data cleared. Refresh to reload from database.")

with security_tab:
    help_header("Password & Security", "security")
    render_change_password_form()

    st.markdown("---")

    admin_email = (os.getenv("ADMIN_EMAIL") or os.getenv("SENDGRID_FROM_EMAIL") or "").strip()
    st.markdown("#### Forgot Password Reset Codes")
    if admin_email:
        st.markdown(f"Reset codes are sent to: **{admin_email}**")
    else:
        st.warning("Admin email is not configured. Set ADMIN_EMAIL or SENDGRID_FROM_EMAIL.")
    st.caption("Only the configured admin email can receive password reset codes.")
