"""
auth.py — Simple Authentication for MPT-CRM
============================================

Provides username/password login gating for all pages.
Credentials configured via environment variables:
    AUTH_USERNAME (default: patrick)
    AUTH_PASSWORD (default: mpt2026!)

Usage in any page:
    from auth import require_login
    require_login()  # Blocks rendering if not authenticated
"""

import os
import streamlit as st

from db_service import db_get_setting, db_set_setting, db_hash_password

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _get_credentials():
    """Get configured credentials from environment."""
    username = os.getenv("AUTH_USERNAME", "patrick")
    password = os.getenv("AUTH_PASSWORD", "mpt2026!")
    return username, password


def _get_stored_password_hash():
    """Get the stored password hash from settings, if available."""
    return db_get_setting("auth_password_hash")


def _verify_current_password(plain_password):
    """Verify current password against stored hash or env fallback."""
    stored_hash = _get_stored_password_hash()
    if stored_hash:
        return db_hash_password(plain_password) == stored_hash
    _, env_pass = _get_credentials()
    if not env_pass:
        return False
    return plain_password == env_pass


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
                stored_hash = _get_stored_password_hash()

                if not stored_hash and not expected_pass:
                    st.error("Authentication not configured. Set AUTH_PASSWORD in .env file.")
                    return False

                if stored_hash:
                    is_valid = username == expected_user and db_hash_password(password) == stored_hash
                    if is_valid:
                        st.session_state["authenticated"] = True
                        st.session_state["auth_user"] = username
                        st.session_state["auth_needs_password_change"] = False
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                        return False
                elif username == expected_user and password == expected_pass:
                    st.session_state["authenticated"] = True
                    st.session_state["auth_user"] = username
                    st.session_state["auth_needs_password_change"] = True
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
    if not is_authenticated():
        login_page()
        st.stop()
    _render_change_password_sidebar()


def logout():
    """Log out the current user."""
    st.session_state["authenticated"] = False
    if "auth_user" in st.session_state:
        del st.session_state["auth_user"]


def _render_change_password_sidebar():
    """Render the change password form in the sidebar for authenticated users."""
    if not is_authenticated():
        return

    with st.sidebar:
        st.markdown("### Change Password")

        if st.session_state.get("auth_needs_password_change"):
            st.warning("Please change your password to finish setup.")

        with st.form("change_password_form"):
            current_password = st.text_input("Current password", type="password", key="current_password")
            new_password = st.text_input("New password", type="password", key="new_password")
            confirm_password = st.text_input("Confirm new password", type="password", key="confirm_new_password")
            submitted = st.form_submit_button("Update Password")

            if submitted:
                if not current_password or not new_password or not confirm_password:
                    st.error("Please fill in all password fields.")
                    return
                if new_password != confirm_password:
                    st.error("New passwords do not match.")
                    return
                if not _verify_current_password(current_password):
                    st.error("Current password is incorrect.")
                    return

                new_hash = db_hash_password(new_password)
                saved = db_set_setting("auth_password_hash", new_hash)
                if saved:
                    st.success("Password updated successfully.")
                    st.session_state["auth_needs_password_change"] = False
                else:
                    st.error("Unable to update password. Check database connection.")
