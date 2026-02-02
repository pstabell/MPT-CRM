"""
MPT-CRM Help System
Contextual help buttons ("?" coins) with inline documentation.
"""

import streamlit as st

# ============================================
# HELP COIN STYLING
# ============================================
HELP_COIN_CSS = """
<style>
    .help-coin {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        background: linear-gradient(135deg, #FFD700, #FFA500);
        color: #1a1a2e;
        font-weight: bold;
        font-size: 14px;
        cursor: pointer;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3), inset 0 1px 2px rgba(255,255,255,0.4);
        border: 1.5px solid #DAA520;
        vertical-align: middle;
        margin-left: 8px;
        text-decoration: none;
        user-select: none;
    }
    .help-coin:hover {
        background: linear-gradient(135deg, #FFE44D, #FFB733);
        box-shadow: 0 2px 8px rgba(255, 215, 0, 0.5), inset 0 1px 2px rgba(255,255,255,0.4);
        transform: scale(1.1);
    }
    .section-header-with-help {
        display: flex;
        align-items: center;
        gap: 0;
    }
</style>
"""


def inject_help_styles():
    """Call once per page to inject the help coin CSS."""
    st.markdown(HELP_COIN_CSS, unsafe_allow_html=True)


def help_header(title: str, help_key: str, level: str = "###"):
    """
    Render a section header with a yellow help coin button.
    Uses st.popover for the help content.
    
    Args:
        title: Section title text (e.g., "Company Information")
        help_key: Key to look up help content
        level: Markdown heading level (default "###")
    """
    cols = st.columns([0.92, 0.08])
    with cols[0]:
        st.markdown(f"{level} {title}")
    with cols[1]:
        help_content = HELP_CONTENT.get(help_key)
        if help_content:
            with st.popover("🪙"):
                st.markdown(f"**{help_content['title']}**")
                st.markdown(help_content['body'])
                if help_content.get('tips'):
                    st.markdown("---")
                    st.markdown("💡 **Tips:**")
                    for tip in help_content['tips']:
                        st.markdown(f"- {tip}")


def help_coin_inline(help_key: str):
    """
    Render a standalone help coin (not attached to a header).
    Good for placing next to specific fields or elements.
    """
    help_content = HELP_CONTENT.get(help_key)
    if help_content:
        with st.popover("🪙"):
            st.markdown(f"**{help_content['title']}**")
            st.markdown(help_content['body'])
            if help_content.get('tips'):
                st.markdown("---")
                st.markdown("💡 **Tips:**")
                for tip in help_content['tips']:
                    st.markdown(f"- {tip}")


# ============================================
# HELP CONTENT LIBRARY
# ============================================
HELP_CONTENT = {
    # --- SETTINGS PAGE ---
    "company_info": {
        "title": "📋 Company Information",
        "body": """
Your company profile used across the CRM — on invoices, emails, reports, and client-facing documents.

**Fields:**
- **Company Name** — Your registered business name
- **Owner Name** — Primary contact / owner
- **Email** — Default business email for correspondence
- **Phone** — Main business phone number
- **Address** — Registered business address
- **Website** — Your company website URL
        """,
        "tips": [
            "This info appears on all generated invoices",
            "Update here to change it everywhere at once",
        ],
    },

    "integrations": {
        "title": "🔗 Integrations Overview",
        "body": """
Connect external services to extend the CRM's capabilities.

**Available Integrations:**

🗄️ **Supabase** — Cloud database for persistent data storage. Without it, data lives only in your browser session.

📧 **SendGrid** — Email delivery service for sending marketing campaigns, invoices, and notifications from the CRM.

📅 **Microsoft 365** — Calendar, email, tasks, planner, and contacts sync via Microsoft Graph API, managed by Metro Bot.
        """,
        "tips": [
            "Supabase is required for data to persist between sessions",
            "SendGrid requires a verified sender email",
            "M365 integration is managed through Metro Bot on Teams",
        ],
    },

    "supabase": {
        "title": "🗄️ Supabase (Database)",
        "body": """
Supabase provides the cloud PostgreSQL database that stores all your CRM data — contacts, deals, tasks, invoices, and more.

**Status indicators:**
- ✅ **Connected** — Database is active and storing data
- ⚠️ **Not connected** — Data only exists in browser session (lost on refresh)

**To connect:** Enter your Supabase project URL and anon key from your Supabase dashboard → Settings → API.
        """,
        "tips": [
            "Get your credentials at app.supabase.com → Project → Settings → API",
            "The anon key is safe to use client-side",
            "Use 'Test Connection' to verify it's working",
        ],
    },

    "sendgrid": {
        "title": "📧 SendGrid (Email)",
        "body": """
SendGrid handles outbound email delivery — marketing campaigns, invoice emails, follow-up sequences, and notifications.

**To connect:**
1. Create a free account at sendgrid.com
2. Go to Settings → API Keys → Create API Key
3. Give it "Full Access" or at minimum "Mail Send"
4. Paste the key here (starts with `SG.`)

**From Email** — The verified sender address (must be verified in SendGrid)
**From Name** — Display name recipients see
        """,
        "tips": [
            "Free tier: 100 emails/day",
            "Verify your sender email in SendGrid first",
            "API key is shown only once — save it securely",
        ],
    },

    "microsoft_365": {
        "title": "📅 Microsoft 365 Integration",
        "body": """
The M365 integration connects your CRM to Microsoft's ecosystem through the Graph API.

**How it works:** Metro Bot (Clawdbot) authenticates with Microsoft Graph using OAuth tokens and bridges the connection. All M365 operations go through the bot.

**Active services:**
- **📧 Email** — Send/receive via Support@MetroPointTech.com
- **📅 Calendar** — Read/write Outlook calendar events, sync appointments
- **📋 Planner** — Create/manage tasks on MPT Mission Control board
- **✅ Tasks** — Microsoft To-Do integration for personal task lists
- **👥 Contacts** — Directory access for contact sync

**Management:** Configuration changes are made through Metro Bot on Teams — just ask!
        """,
        "tips": [
            "Chat with Metro Bot on Teams to manage M365 settings",
            "Calendar sync is bidirectional — changes flow both ways",
            "Planner is for business tasks; To-Do is for personal tasks",
        ],
    },

    "billing": {
        "title": "💰 Billing & Invoicing",
        "body": """
Configure how invoices are generated and what defaults to use.

**Fields:**
- **Default Hourly Rate** — Pre-filled rate for new time entries
- **Tax Rate** — Applied to invoice subtotals (set 0% if tax-exempt)
- **Invoice Prefix** — Appears before invoice numbers (e.g., INV-2026-001)
- **Payment Due Days** — Default net terms (e.g., Net 30)

The preview below shows how invoices will look with current settings.
        """,
        "tips": [
            "You can override the rate on individual time entries",
            "Invoice numbering is automatic and sequential",
            "Tax rate can be overridden per invoice if needed",
        ],
    },

    "email_settings": {
        "title": "📧 Email Settings",
        "body": """
Configure how outbound emails behave.

**Email Signature** — Appended to all outgoing emails. Supports plain text formatting.

**Tracking:**
- **Track Opens** — Know when recipients open your emails
- **Track Clicks** — Know when recipients click links in your emails

**Options:**
- **BCC Yourself** — Get a copy of every email sent from the CRM
- **Daily Summary** — Receive a daily digest of CRM email activity
        """,
        "tips": [
            "Open tracking uses a tiny invisible pixel",
            "Some email clients block tracking pixels",
            "BCC copies go to your configured business email",
        ],
    },

    "danger_zone": {
        "title": "⚠️ Danger Zone",
        "body": """
Data management tools — use with caution!

**Export All Data** — Downloads a complete JSON backup of all CRM tables (contacts, deals, tasks, invoices, etc.). Good for backups or migration.

**Clear Session Data** — Removes all data from your current browser session. If connected to Supabase, a page refresh will reload from the database. If NOT connected to Supabase, **data will be permanently lost**.
        """,
        "tips": [
            "Export regularly as a backup",
            "Clearing session data does NOT delete from Supabase",
            "Always export before making major changes",
        ],
    },

    "security": {
        "title": "🔐 Password & Security",
        "body": """
Manage your CRM login credentials and security settings.

**Change Password** — Update your login password. Requires your current password for verification.

**Forgot Password** — Reset codes are sent to the configured admin email address. Only one admin email can receive reset codes.

**Passkeys** — If you've set up Microsoft passkeys, those are for your M365 account (separate from CRM login).
        """,
        "tips": [
            "Use a strong, unique password",
            "Admin email is set via ADMIN_EMAIL environment variable",
            "CRM passwords are stored securely with bcrypt hashing",
        ],
    },

    # --- DASHBOARD ---
    "dashboard": {
        "title": "📊 Dashboard Overview",
        "body": """
Your CRM command center — see key metrics, recent activity, and quick actions at a glance.

**Metrics** show real-time counts of contacts, active deals, pipeline value, and tasks.

**Recent Activity** displays the latest changes across the CRM.
        """,
        "tips": [
            "Click any metric to jump to that section",
            "Dashboard refreshes automatically on each visit",
        ],
    },

    # --- CONTACTS ---
    "contacts": {
        "title": "👥 Contacts",
        "body": """
Your central contact database — clients, leads, vendors, and partners.

**Features:**
- Add/edit contacts with full details
- Business card scanner (OCR)
- Link contacts to deals and projects
- Search and filter
- Import/export capabilities
        """,
        "tips": [
            "Use the business card scanner to quickly add new contacts",
            "Tags help organize contacts into groups",
            "Linked deals show on the contact detail page",
        ],
    },

    # --- PIPELINE ---
    "pipeline": {
        "title": "🎯 Sales Pipeline",
        "body": """
Visual deal tracking from lead to close.

**Stages:** Lead → Qualified → Proposal → Negotiation → Closed Won / Lost

Each deal card shows the client, value, and expected close date. Drag deals between stages or click to edit.
        """,
        "tips": [
            "Keep deal values updated for accurate forecasting",
            "Set expected close dates for pipeline reports",
            "Mark lost deals with a reason to track patterns",
        ],
    },
}
