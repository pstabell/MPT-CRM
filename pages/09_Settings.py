"""
MPT-CRM Settings Page
Configure integrations, user preferences, and system settings
"""

import streamlit as st
import os
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.navigation import render_sidebar

st.set_page_config(
    page_title="MPT-CRM - Settings",
    page_icon="⚙️",
    layout="wide"
)

# Render shared sidebar
render_sidebar("Settings")

# Initialize settings in session state
if 'settings' not in st.session_state:
    st.session_state.settings = {
        "company_name": "Metro Point Technology, LLC",
        "owner_name": "Patrick Stabell",
        "email": "patrick@metropointtechnology.com",
        "phone": "(239) 600-8159",
        "address": "4021 NE 8th Place, Cape Coral, FL 33909",
        "website": "www.MetroPointTechnology.com",
        "default_hourly_rate": 150,
        "tax_rate": 0,
        "invoice_prefix": "INV",
        "invoice_due_days": 30,
        "supabase_connected": False,
        "sendgrid_connected": False,
    }

# Main page
st.title("⚙️ Settings")

# Tabs for different settings sections
tab1, tab2, tab3, tab4 = st.tabs(["🏢 Company", "🔗 Integrations", "💰 Billing", "📧 Email"])

# ============================================
# COMPANY SETTINGS TAB
# ============================================
with tab1:
    st.markdown("### Company Information")

    settings = st.session_state.settings

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
    st.markdown("### Integrations")

    # Supabase
    st.markdown("#### 🗄️ Supabase (Database)")

    with st.container(border=True):
        if settings['supabase_connected']:
            st.success("✅ Connected to Supabase")
            if st.button("Disconnect Supabase"):
                settings['supabase_connected'] = False
                st.rerun()
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
    st.markdown("#### 📧 SendGrid (Email)")

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

    # Microsoft Graph (Future)
    st.markdown("#### 📅 Microsoft 365 (Coming Soon)")

    with st.container(border=True):
        st.info("🔜 Microsoft Graph integration will enable:")
        st.markdown("""
        - Sync contacts with Outlook
        - Sync deals with Microsoft Planner
        - Calendar integration for meetings
        - Send emails via Outlook
        """)

# ============================================
# BILLING SETTINGS TAB
# ============================================
with tab3:
    st.markdown("### Billing & Invoicing")

    col1, col2 = st.columns(2)

    with col1:
        new_rate = st.number_input("Default Hourly Rate ($)", value=settings['default_hourly_rate'], min_value=0, step=25)
        new_tax = st.number_input("Tax Rate (%)", value=settings['tax_rate'], min_value=0.0, max_value=100.0, step=0.5)

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
    st.markdown("### Email Settings")

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
    st.markdown("### Data Management")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Export Data**")
        if st.button("📥 Export All Data (JSON)"):
            st.toast("Export feature coming soon!")

    with col2:
        st.markdown("**Reset Data**")
        if st.button("🗑️ Clear All Session Data", type="secondary"):
            for key in ['contacts', 'deals', 'projects', 'tasks', 'time_entries', 'invoices', 'email_templates', 'email_campaigns']:
                if key in st.session_state:
                    del st.session_state[key]
            st.warning("Session data cleared. Refresh to reload sample data.")
