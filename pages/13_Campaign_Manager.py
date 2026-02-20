"""
MPT-CRM Campaign Manager & Analytics
Comprehensive drip campaign management and performance analytics

Item #006 - Complete UI: campaign manager and analytics
"""

import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import json
import db_service
from db_service import get_db, db_is_connected
from sso_auth import require_sso_auth
from mobile_styles import inject_mobile_styles

st.set_page_config(
    page_title="MPT-CRM - Campaign Manager",
    page_icon="favicon.jpg",
    layout="wide"
)

require_sso_auth(allow_bypass=True)
inject_mobile_styles()

st.title("📬 Campaign Manager & Analytics")

if not db_is_connected():
    st.error("Database not connected. Check your .env file.")
    st.stop()

# Sidebar navigation
st.sidebar.title("Campaign Manager")
page_mode = st.sidebar.radio("View", [
    "📊 Analytics Dashboard", 
    "📧 Active Campaigns",
    "👥 Enrolled Contacts", 
    "⚙️ Campaign Templates",
    "🔄 Bulk Actions"
])

def get_campaign_analytics():
    """Get comprehensive campaign performance data"""
    db = get_db()
    
    analytics = {
        "total_enrollments": 0,
        "active_enrollments": 0,
        "completed_enrollments": 0,
        "stopped_enrollments": 0,
        "campaigns": {},
        "recent_emails": [],
        "enrollment_trends": []
    }
    
    try:
        # Get enrollment statistics
        enrollments_resp = db.table("campaign_enrollments").select("*").execute()
        enrollments = enrollments_resp.data or []
        
        analytics["total_enrollments"] = len(enrollments)
        
        # Status breakdown
        for enrollment in enrollments:
            status = enrollment.get("status", "unknown")
            if status == "active":
                analytics["active_enrollments"] += 1
            elif status == "completed":
                analytics["completed_enrollments"] += 1
            elif status == "stopped":
                analytics["stopped_enrollments"] += 1
            
            # Campaign breakdown
            campaign_id = enrollment.get("campaign_id", "unknown")
            if campaign_id not in analytics["campaigns"]:
                analytics["campaigns"][campaign_id] = {
                    "total": 0, "active": 0, "completed": 0, "stopped": 0
                }
            analytics["campaigns"][campaign_id]["total"] += 1
            analytics["campaigns"][campaign_id][status] += 1
        
        # Get recent email sends
        emails_resp = db.table("email_sends").select("*").order("sent_at", desc=True).limit(20).execute()
        analytics["recent_emails"] = emails_resp.data or []
        
    except Exception as e:
        st.error(f"Error loading analytics: {e}")
    
    return analytics

def render_analytics_dashboard():
    """Render the main analytics dashboard"""
    st.header("📊 Campaign Analytics Dashboard")
    
    analytics = get_campaign_analytics()
    
    # Key Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Enrollments", 
            analytics["total_enrollments"],
            help="All-time campaign enrollments"
        )
    
    with col2:
        st.metric(
            "Active Campaigns", 
            analytics["active_enrollments"],
            help="Currently running campaigns"
        )
    
    with col3:
        completion_rate = 0
        if analytics["total_enrollments"] > 0:
            completion_rate = round((analytics["completed_enrollments"] / analytics["total_enrollments"]) * 100, 1)
        st.metric(
            "Completion Rate", 
            f"{completion_rate}%",
            help="Percentage of campaigns completed vs stopped"
        )
    
    with col4:
        st.metric(
            "Recent Emails", 
            len(analytics["recent_emails"]),
            help="Emails sent in last 20 sends"
        )
    
    # Campaign Performance Table
    st.subheader("📈 Campaign Performance")
    
    if analytics["campaigns"]:
        campaign_data = []
        for campaign_id, stats in analytics["campaigns"].items():
            # Get campaign display name
            campaign_names = {
                "networking-drip-6week": "🤝 Networking (8 emails)",
                "lead-drip": "🎯 Lead Nurture (6 emails)",
                "prospect-drip": "💼 Prospect (5 emails)",
                "client-drip": "⭐ Client Onboard (4 emails)"
            }
            display_name = campaign_names.get(campaign_id, campaign_id)
            
            completion_rate = 0
            if stats["total"] > 0:
                completion_rate = round((stats["completed"] / stats["total"]) * 100, 1)
            
            campaign_data.append({
                "Campaign": display_name,
                "Total": stats["total"],
                "Active": stats["active"],
                "Completed": stats["completed"],
                "Stopped": stats["stopped"],
                "Completion %": f"{completion_rate}%"
            })
        
        df = pd.DataFrame(campaign_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No campaign data available yet. Enroll some contacts to see analytics!")
    
    # Recent Email Activity
    st.subheader("📧 Recent Email Activity")
    
    if analytics["recent_emails"]:
        email_data = []
        for email in analytics["recent_emails"][:10]:
            sent_at = email.get("sent_at", "")
            if sent_at:
                try:
                    sent_date = datetime.fromisoformat(sent_at.replace('Z', '+00:00')).strftime('%b %d, %I:%M %p')
                except:
                    sent_date = sent_at[:16]
            else:
                sent_date = "Unknown"
            
            email_data.append({
                "Date": sent_date,
                "Subject": email.get("subject", "No subject")[:50],
                "Contact": f"{email.get('to_name', 'Unknown')} <{email.get('to_email', '')}>",
                "Campaign": email.get("campaign_id", "Manual")
            })
        
        df_emails = pd.DataFrame(email_data)
        st.dataframe(df_emails, use_container_width=True, hide_index=True)
    else:
        st.info("No recent email activity.")

def render_active_campaigns():
    """Show all active campaign enrollments"""
    st.header("📧 Active Campaign Enrollments")
    
    db = get_db()
    try:
        # Get active enrollments with contact info
        query = """
        SELECT ce.*, c.first_name, c.last_name, c.email, c.company
        FROM campaign_enrollments ce
        LEFT JOIN contacts c ON ce.contact_id = c.id
        WHERE ce.status = 'active'
        ORDER BY ce.next_email_scheduled ASC
        """
        
        # Note: This would need a proper SQL query function
        # For now, get enrollments and contacts separately
        enrollments_resp = db.table("campaign_enrollments").select("*").eq("status", "active").order("next_email_scheduled").execute()
        active_enrollments = enrollments_resp.data or []
        
        if not active_enrollments:
            st.info("No active campaign enrollments.")
            return
        
        # Get contact details for each enrollment
        enriched_enrollments = []
        for enrollment in active_enrollments:
            contact_id = enrollment.get("contact_id")
            try:
                contact_resp = db.table("contacts").select("*").eq("id", contact_id).single().execute()
                contact = contact_resp.data or {}
                enrollment["contact"] = contact
                enriched_enrollments.append(enrollment)
            except:
                enrollment["contact"] = {"first_name": "Unknown", "last_name": "", "email": "", "company": ""}
                enriched_enrollments.append(enrollment)
        
        # Display active campaigns
        for enrollment in enriched_enrollments:
            contact = enrollment.get("contact", {})
            contact_name = f"{contact.get('first_name', 'Unknown')} {contact.get('last_name', '')}"
            contact_email = contact.get('email', 'No email')
            company = contact.get('company', '')
            
            campaign_names = {
                "networking-drip-6week": "🤝 Networking Follow-up",
                "lead-drip": "🎯 Lead Nurture", 
                "prospect-drip": "💼 Prospect Nurture",
                "client-drip": "⭐ Client Onboarding"
            }
            campaign_display = campaign_names.get(enrollment.get("campaign_id"), enrollment.get("campaign_id", "Unknown"))
            
            next_email = enrollment.get("next_email_scheduled", "None")
            if next_email and next_email != "None":
                try:
                    next_date = datetime.fromisoformat(next_email.replace('Z', '+00:00')).strftime('%b %d, %Y at %I:%M %p')
                    next_display = f"📅 Next: {next_date}"
                except:
                    next_display = f"📅 Next: {next_email}"
            else:
                next_display = "✅ Campaign completed"
            
            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.write(f"**{contact_name}**")
                    if company:
                        st.caption(f"{company}")
                    st.caption(f"📧 {contact_email}")
                
                with col2:
                    st.write(f"**{campaign_display}**")
                    st.caption(next_display)
                    
                with col3:
                    if st.button("Stop", key=f"stop_{enrollment['id']}", help="Stop this campaign"):
                        try:
                            db.table("campaign_enrollments").update({"status": "stopped"}).eq("id", enrollment["id"]).execute()
                            st.success("Campaign stopped!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
        
    except Exception as e:
        st.error(f"Error loading active campaigns: {e}")

def render_enrolled_contacts():
    """Show all contacts and their enrollment status"""
    st.header("👥 Contact Enrollment Status")
    
    # Contact type filter
    contact_types = ["All", "networking", "lead", "prospect", "client", "vendor"]
    selected_type = st.selectbox("Filter by contact type:", contact_types)
    
    db = get_db()
    try:
        # Get all contacts
        contacts_resp = db.table("contacts").select("*").eq("archived", False).execute()
        contacts = contacts_resp.data or []
        
        # Filter by type if selected
        if selected_type != "All":
            contacts = [c for c in contacts if c.get("type") == selected_type]
        
        # Get enrollments for display
        enrollments_resp = db.table("campaign_enrollments").select("*").execute()
        enrollments = enrollments_resp.data or []
        
        # Create enrollment lookup
        enrollment_lookup = {}
        for enrollment in enrollments:
            contact_id = enrollment.get("contact_id")
            if contact_id not in enrollment_lookup:
                enrollment_lookup[contact_id] = []
            enrollment_lookup[contact_id].append(enrollment)
        
        if not contacts:
            st.info(f"No {'contacts' if selected_type == 'All' else selected_type + ' contacts'} found.")
            return
        
        # Display contacts with their enrollment status
        for contact in contacts:
            contact_id = contact["id"]
            contact_enrollments = enrollment_lookup.get(contact_id, [])
            active_enrollments = [e for e in contact_enrollments if e.get("status") == "active"]
            
            contact_name = f"{contact.get('first_name', 'Unknown')} {contact.get('last_name', '')}"
            contact_type = contact.get('type', 'unknown')
            
            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.write(f"**{contact_name}**")
                    st.caption(f"Type: {contact_type} | 📧 {contact.get('email', 'No email')}")
                
                with col2:
                    if active_enrollments:
                        for enrollment in active_enrollments:
                            campaign_id = enrollment.get("campaign_id", "Unknown")
                            next_email = enrollment.get("next_email_scheduled")
                            if next_email:
                                try:
                                    next_date = datetime.fromisoformat(next_email.replace('Z', '+00:00')).strftime('%b %d')
                                    st.write(f"📧 {campaign_id} (Next: {next_date})")
                                except:
                                    st.write(f"📧 {campaign_id}")
                            else:
                                st.write(f"✅ {campaign_id} (Completed)")
                    else:
                        st.write("🚫 No active campaigns")
                
                with col3:
                    # Quick enroll button
                    campaign_map = {
                        "networking": "networking-drip-6week",
                        "lead": "lead-drip",
                        "prospect": "prospect-drip", 
                        "client": "client-drip"
                    }
                    
                    if contact_type in campaign_map and not active_enrollments:
                        if st.button("📬 Enroll", key=f"enroll_{contact_id}", help=f"Auto-enroll in {contact_type} campaign"):
                            try:
                                from db_service import _auto_enroll_in_drip_campaign
                                result = _auto_enroll_in_drip_campaign(contact_id, campaign_map[contact_type])
                                if result:
                                    st.success("Enrolled!")
                                    st.rerun()
                                else:
                                    st.error("Failed to enroll")
                            except Exception as e:
                                st.error(f"Error: {e}")
    
    except Exception as e:
        st.error(f"Error loading contacts: {e}")

def render_campaign_templates():
    """Show and manage campaign templates"""
    st.header("⚙️ Campaign Templates")
    
    db = get_db()
    
    # Try to load templates from database
    try:
        templates_resp = db.table("drip_campaign_templates").select("*").execute()
        templates = templates_resp.data or []
        
        if templates:
            st.success(f"✅ {len(templates)} campaign templates loaded from database")
            
            for template in templates:
                with st.expander(f"📧 {template.get('name', 'Unnamed Campaign')}"):
                    st.write(f"**Campaign ID:** {template.get('campaign_id')}")
                    st.write(f"**Description:** {template.get('description', 'No description')}")
                    
                    # Show email sequence
                    email_sequence = template.get('email_sequence', [])
                    if isinstance(email_sequence, str):
                        try:
                            email_sequence = json.loads(email_sequence)
                        except:
                            email_sequence = []
                    
                    if email_sequence:
                        st.write(f"**Email Sequence:** {len(email_sequence)} emails")
                        for i, email in enumerate(email_sequence, 1):
                            day = email.get('day', i)
                            purpose = email.get('purpose', 'Unknown')
                            subject = email.get('subject', 'No subject')
                            st.caption(f"  {i}. Day {day}: {subject} ({purpose})")
                    
                    auto_enroll = template.get('auto_enroll_contact_types', [])
                    if auto_enroll:
                        st.write(f"**Auto-enroll:** {', '.join(auto_enroll)}")
        else:
            st.warning("⚠️ No campaign templates found in database")
            st.info("Campaign templates need to be loaded via the SQL migration. See DRIP_SETUP_REQUIRED.md")
            
    except Exception as e:
        st.error(f"❌ Error loading templates: {e}")
        st.info("This usually means the drip migration SQL hasn't been run yet.")
    
    # Show code-based templates as fallback
    st.subheader("📋 Available Templates (Code)")
    st.info("These templates are defined in drip_scheduler.py and ready to be loaded into the database.")
    
    code_templates = {
        "networking-drip-6week": {
            "name": "🤝 Networking Follow-Up (6 Week)",
            "emails": 8,
            "description": "8-email follow-up sequence for networking contacts over 6 weeks"
        },
        "lead-drip": {
            "name": "🎯 Lead Nurture (4 Week)", 
            "emails": 6,
            "description": "6-email nurture sequence for inbound leads over 4 weeks"
        },
        "prospect-drip": {
            "name": "💼 Prospect Nurture (6 Week)",
            "emails": 5, 
            "description": "5-email professional sequence for qualified prospects"
        },
        "client-drip": {
            "name": "⭐ Client Onboarding (2 Week)",
            "emails": 4,
            "description": "4-email onboarding sequence for new clients"
        }
    }
    
    for campaign_id, info in code_templates.items():
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{info['name']}**")
                st.caption(f"{info['emails']} emails • {info['description']}")
            with col2:
                st.write(f"📧 {info['emails']} emails")

def render_bulk_actions():
    """Bulk campaign management actions"""
    st.header("🔄 Bulk Campaign Actions")
    
    st.warning("⚠️ Bulk actions affect multiple contacts at once. Use carefully!")
    
    # Action selection
    action = st.selectbox(
        "Select bulk action:",
        [
            "",
            "Stop all active campaigns",
            "Re-enroll based on contact type", 
            "Archive completed enrollments",
            "Export campaign data"
        ]
    )
    
    if action == "Stop all active campaigns":
        st.subheader("🛑 Stop All Active Campaigns")
        st.write("This will stop ALL currently active campaign enrollments.")
        
        if st.button("⚠️ STOP ALL CAMPAIGNS", type="primary"):
            db = get_db()
            try:
                result = db.table("campaign_enrollments").update({"status": "stopped"}).eq("status", "active").execute()
                count = len(result.data) if result.data else 0
                st.success(f"✅ Stopped {count} active campaigns!")
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    elif action == "Re-enroll based on contact type":
        st.subheader("📬 Auto Re-enrollment") 
        st.write("This will enroll contacts in campaigns based on their current type (networking → networking-drip, etc.)")
        
        contact_type = st.selectbox("Select contact type:", ["networking", "lead", "prospect", "client"])
        
        if st.button(f"📬 Re-enroll all {contact_type} contacts", type="primary"):
            db = get_db()
            try:
                # Get contacts of selected type without active campaigns
                contacts_resp = db.table("contacts").select("*").eq("type", contact_type).eq("archived", False).execute()
                contacts = contacts_resp.data or []
                
                enrolled_count = 0
                campaign_map = {
                    "networking": "networking-drip-6week",
                    "lead": "lead-drip",
                    "prospect": "prospect-drip",
                    "client": "client-drip"
                }
                
                target_campaign = campaign_map.get(contact_type)
                if target_campaign:
                    for contact in contacts:
                        try:
                            # Check if already enrolled
                            existing = db.table("campaign_enrollments").select("*").eq(
                                "contact_id", contact["id"]
                            ).eq("status", "active").execute()
                            
                            if not existing.data:  # No active enrollments
                                from db_service import _auto_enroll_in_drip_campaign
                                if _auto_enroll_in_drip_campaign(contact["id"], target_campaign):
                                    enrolled_count += 1
                        except:
                            continue
                    
                    st.success(f"✅ Enrolled {enrolled_count} contacts in {target_campaign}!")
                else:
                    st.error("❌ No campaign mapping for this contact type")
                    
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    elif action == "Export campaign data":
        st.subheader("📊 Export Campaign Data")
        
        if st.button("📁 Export to CSV"):
            try:
                db = get_db()
                
                # Get all enrollments with contact info
                enrollments_resp = db.table("campaign_enrollments").select("*").execute()
                enrollments = enrollments_resp.data or []
                
                export_data = []
                for enrollment in enrollments:
                    contact_id = enrollment.get("contact_id")
                    try:
                        contact_resp = db.table("contacts").select("*").eq("id", contact_id).single().execute()
                        contact = contact_resp.data or {}
                        
                        export_data.append({
                            "Contact Name": f"{contact.get('first_name', '')} {contact.get('last_name', '')}",
                            "Email": contact.get('email', ''),
                            "Company": contact.get('company', ''),
                            "Type": contact.get('type', ''),
                            "Campaign": enrollment.get('campaign_id', ''),
                            "Status": enrollment.get('status', ''),
                            "Enrolled Date": enrollment.get('created_at', '')[:10],
                            "Next Email": enrollment.get('next_email_scheduled', '')[:10] if enrollment.get('next_email_scheduled') else ''
                        })
                    except:
                        continue
                
                if export_data:
                    df = pd.DataFrame(export_data)
                    csv = df.to_csv(index=False)
                    
                    st.download_button(
                        label="📁 Download Campaign Data CSV",
                        data=csv,
                        file_name=f"mpt_campaign_data_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No data to export")
                    
            except Exception as e:
                st.error(f"❌ Export error: {e}")

# Main page routing
if page_mode == "📊 Analytics Dashboard":
    render_analytics_dashboard()
elif page_mode == "📧 Active Campaigns":
    render_active_campaigns()
elif page_mode == "👥 Enrolled Contacts":
    render_enrolled_contacts()
elif page_mode == "⚙️ Campaign Templates":
    render_campaign_templates()
elif page_mode == "🔄 Bulk Actions":
    render_bulk_actions()

# Footer
st.markdown("---")
st.caption("💡 **Tip:** Use the sidebar to navigate between different campaign management views.")