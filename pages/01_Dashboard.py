"""
Admin Dashboard Page
"""
import streamlit as st
from lib.auth import get_current_user, get_profile_and_role, require_role
from lib.quiz import get_question_stats, get_user_score, get_user_rank, get_user_group_rank
from lib.auth import get_pending_users

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

from lib.navigation import render_sidebar_navigation
render_sidebar_navigation()

# Check authentication
user, sess = get_current_user()
if not user:
    from lib.login_component import show_login_section
    show_login_section()
    st.stop()

# Check if admin
prof = get_profile_and_role(user.id)
if prof.get('role') != 'admin':
    st.error("Access denied. Admin only.")
    st.stop()

st.title("📊 Admin Dashboard")
st.success(f"Hello {prof['full_name']} (role: {prof['role']})")

# User's rank information
st.subheader("🏆 Your Rankings")
user_score = get_user_score(user.id)
user_rank = get_user_rank(user.id)
user_group = prof.get('group', 'uncategorised')
user_group_rank = get_user_group_rank(user.id, user_group) if user_group != 'uncategorised' else None

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Your Score", user_score)
with col2:
    if user_rank:
        st.metric("Overall Rank", f"#{user_rank}")
    else:
        st.metric("Overall Rank", "Not ranked")
with col3:
    if user_group_rank:
        st.metric(f"Rank in {user_group.title()}", f"#{user_group_rank}")
    else:
        st.metric(f"Group", user_group.title())

st.divider()

# Quick stats
st.subheader("📈 Quick Stats")
stats = get_question_stats()
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Questions", stats.get("total_questions", 0))
with col2:
    st.metric("Active Questions", stats.get("active_questions", 0))
with col3:
    st.metric("Total Answers", stats.get("total_answers", 0))
with col4:
    pending = len(get_pending_users())
    st.metric("Pending Users", pending)

st.divider()
st.info("Use the sidebar to navigate to different admin functions.")

