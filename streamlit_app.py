"""
Entrypoint for streamlit app.
Runs top to bottom every time the user interacts with the app (other than imports and cached functions).

conda create --name streamlit_env
conda activate streamlit_env
pip install -r requirements.txt
streamlit run streamlit_app.py
"""

import streamlit as st
from lib.auth import sign_up, sign_in, get_current_user, get_profile_and_role, sign_out

st.set_page_config(page_title="Quiz App", page_icon="🧠", layout="centered")
st.title("🧠 Quiz App")

tab_login, tab_signup, tab_account = st.tabs(["Login", "Sign up", "Account"])

with tab_signup:
    st.subheader("Create an account")
    full_name = st.text_input("Full name")
    email_su = st.text_input("Email", key="su_email")
    pwd_su = st.text_input("Password", type="password", key="su_pwd")
    if st.button("Sign up"):
        if not (full_name and email_su and pwd_su):
            st.error("Please fill all fields.")
        else:
            try:
                sign_up(email_su, pwd_su, full_name)
                st.success("Account created. Please log in.")
            except Exception as e:
                st.error(f"Sign-up failed: {e}")

with tab_login:
    st.subheader("Log in")
    email = st.text_input("Email", key="li_email")
    pwd = st.text_input("Password", type="password", key="li_pwd")
    if st.button("Log in"):
        try:
            user = sign_in(email, pwd)
            st.success(f"Welcome back!")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Login failed: {e}")

with tab_account:
    user, sess = get_current_user()
    if user:
        prof = get_profile_and_role(user.id)
        st.write(f"**Email:** {prof['email']}")
        st.write(f"**Name:** {prof['full_name']}")
        st.write(f"**Role:** `{prof['role']}`")
        if st.button("Sign out"):
            sign_out()
            st.experimental_rerun()
    else:
        st.info("Not logged in.")




