"""
Navigation helper for sidebar menu based on user role
"""
import streamlit as st
from lib.auth import get_current_user, get_profile_and_role, sign_out


def render_sidebar_navigation():
    """Render sidebar navigation based on user role."""
    user, sess = get_current_user()
    
    if not user:
        # Not logged in - show login message
        st.sidebar.info("Please log in to access the app.")
        return
    
    # Get user profile
    prof = get_profile_and_role(user.id)
    role = prof.get('role', 'user')
    
    st.sidebar.image("theme/Logo/quiznight.jpg", use_container_width=True)

    # User info in sidebar
    st.sidebar.markdown(f"### Welcome, {prof['full_name']}!")
    st.sidebar.markdown(f"**Role:** `{role}`")
    st.sidebar.divider()
    
    # Navigation based on role
    if role == 'admin':
        render_admin_navigation()
    else:
        render_user_navigation()
    
    st.sidebar.divider()
    
    # Sign out button
    if st.sidebar.button("🚪 Sign Out", use_container_width=True):
        sign_out()
        st.rerun()


def render_admin_navigation():
    """Render navigation menu for admin users using page links."""
    st.sidebar.markdown("### Navigation")
    
    # Use page links for navigation
    st.sidebar.page_link("pages/01_Dashboard.py", label="Dashboard", icon="📊")
    st.sidebar.page_link("pages/02_Manage_Users.py", label="Manage Users", icon="👥")
    st.sidebar.page_link("pages/03_Create_Quiz.py", label="Create Quiz", icon="➕")
    st.sidebar.page_link("pages/04_Take_Quiz.py", label="Take Quiz", icon="📝")
    st.sidebar.page_link("pages/05_Quiz_History.py", label="Quiz History", icon="📚")
    st.sidebar.page_link("pages/06_My_Rank.py", label="My Rank", icon="🏆")
    st.sidebar.page_link("pages/07_All_Ranks.py", label="All Ranks", icon="📈")
    st.sidebar.page_link("pages/08_Submit_Feedback.py", label="Submit Feedback", icon="💬")
    st.sidebar.page_link("pages/09_Manage_Feedback.py", label="Manage Feedback", icon="📋")


def render_user_navigation():
    """Render navigation menu for regular users using page links."""
    st.sidebar.markdown("### Navigation")
    
    # Use page links for navigation
    st.sidebar.page_link("pages/04_Take_Quiz.py", label="Take Quiz", icon="📝")
    st.sidebar.page_link("pages/05_Quiz_History.py", label="Quiz History", icon="📚")
    st.sidebar.page_link("pages/06_My_Rank.py", label="My Rank", icon="🏆")
    st.sidebar.page_link("pages/08_Submit_Feedback.py", label="Submit Feedback", icon="💬")

