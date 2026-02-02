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
try:
    import streamlit as st
    if hasattr(st, "secrets"):
        for key, value in st.secrets.items():
            if isinstance(value, str):
                os.environ.setdefault(key, value)
except Exception:
    pass

import random
from datetime import datetime, timedelta

from db_service import (
    db_get_setting,
    db_set_setting,
    db_hash_password,
    db_set_password_reset,
    db_get_password_reset,
    db_clear_password_reset,
    db_send_password_reset_email,
)

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


def _get_admin_email():
    """Get configured admin email for password reset verification."""
    admin_email = os.getenv("ADMIN_EMAIL")
    if not admin_email:
        admin_email = os.getenv("SENDGRID_FROM_EMAIL", "")
    return (admin_email or "").strip()


def _generate_reset_code():
    """Generate a 6-digit reset code."""
    return f"{random.SystemRandom().randint(0, 999999):06d}"


def _parse_iso_datetime(value):
    """Parse an ISO datetime string into a naive datetime."""
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo:
            parsed = parsed.replace(tzinfo=None)
        return parsed
    except Exception:
        return None


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

    if "auth_flow" not in st.session_state:
        st.session_state["auth_flow"] = "login"
    if "reset_success" not in st.session_state:
        st.session_state["reset_success"] = False

    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)

        # Logo
        try:
            st.image("logo.jpg", use_container_width=True)
        except Exception:
            st.title("MPT-CRM")

        if st.session_state["auth_flow"] == "login":
            st.markdown("### Sign In")
            st.markdown("---")

            if st.session_state.get("reset_success"):
                st.success("Password reset successfully. Please sign in.")
                st.session_state["reset_success"] = False

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

            if st.button("Forgot Password?", use_container_width=True):
                st.session_state["auth_flow"] = "forgot_email"
                st.rerun()

        elif st.session_state["auth_flow"] == "forgot_email":
            st.markdown("### Forgot Password")
            st.markdown("---")

            admin_email = _get_admin_email()
            with st.form("forgot_password_form"):
                email = st.text_input("Admin email", key="reset_email")
                submitted = st.form_submit_button("Send Reset Code", type="primary", use_container_width=True)

                if submitted:
                    if not admin_email:
                        st.error("Admin email is not configured. Set ADMIN_EMAIL in .env.")
                        return False
                    if not email or email.strip().lower() != admin_email.lower():
                        st.error("Email does not match the configured admin email.")
                        return False

                    reset_code = _generate_reset_code()
                    expires_at = datetime.now() + timedelta(minutes=15)
                    saved = db_set_password_reset(reset_code, expires_at)
                    if not saved:
                        st.error("Unable to store reset code. Check database connection.")
                        return False

                    send_result = db_send_password_reset_email(
                        to_email=admin_email,
                        reset_code=reset_code,
                        expires_minutes=15
                    )
                    if not send_result.get("success"):
                        db_clear_password_reset()
                        st.error(f"Failed to send reset email: {send_result.get('error')}")
                        return False

                    st.session_state["auth_flow"] = "forgot_verify"
                    st.success("Reset code sent. Check your email.")
                    st.rerun()

            if st.button("Back to Sign In", use_container_width=True):
                st.session_state["auth_flow"] = "login"
                st.rerun()

        elif st.session_state["auth_flow"] == "forgot_verify":
            st.markdown("### Enter Reset Code")
            st.markdown("---")

            with st.form("reset_code_form"):
                code = st.text_input("6-digit code", key="reset_code")
                new_password = st.text_input("New password", type="password", key="reset_new_password")
                confirm_password = st.text_input("Confirm new password", type="password", key="reset_confirm_password")
                submitted = st.form_submit_button("Reset Password", type="primary", use_container_width=True)

                if submitted:
                    if not code or not new_password or not confirm_password:
                        st.error("Please fill in all fields.")
                        return False
                    if new_password != confirm_password:
                        st.error("Passwords do not match.")
                        return False

                    reset_data = db_get_password_reset()
                    stored_code = (reset_data.get("code") or "").strip()
                    expires_at = _parse_iso_datetime(reset_data.get("expires_at"))

                    if not stored_code or not expires_at:
                        st.error("Reset code is not available. Request a new code.")
                        return False
                    if code.strip() != stored_code:
                        st.error("Reset code is incorrect.")
                        return False
                    if datetime.now() > expires_at:
                        st.error("Reset code has expired. Request a new code.")
                        return False

                    new_hash = db_hash_password(new_password)
                    saved = db_set_setting("auth_password_hash", new_hash)
                    if not saved:
                        st.error("Unable to update password. Check database connection.")
                        return False

                    db_clear_password_reset()
                    st.session_state["auth_needs_password_change"] = False
                    st.session_state["auth_flow"] = "login"
                    st.session_state["reset_success"] = True
                    st.rerun()

            if st.button("Back to Sign In", use_container_width=True):
                st.session_state["auth_flow"] = "login"
                st.rerun()

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


def logout():
    """Log out the current user."""
    st.session_state["authenticated"] = False
    if "auth_user" in st.session_state:
        del st.session_state["auth_user"]


def render_change_password_form():
    """Render the change password form for authenticated users."""
    if not is_authenticated():
        return

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
