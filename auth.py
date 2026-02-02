"""
auth.py — Simple Authentication for MPT-CRM
============================================

Provides username/password login gating for all pages.
Credentials configured via environment variables:
    AUTH_USERNAME (default: patrick)
    AUTH_PASSWORD (required)

Usage in any page:
    from auth import require_login
    require_login()  # Blocks rendering if not authenticated
"""

import os
import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _get_credentials():
    """Get configured credentials from environment."""
    username = os.getenv("AUTH_USERNAME", "patrick")
    password = os.getenv("AUTH_PASSWORD", "")
    return username, password


def is_authenticated():
    """Check if the current session is authenticated."""
    return st.session_state.get("authenticated", False)


def login_page():
    """Render the login page. Returns True if just authenticated, False otherwise."""
    # Center the login form
    st.markdown("""
    <style>
        [data-testid="stSidebarNav"] { display: none !important; }
        section[data-testid="stSidebar"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)

        # Logo
        try:
            st.image("logo.jpg", use_container_width=True)
        except Exception:
            st.title("MPT-CRM")

        st.markdown("### Sign In")
        st.markdown("---")

        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)

            if submitted:
                expected_user, expected_pass = _get_credentials()

                if not expected_pass:
                    st.error("Authentication not configured. Set AUTH_PASSWORD in .env file.")
                    return False

                if username == expected_user and password == expected_pass:
                    st.session_state["authenticated"] = True
                    st.session_state["auth_user"] = username
                    st.rerun()
                else:
                    st.error("Invalid username or password")
                    return False

        st.caption("Metro Point Technology, LLC")

    return False


def require_login():
    """Gate the current page behind authentication.

    Call this at the top of every page. If the user is not authenticated,
    the login page is shown and page execution stops.

    Usage:
        from auth import require_login
        require_login()
        # ... rest of your page code (only runs if authenticated)
    """
    _, expected_pass = _get_credentials()

    # If no password is configured, skip auth (development mode)
    if not expected_pass:
        return

    if not is_authenticated():
        login_page()
        st.stop()


def logout():
    """Log out the current user."""
    st.session_state["authenticated"] = False
    if "auth_user" in st.session_state:
        del st.session_state["auth_user"]
