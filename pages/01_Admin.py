import streamlit as st
from lib.auth import require_role

st.set_page_config(page_title="Admin", page_icon="🔐")
user, profile = require_role(("admin",))  # blocks non-admins

st.title("🔐 Admin Dashboard")
st.success(f"Hello {profile['full_name']} (role: {profile['role']})")

# Example: create a monthly quiz
with st.form("new_quiz"):
    month = st.selectbox("Month", ["January","February","March","April","May","June","July","August","September","October","November","December"])
    year = st.number_input("Year", 2020, 2100, 2025, 1)
    title = st.text_input("Quiz title")
    submit = st.form_submit_button("Create")
    if submit:
        st.success(f"Created quiz: {title} ({month} {year})")
