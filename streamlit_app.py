"""
Entrypoint for streamlit app.
Main login/signup page. Other pages are in pages/ directory.

conda create --name streamlit_env
conda activate streamlit_env
pip install -r requirements.txt
streamlit run streamlit_app.py
"""

import streamlit as st
from lib.auth import sign_in, get_current_user, get_profile_and_role, check_if_admin_email
from lib.navigation import render_sidebar_navigation

st.set_page_config(
    page_title="Quiz App",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Check if user is logged in
user, sess = get_current_user()

if not user:
    # Show login interface - unified login/signup
    st.title("🧠 Quiz App")
    st.subheader("Log in or Sign up")
    
    email = st.text_input("Email", key="li_email", value=st.session_state.get("login_email", ""))
    
    # Detect email type immediately
    email_type = None  # 'new', 'admin', 'existing'
    if email:
        # Check if it's an admin email
        is_admin = check_if_admin_email(email)
        if is_admin:
            email_type = 'admin'
        else:
            # Check if profile exists
            from lib.auth import check_if_profile_exists
            if check_if_profile_exists(email):
                email_type = 'existing'
            else:
                email_type = 'new'
    
    admin_password = None
    full_name = None
    
    # Show appropriate fields based on email type
    if email_type == 'admin':
        st.warning("🔐 Admin account detected. Please enter the admin password.")
        admin_password = st.text_input("Admin Password", type="password", key="admin_pwd")
        button_label = "Log In"
    elif email_type == 'new':
        st.info("👋 New email detected! Please enter your name to create an account.")
        full_name = st.text_input("Full Name", key="new_name_input")
        button_label = "Sign Up"
    elif email_type == 'existing':
        st.success("✓ Existing user detected. Click below to log in.")
        button_label = "Log In"
    else:
        st.info("📧 Enter your email to get started.")
        button_label = "Continue"
    
    # Handle button click
    if st.button(button_label, use_container_width=True, key="login_btn"):
        if not email:
            st.error("Please enter your email.")
        elif email_type == 'admin' and not admin_password:
            st.error("Please enter the admin password.")
        elif email_type == 'new' and not full_name:
            st.error("Please enter your full name.")
        else:
            try:
                user = sign_in(email, admin_password, full_name)
                st.session_state.pop("login_email", None)
                st.success(f"Welcome!")
                st.rerun()
            except Exception as e:
                error_msg = str(e)
                if error_msg == "NEW_EMAIL":
                    # This shouldn't happen if we detected correctly, but handle it
                    st.session_state["login_email"] = email
                    st.info("👋 This is a new email. Please enter your name above and click Sign Up.")
                    st.rerun()
                else:
                    st.error(f"Error: {e}")

else:
    # User is logged in - show welcome and navigation
    render_sidebar_navigation()
    
    prof = get_profile_and_role(user.id)
    st.title("🧠 Quiz App")
    st.success(f"Welcome back, {prof['full_name']}!")
    st.info("👈 Use the sidebar to navigate to different pages.")
    
    # Show quick links
    st.subheader("Quick Links")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.page_link("pages/04_Take_Quiz.py", label="Take Quiz", icon="📝")
    with col2:
        st.page_link("pages/05_Quiz_History.py", label="Quiz History", icon="📚")
    with col3:
        st.page_link("pages/06_My_Rank.py", label="My Rank", icon="🏆")
    with col4:
        st.page_link("pages/08_Submit_Feedback.py", label="Submit Feedback", icon="💬")
    
    if prof.get('role') == 'admin':
        st.divider()
        st.subheader("Admin Links")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.page_link("pages/01_Dashboard.py", label="Dashboard", icon="📊")
        with col2:
            st.page_link("pages/02_Manage_Users.py", label="Manage Users", icon="👥")
        with col3:
            st.page_link("pages/03_Create_Quiz.py", label="Create Quiz", icon="➕")
        with col4:
            st.page_link("pages/07_All_Ranks.py", label="All Ranks", icon="📈")
        with col5:
            st.page_link("pages/09_Manage_Feedback.py", label="Manage Feedback", icon="📋")