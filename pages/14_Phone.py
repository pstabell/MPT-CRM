"""
Phone Page for MPT-CRM - Minimal version to debug
"""

import streamlit as st

# Page config - must be first Streamlit command
st.set_page_config(
    page_title="Phone - MPT CRM",
    page_icon="📱",
    layout="wide"
)

st.title("📱 Phone")
st.markdown("Make and receive calls directly from the CRM.")

# Simple iframe embed
st.components.v1.iframe(
    src="https://mpt-phone.vercel.app",
    height=500,
    scrolling=False
)

st.info("If you see this, the page is working!")
