"""
Reusable login component for pages
"""
import streamlit as st
from lib.auth import sign_in, check_if_admin_email, check_if_profile_exists


def show_login_section():
    """Show a simplified login section for pages."""
    st.title("🧠 Quiz App")
    st.subheader("Please log in to continue")
    
    # Streamlit automatically scopes widget keys per page, so we can use simple keys
    email = st.text_input("Email", key="page_login_email")
    
    # Check if email belongs to an admin
    is_admin_email = False
    if email:
        is_admin_email = check_if_admin_email(email)
    
    admin_password = None
    full_name = None
    
    # Check if this is a new email (not in profiles table)
    is_new_email = False
    if email:
        is_new_email = not check_if_profile_exists(email)
    
    # Show appropriate fields based on email type
    if is_admin_email:
        st.warning("🔐 Admin account detected. Please enter the admin password.")
        admin_password = st.text_input("Admin Password", type="password", key="page_admin_pwd")
    elif is_new_email:
        st.info("👋 New email detected! Please enter your name to create an account.")
        full_name = st.text_input("Full Name", key="page_new_name")
    else:
        st.info("📧 Enter your email to log in. No password needed!")
    
    if st.button("Continue", use_container_width=True, key="page_login_btn"):
        if not email:
            st.error("Please enter your email.")
        elif is_admin_email and not admin_password:
            st.error("Please enter the admin password.")
        elif is_new_email and not full_name:
            st.error("Please enter your full name.")
        else:
            try:
                user = sign_in(email, admin_password, full_name)
                st.success(f"Welcome!")
                st.rerun()
            except Exception as e:
                error_msg = str(e)
                if error_msg == "NEW_EMAIL":
                    # This shouldn't happen if we checked above, but handle it anyway
                    st.info("👋 This is a new email. Please enter your name above and click Continue again.")
                else:
                    st.error(f"Login failed: {e}")

