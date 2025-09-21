import streamlit as st
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth

st.set_page_config(page_title="Quiz Admin", page_icon="🔐", layout="centered")

# Load config (you can also use st.secrets["auth_config"] instead)
with open("config.yaml") as f:
    config = yaml.load(f, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
)

name, auth_status, username = authenticator.login("Admin Login", "main")

if auth_status is False:
    st.error("Invalid username or password.")
elif auth_status is None:
    st.info("Enter your admin credentials.")
elif auth_status:
    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"Logged in as {name}")
    # ----- Admin area -----
    st.title("🔐 Quiz Admin")
    st.write("Create/edit monthly quizzes here.")
    # e.g., form for adding a quiz
    with st.form("new_quiz"):
        month = st.selectbox("Month", ["January","February","March","April","May","June","July","August","September","October","November","December"])
        year = st.number_input("Year", min_value=2020, max_value=2100, value=2025, step=1)
        title = st.text_input("Quiz title")
        submitted = st.form_submit_button("Create Quiz")
        if submitted:
            st.success(f"Quiz created: {title} ({month} {year})")
