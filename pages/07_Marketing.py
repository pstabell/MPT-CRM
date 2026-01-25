"""
MPT-CRM Marketing Page
Drip campaigns, email templates, and SendGrid integration
"""

import streamlit as st
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.navigation import render_sidebar, render_sidebar_stats

st.set_page_config(
    page_title="MPT-CRM - Marketing",
    page_icon="📧",
    layout="wide"
)

# Render shared sidebar (includes all styling)
render_sidebar("Marketing")

# Initialize session state for campaigns
if 'campaigns' not in st.session_state:
    st.session_state.campaigns = [
        {
            "id": "camp-1",
            "name": "New Networking Contact",
            "type": "drip",
            "status": "active",
            "trigger": "Contact added with type=Networking",
            "target_types": ["networking"],
            "emails": [
                {"day": 0, "subject": "Great meeting you at {{event_name}}!", "status": "active"},
                {"day": 3, "subject": "Quick tip: Streamline your business operations", "status": "active"},
                {"day": 7, "subject": "Let's grab coffee", "status": "active"},
                {"day": 21, "subject": "Staying in touch", "status": "active"},
            ],
            "enrollments": 12,
            "sent": 38,
            "opened": 28,
            "clicked": 8,
            "created_at": "2026-01-15"
        },
        {
            "id": "camp-2",
            "name": "Proposal Follow-up",
            "type": "drip",
            "status": "active",
            "trigger": "Deal moves to Proposal stage",
            "target_types": ["lead"],
            "emails": [
                {"day": 2, "subject": "Following up on your proposal", "status": "active"},
                {"day": 5, "subject": "Why clients choose Metro Point Technology", "status": "active"},
                {"day": 10, "subject": "Checking in on your decision", "status": "active"},
                {"day": 14, "subject": "Final thoughts on your project", "status": "active"},
            ],
            "enrollments": 5,
            "sent": 14,
            "opened": 11,
            "clicked": 4,
            "created_at": "2026-01-10"
        },
        {
            "id": "camp-3",
            "name": "New Client Welcome",
            "type": "drip",
            "status": "active",
            "trigger": "Deal won",
            "target_types": ["client"],
            "emails": [
                {"day": 0, "subject": "Welcome to Metro Point Technology!", "status": "active"},
                {"day": 3, "subject": "Getting started with your project", "status": "active"},
                {"day": 7, "subject": "First week check-in", "status": "active"},
                {"day": 30, "subject": "One month milestone", "status": "active"},
                {"day": 90, "subject": "We'd love your feedback!", "status": "active"},
            ],
            "enrollments": 3,
            "sent": 8,
            "opened": 8,
            "clicked": 2,
            "created_at": "2026-01-05"
        },
        {
            "id": "camp-4",
            "name": "Lost Deal Re-engagement",
            "type": "drip",
            "status": "paused",
            "trigger": "Deal lost (30 days after)",
            "target_types": ["prospect"],
            "emails": [
                {"day": 0, "subject": "Circumstances change - let's reconnect", "status": "active"},
                {"day": 30, "subject": "New case study: How we helped {{industry}} company", "status": "active"},
                {"day": 60, "subject": "Quick question about your project", "status": "active"},
            ],
            "enrollments": 2,
            "sent": 3,
            "opened": 1,
            "clicked": 0,
            "created_at": "2026-01-08"
        },
        {
            "id": "camp-5",
            "name": "Prospect Nurture",
            "type": "drip",
            "status": "draft",
            "trigger": "Manual enrollment",
            "target_types": ["prospect", "networking"],
            "emails": [
                {"day": 0, "subject": "5 ways to automate your business", "status": "draft"},
                {"day": 14, "subject": "Client spotlight: Insurance agency transformation", "status": "draft"},
                {"day": 28, "subject": "Is your software holding you back?", "status": "draft"},
            ],
            "enrollments": 0,
            "sent": 0,
            "opened": 0,
            "clicked": 0,
            "created_at": "2026-01-20"
        },
    ]

if 'email_templates' not in st.session_state:
    st.session_state.email_templates = [
        {
            "id": "tmpl-1",
            "name": "Networking Follow-Up - New Contact",
            "category": "follow_up",
            "subject": "Great meeting you at {{event_name}}",
            "body": """Hi {{first_name}},

It was great meeting you at {{event_name}} today. I enjoyed learning about {{conversation_topic}}.

I'm the owner of Metro Point Technology - we build custom software and web applications for businesses, with a focus on the insurance industry. If you ever need help streamlining operations with technology, I'd be happy to chat.

Would you like to grab coffee sometime and continue the conversation?

Best,
Patrick
Metro Point Technology, LLC
{{your_phone}}
{{your_email}}
{{your_website}}

{{unsubscribe_link}}""",
            "merge_fields": ["first_name", "event_name", "conversation_topic", "your_phone", "your_email", "your_website", "unsubscribe_link"],
            "tips": "Send within 24 hours of meeting. Reference something specific you discussed. Keep it short and personal."
        },
        {
            "id": "tmpl-2",
            "name": "Networking Follow-Up - Reconnection",
            "category": "follow_up",
            "subject": "Good seeing you again at {{event_name}}",
            "body": """Hi {{first_name}},

It was good seeing you again at {{event_name}} today. Always nice to catch up with familiar faces.

{{optional_reference}}

Quick update on my end - I recently launched Metro Point Technology, a custom software and web development company. We're focused on helping businesses (especially in the insurance space) automate and streamline their operations.

If you know anyone who could use help with software, websites, or business automation, I'd appreciate the referral. And if there's anything I can do for you, just let me know.

Let's grab lunch soon and catch up properly.

Best,
Patrick
Metro Point Technology, LLC
{{your_phone}}
{{your_email}}
{{your_website}}

{{unsubscribe_link}}""",
            "merge_fields": ["first_name", "event_name", "optional_reference", "your_phone", "your_email", "your_website", "unsubscribe_link"],
            "tips": "Acknowledge the existing relationship. Share your news briefly. Ask for referrals - warm contacts are great sources."
        },
        {
            "id": "tmpl-3",
            "name": "Networking Follow-Up - Value Add",
            "category": "follow_up",
            "subject": "Quick tip: Streamline your business operations",
            "body": """Hi {{first_name}},

I was thinking about our conversation at {{event_name}} and wanted to share a quick tip that might be helpful.

Many businesses I work with spend hours each week on manual data entry and repetitive tasks. One simple change that makes a big difference: identify your top 3 time-consuming processes and look for automation opportunities.

If you'd like to chat about how technology could help {{company_name}}, I'm always happy to brainstorm ideas - no strings attached.

Best,
Patrick

{{unsubscribe_link}}""",
            "merge_fields": ["first_name", "event_name", "company_name", "unsubscribe_link"],
            "tips": "Send 3-7 days after initial contact. Provide genuine value. Keep the ask soft."
        },
        {
            "id": "tmpl-4",
            "name": "Networking Follow-Up - Coffee Invite",
            "category": "follow_up",
            "subject": "Let's grab coffee",
            "body": """Hi {{first_name}},

I hope you've been well since we met at {{event_name}}.

I'd love to learn more about what you're working on at {{company_name}}. Would you be open to grabbing coffee sometime this week or next?

I'm flexible on time and happy to come to you.

Best,
Patrick
{{your_phone}}

{{unsubscribe_link}}""",
            "merge_fields": ["first_name", "event_name", "company_name", "your_phone", "unsubscribe_link"],
            "tips": "Send 7-14 days after initial contact. Be specific about timing. Offer to make it easy for them."
        },
        {
            "id": "tmpl-5",
            "name": "New Client Welcome",
            "category": "welcome",
            "subject": "Welcome to Metro Point Technology!",
            "body": """Hi {{first_name}},

Welcome to Metro Point Technology! I'm thrilled to be working with {{company_name}} on {{deal_title}}.

Here's what you can expect:

1. **Kickoff Call**: We'll schedule a call this week to align on goals and timeline
2. **Communication**: I'll send weekly progress updates every Friday
3. **Access**: You'll have direct access to me via email, phone, or our project portal

If you have any questions before we get started, don't hesitate to reach out.

Looking forward to building something great together!

Best,
Patrick
{{your_phone}}
{{your_email}}

{{unsubscribe_link}}""",
            "merge_fields": ["first_name", "company_name", "deal_title", "your_phone", "your_email", "unsubscribe_link"],
            "tips": "Send immediately when deal is won. Set clear expectations. Make them feel valued."
        },
        {
            "id": "tmpl-6",
            "name": "Proposal Follow-Up",
            "category": "proposal",
            "subject": "Following up on your proposal",
            "body": """Hi {{first_name}},

I wanted to check in on the proposal I sent for {{deal_title}}.

Have you had a chance to review it? I'm happy to jump on a quick call to walk through any questions or discuss adjustments.

Just let me know what works best for your schedule.

Best,
Patrick
{{your_phone}}

{{unsubscribe_link}}""",
            "merge_fields": ["first_name", "deal_title", "your_phone", "unsubscribe_link"],
            "tips": "Send 2-3 days after proposal. Don't be pushy. Offer to clarify."
        },
    ]

if 'selected_campaign' not in st.session_state:
    st.session_state.selected_campaign = None

if 'selected_template' not in st.session_state:
    st.session_state.selected_template = None


def show_campaign_detail(campaign_id):
    """Show full campaign detail with email sequence"""
    campaign = next((c for c in st.session_state.campaigns if c['id'] == campaign_id), None)
    if not campaign:
        return

    col1, col2 = st.columns([3, 1])
    with col1:
        status_icon = {"active": "🟢", "paused": "🟡", "draft": "⚪", "completed": "✅"}.get(campaign['status'], "⚪")
        st.markdown(f"## {status_icon} {campaign['name']}")
    with col2:
        if st.button("← Back to Campaigns"):
            st.session_state.selected_campaign = None
            st.rerun()

    st.markdown("---")

    # Campaign info and stats
    info_col, stats_col = st.columns([2, 1])

    with info_col:
        st.markdown("### Campaign Settings")

        # Status toggle
        status_options = ["active", "paused", "draft"]
        status_labels = ["🟢 Active", "🟡 Paused", "⚪ Draft"]
        current_idx = status_options.index(campaign['status']) if campaign['status'] in status_options else 0
        new_status_label = st.selectbox("Status", status_labels, index=current_idx)
        campaign['status'] = status_options[status_labels.index(new_status_label)]

        st.markdown(f"**Trigger:** {campaign['trigger']}")
        st.markdown(f"**Target Types:** {', '.join(campaign['target_types'])}")
        st.markdown(f"**Created:** {campaign['created_at']}")

    with stats_col:
        st.markdown("### Performance")
        st.metric("Enrolled", campaign['enrollments'])
        st.metric("Emails Sent", campaign['sent'])

        if campaign['sent'] > 0:
            open_rate = (campaign['opened'] / campaign['sent']) * 100
            click_rate = (campaign['clicked'] / campaign['sent']) * 100
            st.metric("Open Rate", f"{open_rate:.0f}%")
            st.metric("Click Rate", f"{click_rate:.0f}%")

    # Email sequence
    st.markdown("---")
    st.markdown("### 📧 Email Sequence")

    for i, email in enumerate(campaign['emails']):
        with st.container(border=True):
            col1, col2, col3 = st.columns([1, 4, 1])

            with col1:
                if email['day'] == 0:
                    st.markdown("**Day 0**")
                    st.caption("(Trigger)")
                else:
                    st.markdown(f"**Day {email['day']}**")
                    st.caption(f"+{email['day']} days")

            with col2:
                st.markdown(f"**{email['subject']}**")
                if st.button("Edit Email", key=f"edit_email_{i}"):
                    st.toast("Email editor coming soon!")

            with col3:
                status_badge = {"active": "🟢", "draft": "⚪", "paused": "🟡"}.get(email['status'], "⚪")
                st.markdown(f"{status_badge} {email['status'].title()}")

    # Add email button
    if st.button("➕ Add Email to Sequence"):
        st.toast("Email builder coming soon!")

    # Enrollments section
    st.markdown("---")
    st.markdown("### 👥 Current Enrollments")

    if campaign['enrollments'] > 0:
        st.info(f"📊 {campaign['enrollments']} contacts currently enrolled in this campaign")
        if st.button("View All Enrollments"):
            st.toast("Enrollment list coming soon!")
    else:
        st.warning("No contacts enrolled yet.")

    if st.button("➕ Manually Enroll Contacts"):
        st.toast("Manual enrollment coming soon!")


def show_template_detail(template_id):
    """Show and edit email template"""
    template = next((t for t in st.session_state.email_templates if t['id'] == template_id), None)
    if not template:
        return

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"## ✉️ {template['name']}")
    with col2:
        if st.button("← Back to Templates"):
            st.session_state.selected_template = None
            st.rerun()

    st.markdown("---")

    # Template editor
    col1, col2 = st.columns([2, 1])

    with col1:
        new_name = st.text_input("Template Name", template['name'])
        new_subject = st.text_input("Subject Line", template['subject'])
        new_body = st.text_area("Email Body", template['body'], height=400)

        if new_name != template['name'] or new_subject != template['subject'] or new_body != template['body']:
            template['name'] = new_name
            template['subject'] = new_subject
            template['body'] = new_body

        if st.button("💾 Save Template", type="primary"):
            st.success("Template saved!")

        # Send Test Email section
        st.markdown("---")
        st.markdown("### 📤 Send Test Email")
        test_email = st.text_input("Send test to:", value="patrick@metropointtechnology.com", key="test_email_addr")
        test_first_name = st.text_input("Test first name:", value="Patrick", key="test_first_name")

        if st.button("📧 Send Test Email", type="secondary"):
            try:
                from services.email_service import email_service

                if email_service.is_configured:
                    # Prepare merge data
                    merge_data = {
                        "first_name": test_first_name,
                        "last_name": "Test",
                        "company_name": "Test Company",
                        "event_name": "Test Event",
                        "conversation_topic": "your business",
                        "deal_title": "Test Project",
                    }

                    result = email_service.send_template_email(
                        to_email=test_email,
                        to_name=test_first_name,
                        template_subject=template['subject'],
                        template_body=template['body'],
                        merge_data=merge_data
                    )

                    if result['success']:
                        st.success(f"✅ Test email sent to {test_email}!")
                    else:
                        st.error(f"❌ Failed: {result.get('error', 'Unknown error')}")
                else:
                    st.error("SendGrid not configured. Check your .env file.")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    with col2:
        st.markdown("### 🔗 Merge Fields")
        st.caption("Click to copy")

        merge_fields = [
            ("{{first_name}}", "Contact's first name"),
            ("{{last_name}}", "Contact's last name"),
            ("{{company_name}}", "Company name"),
            ("{{event_name}}", "Event/source detail"),
            ("{{deal_title}}", "Deal/project name"),
            ("{{your_name}}", "Your name"),
            ("{{your_phone}}", "Your phone"),
            ("{{your_email}}", "Your email"),
            ("{{calendar_link}}", "Scheduling link"),
            ("{{unsubscribe_link}}", "Unsubscribe link"),
        ]

        for field, description in merge_fields:
            st.code(field)
            st.caption(description)

        st.markdown("---")
        st.markdown("### 📂 Category")
        categories = ["follow_up", "welcome", "proposal", "nurture", "re_engagement"]
        cat_labels = ["Follow-up", "Welcome", "Proposal", "Nurture", "Re-engagement"]
        current_idx = categories.index(template['category']) if template['category'] in categories else 0
        new_cat_label = st.selectbox("Category", cat_labels, index=current_idx)
        template['category'] = categories[cat_labels.index(new_cat_label)]

        # Show tips if available
        if template.get('tips'):
            st.markdown("---")
            st.markdown("### 💡 Tips")
            st.info(template['tips'])


# Main page
st.title("📧 Marketing")

# Show detail views if selected
if st.session_state.selected_campaign:
    show_campaign_detail(st.session_state.selected_campaign)
elif st.session_state.selected_template:
    show_template_detail(st.session_state.selected_template)
else:
    # Tab navigation
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "🔄 Campaigns", "✉️ Templates", "⚙️ Settings"])

    with tab1:
        # Marketing Dashboard
        st.markdown("### Campaign Performance Overview")

        # Stats row
        stat_cols = st.columns(4)

        total_sent = sum(c['sent'] for c in st.session_state.campaigns)
        total_opened = sum(c['opened'] for c in st.session_state.campaigns)
        total_clicked = sum(c['clicked'] for c in st.session_state.campaigns)
        active_campaigns = len([c for c in st.session_state.campaigns if c['status'] == 'active'])

        with stat_cols[0]:
            st.metric("Active Campaigns", active_campaigns)
        with stat_cols[1]:
            st.metric("Emails Sent (All Time)", total_sent)
        with stat_cols[2]:
            if total_sent > 0:
                st.metric("Avg Open Rate", f"{(total_opened/total_sent)*100:.0f}%")
            else:
                st.metric("Avg Open Rate", "0%")
        with stat_cols[3]:
            if total_sent > 0:
                st.metric("Avg Click Rate", f"{(total_clicked/total_sent)*100:.0f}%")
            else:
                st.metric("Avg Click Rate", "0%")

        st.markdown("---")

        # Recent activity
        st.markdown("### 📬 Recent Email Activity")
        st.info("📊 SendGrid integration will show real-time email activity here (opens, clicks, bounces)")

        # Quick actions
        st.markdown("### ⚡ Quick Actions")
        action_cols = st.columns(3)
        with action_cols[0]:
            if st.button("📧 Send One-Time Email", use_container_width=True):
                st.toast("One-time email sender coming soon!")
        with action_cols[1]:
            if st.button("👥 Enroll Contacts", use_container_width=True):
                st.toast("Bulk enrollment coming soon!")
        with action_cols[2]:
            if st.button("📈 View Full Reports", use_container_width=True):
                st.toast("Detailed reports coming soon!")

    with tab2:
        # Campaigns list
        st.markdown("### 🔄 Drip Campaigns")

        toolbar_col1, toolbar_col2 = st.columns([3, 1])
        with toolbar_col2:
            if st.button("➕ New Campaign", type="primary"):
                st.toast("Campaign builder coming soon!")

        for campaign in st.session_state.campaigns:
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

                status_icon = {"active": "🟢", "paused": "🟡", "draft": "⚪", "completed": "✅"}.get(campaign['status'], "⚪")

                with col1:
                    st.markdown(f"**{status_icon} {campaign['name']}**")
                    st.caption(f"Trigger: {campaign['trigger']}")

                with col2:
                    st.markdown(f"📧 {len(campaign['emails'])} emails")
                    st.caption(f"👥 {campaign['enrollments']} enrolled")

                with col3:
                    if campaign['sent'] > 0:
                        open_rate = (campaign['opened'] / campaign['sent']) * 100
                        st.markdown(f"📬 {campaign['sent']} sent")
                        st.caption(f"📖 {open_rate:.0f}% open rate")
                    else:
                        st.markdown("📬 0 sent")
                        st.caption("No data yet")

                with col4:
                    if st.button("Edit", key=f"edit_camp_{campaign['id']}"):
                        st.session_state.selected_campaign = campaign['id']
                        st.rerun()

    with tab3:
        # Email templates
        st.markdown("### ✉️ Email Templates")

        toolbar_col1, toolbar_col2 = st.columns([3, 1])
        with toolbar_col2:
            if st.button("➕ New Template", type="primary"):
                st.toast("Template builder coming soon!")

        # Group by category
        categories = {}
        for template in st.session_state.email_templates:
            cat = template['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(template)

        cat_labels = {
            "follow_up": "📞 Follow-up",
            "welcome": "👋 Welcome",
            "proposal": "📝 Proposal",
            "nurture": "🌱 Nurture",
            "re_engagement": "🔄 Re-engagement"
        }

        for cat, templates in categories.items():
            st.markdown(f"#### {cat_labels.get(cat, cat.title())}")

            for template in templates:
                with st.container(border=True):
                    col1, col2 = st.columns([4, 1])

                    with col1:
                        st.markdown(f"**{template['name']}**")
                        st.caption(f"Subject: {template['subject']}")

                    with col2:
                        if st.button("Edit", key=f"edit_tmpl_{template['id']}"):
                            st.session_state.selected_template = template['id']
                            st.rerun()

    with tab4:
        # SendGrid settings
        st.markdown("### ⚙️ SendGrid Configuration")

        st.markdown("#### API Settings")
        api_key = st.text_input("SendGrid API Key", type="password", placeholder="SG.xxxxxxxxxxxx")
        st.caption("Get your API key from [SendGrid Dashboard](https://app.sendgrid.com/settings/api_keys)")

        st.markdown("#### Sender Settings")
        sender_email = st.text_input("Sender Email", value="patrick@metropointtechnology.com")
        sender_name = st.text_input("Sender Name", value="Patrick - Metro Point Technology")

        st.markdown("#### Tracking Settings")
        track_opens = st.checkbox("Track email opens", value=True)
        track_clicks = st.checkbox("Track link clicks", value=True)

        st.markdown("#### Unsubscribe Settings")
        unsubscribe_text = st.text_area(
            "Unsubscribe footer text",
            value="You're receiving this because you connected with Metro Point Technology. [Unsubscribe]({{unsubscribe_link}})"
        )

        if st.button("💾 Save Settings", type="primary"):
            st.success("Settings saved! (Note: Full SendGrid integration coming in Phase 4)")

        st.markdown("---")
        st.markdown("#### 📡 Webhook Status")
        st.warning("⚠️ Webhook not configured. Set up webhook URL in SendGrid to receive open/click/bounce events.")
        st.code("Webhook URL: https://your-app-url.com/api/sendgrid/webhook")
