"""
SSO Authentication for Streamlit Apps
=====================================

Verifies SSO tokens from Mission Control and manages session state.

Usage in any Streamlit page:
    from sso_auth import require_sso_auth, get_current_user
    
    # At the top of your page
    require_sso_auth()
    
    # Get user info
    user = get_current_user()
    if user:
        st.write(f"Welcome, {user['email']}")
"""

import streamlit as st
from supabase import create_client, Client
from typing import Optional, Dict, Any
import os


# Supabase configuration - shared auth project (Mission Control)
SUPABASE_URL = st.secrets.get("mission_control", {}).get(
    "SUPABASE_URL",
    os.environ.get("MC_SUPABASE_URL", "https://umedbjslspilqakwnapa.supabase.co")
)
SUPABASE_ANON_KEY = st.secrets.get("mission_control", {}).get(
    "SUPABASE_ANON_KEY", 
    os.environ.get("MC_SUPABASE_ANON_KEY", "")
)


def get_supabase_client() -> Optional[Client]:
    """Get Supabase client for auth verification"""
    if not SUPABASE_ANON_KEY:
        return None
    
    try:
        return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    except Exception as e:
        st.warning(f"Auth service unavailable: {e}")
        return None


def verify_sso_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify an SSO token from Mission Control
    
    Returns user info if valid, None if invalid
    """
    client = get_supabase_client()
    if not client:
        return None
    
    try:
        # Get user from token
        response = client.auth.get_user(token)
        if response and response.user:
            return {
                "id": response.user.id,
                "email": response.user.email,
                "full_name": response.user.user_metadata.get("full_name", ""),
                "avatar_url": response.user.user_metadata.get("avatar_url", ""),
                "token": token
            }
    except Exception as e:
        # Token invalid or expired
        pass
    
    return None


def get_sso_token_from_url() -> Optional[str]:
    """Extract SSO token from URL query parameters"""
    params = st.query_params
    return params.get("sso_token", None)


def require_sso_auth(allow_bypass: bool = True) -> Optional[Dict[str, Any]]:
    """
    Require SSO authentication to access the page
    
    Args:
        allow_bypass: If True, allows access without auth (for development)
    
    Returns:
        User info dict if authenticated, None if bypassed
    """
    # Check if user already authenticated in session
    if "sso_user" in st.session_state and st.session_state.sso_user:
        return st.session_state.sso_user
    
    # Check for SSO token in URL
    token = get_sso_token_from_url()
    
    if token:
        user = verify_sso_token(token)
        if user:
            st.session_state.sso_user = user
            # Keep token in URL so refresh works
            # st.query_params.clear()  # Disabled to persist auth on refresh
            return user
        else:
            st.warning("⚠️ Invalid or expired SSO token. Please sign in again.")
    
    # No valid auth
    if allow_bypass:
        # Development mode - allow access without auth
        return None
    else:
        # Production mode - require auth with clean login screen
        # Hide sidebar and center content
        st.markdown("""
        <style>
            [data-testid="stSidebar"] { display: none !important; }
            [data-testid="stSidebarNav"] { display: none !important; }
            .main .block-container { 
                max-width: 450px; 
                padding-top: 5vh;
                margin: 0 auto;
            }
            .login-container {
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                border-radius: 16px;
                padding: 40px 30px;
                text-align: center;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            }
            .login-container h1 { color: white; margin-bottom: 10px; }
            .login-container p { color: rgba(255,255,255,0.8); }
            .login-logo { width: 120px; margin-bottom: 20px; }
        </style>
        """, unsafe_allow_html=True)
        
        # Centered login card
        st.markdown("""
        <div class="login-container">
            <img src="https://mpt-mission-control.vercel.app/mpt-logo.svg" style="height: 80px; margin-bottom: 15px;">
            <h1>🎯 CRM</h1>
            <p>Please sign in through Mission Control<br>to access this application.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.link_button("🚀 Sign in via Mission Control", "https://mpt-mission-control.vercel.app", use_container_width=True)
        
        st.stop()


def get_current_user() -> Optional[Dict[str, Any]]:
    """Get the current authenticated user, or None if not authenticated"""
    return st.session_state.get("sso_user", None)


def is_authenticated() -> bool:
    """Check if user is authenticated"""
    return get_current_user() is not None


def logout():
    """Clear the SSO session"""
    if "sso_user" in st.session_state:
        del st.session_state.sso_user


def render_auth_status():
    """Render auth status in sidebar or header"""
    user = get_current_user()
    
    if user:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"👤 **{user.get('full_name') or user.get('email', 'User')}**")
        with col2:
            if st.button("Logout", key="sso_logout"):
                logout()
                st.rerun()
    else:
        st.markdown("""
        🔐 **Not signed in**
        
        [Sign in via Mission Control →](https://mpt-mission-control.vercel.app)
        """)


def get_return_url() -> str:
    """Get the URL to return to after signing in at Mission Control"""
    # Get current app URL
    # This would be the Streamlit Cloud URL
    return st.secrets.get("app", {}).get("url", "https://mpt-accounting.streamlit.app")


# Auto-check SSO on import
def _auto_init():
    """Auto-initialize SSO check when module is imported"""
    if "sso_initialized" not in st.session_state:
        st.session_state.sso_initialized = True
        token = get_sso_token_from_url()
        if token:
            user = verify_sso_token(token)
            if user:
                st.session_state.sso_user = user

# Run auto-init
_auto_init()
