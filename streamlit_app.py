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
    st.info("📧 Just enter your email. If it's new, we'll ask for your name.")
    
    email = st.text_input("Email", key="li_email")
    
    # Check if email belongs to an admin (show password field if so)
    is_admin_email = False
    if email:
        is_admin_email = check_if_admin_email(email)
    
    admin_password = None
    full_name = None
    
    if is_admin_email:
        st.warning("🔐 Admin account detected. Please enter the admin password.")
        admin_password = st.text_input("Admin Password", type="password", key="admin_pwd")
    else:
        st.info("📧 Enter your email to continue. New users will be asked for their name.")
    
    # Check if this is a new email (will be set if login fails with NEW_EMAIL error)
    if "new_email_prompt" in st.session_state and st.session_state["new_email_prompt"]:
        st.divider()
        st.write("**New email detected! Please provide your name:**")
        full_name = st.text_input("Full Name", key="new_name_input")
    
    if st.button("Continue", use_container_width=True):
        if not email:
            st.error("Please enter your email.")
        elif is_admin_email and not admin_password:
            st.error("Please enter the admin password.")
        else:
            try:
                user = sign_in(email, admin_password, full_name)
                st.session_state.pop("new_email_prompt", None)
                st.success(f"Welcome!")
                st.rerun()
            except Exception as e:
                error_msg = str(e)
                if error_msg == "NEW_EMAIL":
                    st.session_state["new_email_prompt"] = True
                    st.info("👋 This is a new email. Please enter your name above and click Continue again.")
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
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.page_link("pages/04_Take_Quiz.py", label="Take Quiz", icon="📝")
    with col2:
        st.page_link("pages/05_Quiz_History.py", label="Quiz History", icon="📚")
    with col3:
        st.page_link("pages/06_My_Rank.py", label="My Rank", icon="🏆")
    
    if prof.get('role') == 'admin':
        st.divider()
        st.subheader("Admin Links")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.page_link("pages/01_Dashboard.py", label="Dashboard", icon="📊")
        with col2:
            st.page_link("pages/02_Manage_Users.py", label="Manage Users", icon="👥")
        with col3:
            st.page_link("pages/03_Create_Quiz.py", label="Create Quiz", icon="➕")
        with col4:
            st.page_link("pages/07_All_Ranks.py", label="All Ranks", icon="📈")