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
    email = st.text_input("Email", key="page_login_email", value=st.session_state.get("page_login_email_val", ""))
    
    # Detect email type immediately
    email_type = None  # 'new', 'admin', 'existing'
    if email:
        # Check if it's an admin email
        is_admin = check_if_admin_email(email)
        if is_admin:
            email_type = 'admin'
        else:
            # Check if profile exists
            if check_if_profile_exists(email):
                email_type = 'existing'
            else:
                email_type = 'new'
    
    admin_password = None
    full_name = None
    
    # Show appropriate fields based on email type
    if email_type == 'admin':
        st.warning("🔐 Admin account detected. Please enter the admin password.")
        admin_password = st.text_input("Admin Password", type="password", key="page_admin_pwd")
        button_label = "Log In"
    elif email_type == 'new':
        st.info("👋 New email detected! Please enter your name to create an account.")
        full_name = st.text_input("Full Name", key="page_new_name")
        button_label = "Sign Up"
    elif email_type == 'existing':
        st.success("✓ Existing user detected. Click below to log in.")
        button_label = "Log In"
    else:
        st.info("📧 Enter your email to get started.")
        button_label = "Continue"
    
    if st.button(button_label, use_container_width=True, key="page_login_btn"):
        if not email:
            st.error("Please enter your email.")
        elif email_type == 'admin' and not admin_password:
            st.error("Please enter the admin password.")
        elif email_type == 'new' and not full_name:
            st.error("Please enter your full name.")
        else:
            try:
                user = sign_in(email, admin_password, full_name)
                st.session_state.pop("page_login_email_val", None)
                st.success(f"Welcome!")
                st.rerun()
            except Exception as e:
                error_msg = str(e)
                if error_msg == "NEW_EMAIL":
                    # This shouldn't happen if we detected correctly, but handle it
                    st.session_state["page_login_email_val"] = email
                    st.info("👋 This is a new email. Please enter your name above and click Sign Up.")
                    st.rerun()
                else:
                    st.error(f"Login failed: {e}")

