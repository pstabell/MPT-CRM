"""
Phone Page for MPT-CRM
=======================

Integrated softphone for making calls directly from the CRM.
Uses MPT-Phone (Twilio-based browser softphone).
"""

import streamlit as st
import streamlit.components.v1 as components
from sso_auth import require_sso_auth, is_authenticated
from mobile_styles import inject_mobile_styles

# Page config
st.set_page_config(
    page_title="Phone - MPT CRM",
    page_icon="📞",
    layout="wide"
)

# Auth check
if not is_authenticated():
    require_sso_auth()
    st.stop()

# Mobile styles
inject_mobile_styles()

st.title("📞 Phone")
st.markdown("Make and receive calls directly from the CRM.")

# MPT-Phone softphone URL
PHONE_APP_URL = "https://mpt-phone.vercel.app"

# Embed the phone app
st.markdown("---")

# Create two columns - phone on left, call notes on right
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Softphone")
    
    # Embed MPT-Phone in an iframe
    components.iframe(
        src=PHONE_APP_URL,
        height=600,
        scrolling=False
    )
    
    st.caption("💡 Click 'Connect' to enable calling. Allow microphone access when prompted.")

with col2:
    st.subheader("Call Notes")
    
    # Quick contact lookup
    phone_search = st.text_input("🔍 Search contact by phone or name", placeholder="Enter phone number or name...")
    
    if phone_search:
        # TODO: Integrate with db_service to search contacts
        st.info(f"Searching for: {phone_search}")
    
    # Call notes area
    st.text_area(
        "Notes from this call",
        height=200,
        placeholder="Enter notes during or after your call...",
        key="call_notes"
    )
    
    # Quick actions
    st.markdown("**Quick Actions**")
    action_col1, action_col2 = st.columns(2)
    
    with action_col1:
        if st.button("📝 Save to Contact", use_container_width=True):
            if st.session_state.get("call_notes"):
                st.success("Notes saved!")
            else:
                st.warning("Enter notes first")
    
    with action_col2:
        if st.button("📋 Create Task", use_container_width=True):
            st.info("Task creation coming soon")

# Recent calls section
st.markdown("---")
st.subheader("📋 Recent Calls")
st.info("Call history integration coming soon. Calls will be logged automatically via Twilio webhooks.")

# Help section
with st.expander("ℹ️ How to use the Phone"):
    st.markdown("""
    **Making Calls:**
    1. Click **Connect** in the softphone to enable calling
    2. Allow microphone access when your browser prompts
    3. Enter a phone number and click **Call**
    4. Your outbound caller ID will show as +1 (239) 426-7058
    
    **Receiving Calls:**
    - Incoming calls to +1 (239) 426-7058 will ring in the softphone
    - Make sure you're connected before expecting incoming calls
    
    **Tips:**
    - Use the call notes area to take notes during calls
    - Save notes to the contact record after the call
    - Call history will be logged automatically
    """)
