"""
Post-Meeting Survey — MPT CRM
Public survey form for meeting feedback (attendee & host surveys)
"""
import streamlit as st
from datetime import datetime
from supabase import create_client
import os

# Page config - clean survey experience
st.set_page_config(
    page_title="Meeting Feedback | Metro Point Technology",
    page_icon="📋",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Hide sidebar for public survey
st.markdown("""
<style>
    [data-testid="stSidebar"] { display: none; }
    [data-testid="collapsedControl"] { display: none; }
    .main { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)

# Initialize Supabase
@st.cache_resource
def get_supabase():
    url = os.getenv("SUPABASE_URL", st.secrets.get("SUPABASE_URL", ""))
    key = os.getenv("SUPABASE_ANON_KEY", st.secrets.get("SUPABASE_ANON_KEY", ""))
    return create_client(url, key)

supabase = get_supabase()

# Get query parameters
params = st.query_params
contact_id = params.get("contact_id", "")
survey_type = params.get("type", "attendee")  # "attendee" or "host"
meeting_date = params.get("date", datetime.now().strftime("%Y-%m-%d"))

# Header
st.image("https://metropointtech.com/wp-content/uploads/2024/12/mpt-logo.png", width=200)
st.title("📋 Meeting Feedback Survey")

if not contact_id:
    st.error("Invalid survey link. Please use the link from your email.")
    st.stop()

# Get contact info
try:
    response = supabase.table("contacts").select("first_name, last_name, company").eq("id", contact_id).single().execute()
    contact = response.data
    contact_name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
    company = contact.get('company', '')
except Exception as e:
    st.error("Could not load contact information.")
    st.stop()

# Survey content based on type
if survey_type == "host":
    # Patrick's self-assessment survey
    st.subheader(f"Your Meeting with {contact_name}")
    if company:
        st.caption(f"Company: {company}")
    st.caption(f"Meeting Date: {meeting_date}")
    
    st.markdown("---")
    st.markdown("**Please rate your meeting and capture key takeaways:**")
    
    with st.form("host_survey"):
        # Overall rating
        overall_rating = st.slider(
            "How did the meeting go overall?",
            min_value=1, max_value=5, value=3,
            help="1 = Poor, 5 = Excellent"
        )
        
        # Relationship building
        relationship_progress = st.select_slider(
            "Relationship building progress:",
            options=["No connection", "Initial rapport", "Good connection", "Strong connection", "Partnership potential"]
        )
        
        # Business potential
        business_potential = st.select_slider(
            "Business/referral potential:",
            options=["None", "Low", "Medium", "High", "Immediate opportunity"]
        )
        
        # Key takeaways
        key_takeaways = st.text_area(
            "Key takeaways from the meeting:",
            placeholder="What did you learn? What was discussed?",
            height=100
        )
        
        # Action items
        action_items = st.text_area(
            "Action items / Next steps:",
            placeholder="What needs to happen next?",
            height=100
        )
        
        # Follow-up needed
        follow_up = st.selectbox(
            "Follow-up needed?",
            ["No follow-up needed", "Send info/proposal", "Schedule another meeting", "Make introduction", "Add to drip campaign"]
        )
        
        # Additional notes
        additional_notes = st.text_area(
            "Additional notes:",
            placeholder="Anything else to remember?",
            height=80
        )
        
        submitted = st.form_submit_button("✅ Submit Survey", use_container_width=True, type="primary")
        
        if submitted:
            # Format survey results
            survey_result = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 HOST SURVEY RESULTS ({datetime.now().strftime('%Y-%m-%d %H:%M')})
Meeting Date: {meeting_date}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Overall Rating: {'⭐' * overall_rating} ({overall_rating}/5)
Relationship Progress: {relationship_progress}
Business Potential: {business_potential}
Follow-up Needed: {follow_up}

KEY TAKEAWAYS:
{key_takeaways if key_takeaways else 'N/A'}

ACTION ITEMS:
{action_items if action_items else 'N/A'}

ADDITIONAL NOTES:
{additional_notes if additional_notes else 'N/A'}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            
            # Append to contact notes
            try:
                # Get existing notes
                existing = supabase.table("contacts").select("notes").eq("id", contact_id).single().execute()
                existing_notes = existing.data.get("notes", "") or ""
                updated_notes = existing_notes + "\n\n" + survey_result if existing_notes else survey_result
                
                # Update contact
                supabase.table("contacts").update({
                    "notes": updated_notes,
                    "last_contacted": datetime.now().isoformat()
                }).eq("id", contact_id).execute()
                
                st.success("✅ Survey submitted successfully! Your feedback has been saved.")
                st.balloons()
            except Exception as e:
                st.error(f"Error saving survey: {str(e)}")

else:
    # Attendee survey (for Roger, etc.)
    st.subheader("Thank you for meeting with Patrick!")
    st.caption(f"Meeting Date: {meeting_date}")
    
    st.markdown("---")
    st.markdown("**Your feedback helps us improve. This takes less than 2 minutes:**")
    
    with st.form("attendee_survey"):
        # Overall experience
        overall_rating = st.slider(
            "How would you rate your meeting experience?",
            min_value=1, max_value=5, value=3,
            help="1 = Poor, 5 = Excellent"
        )
        
        # Value provided
        value_rating = st.slider(
            "How valuable was the conversation?",
            min_value=1, max_value=5, value=3,
            help="1 = Not valuable, 5 = Very valuable"
        )
        
        # Strategic analysis feedback
        analysis_helpful = st.radio(
            "Was the Strategic Growth Analysis document helpful?",
            ["Very helpful", "Somewhat helpful", "Neutral", "Not very helpful", "Did not review it"],
            index=2
        )
        
        # Topics of interest
        topics_interest = st.multiselect(
            "Which topics would you like to explore further?",
            ["Website development", "CRM implementation", "Marketing automation", "Client portal", "Custom software", "Other"]
        )
        
        # Follow-up interest
        follow_up_interest = st.radio(
            "Would you be interested in a follow-up conversation?",
            ["Yes, definitely", "Maybe, send me more info", "Not at this time"],
            index=1
        )
        
        # Open feedback
        open_feedback = st.text_area(
            "Any other feedback or comments?",
            placeholder="We appreciate your honest feedback...",
            height=100
        )
        
        # Referral question
        referral = st.text_input(
            "Know anyone else who might benefit from meeting with Patrick?",
            placeholder="Name and contact info (optional)"
        )
        
        submitted = st.form_submit_button("✅ Submit Feedback", use_container_width=True, type="primary")
        
        if submitted:
            # Format survey results
            topics_str = ", ".join(topics_interest) if topics_interest else "None selected"
            survey_result = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 ATTENDEE SURVEY RESULTS ({datetime.now().strftime('%Y-%m-%d %H:%M')})
Meeting Date: {meeting_date}
Respondent: {contact_name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Overall Experience: {'⭐' * overall_rating} ({overall_rating}/5)
Value Rating: {'⭐' * value_rating} ({value_rating}/5)
Strategic Analysis: {analysis_helpful}
Topics of Interest: {topics_str}
Follow-up Interest: {follow_up_interest}

FEEDBACK:
{open_feedback if open_feedback else 'No additional feedback'}

REFERRAL:
{referral if referral else 'None provided'}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            
            # Append to contact notes
            try:
                # Get existing notes
                existing = supabase.table("contacts").select("notes").eq("id", contact_id).single().execute()
                existing_notes = existing.data.get("notes", "") or ""
                updated_notes = existing_notes + "\n\n" + survey_result if existing_notes else survey_result
                
                # Update contact
                supabase.table("contacts").update({
                    "notes": updated_notes,
                    "last_contacted": datetime.now().isoformat()
                }).eq("id", contact_id).execute()
                
                st.success("✅ Thank you for your feedback! We truly appreciate it.")
                st.balloons()
                
                st.markdown("---")
                st.markdown("**Learn more about Metro Point Technology:**")
                st.markdown("[🌐 Visit our website](https://metropointtech.com)")
            except Exception as e:
                st.error(f"Error saving survey: {str(e)}")

# Footer
st.markdown("---")
st.caption("Metro Point Technology LLC | (239) 600-8159 | support@metropointtech.com")
