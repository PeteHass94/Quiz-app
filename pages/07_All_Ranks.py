"""
All Ranks Page - Admin only
"""
import streamlit as st
from lib.auth import get_current_user, get_profile_and_role
from lib.quiz import get_all_scores

st.set_page_config(page_title="All Ranks", page_icon="📈", layout="wide")

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

st.title("📈 All Ranks")

scores = get_all_scores()

if scores:
    import pandas as pd
    df_data = []
    for entry in scores:
        df_data.append({
            "Rank": entry["rank"],
            "Name": entry["full_name"],
            "Email": entry["email"],
            "Score": entry["score"],
        })

    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    csv = df.to_csv(index=False)
    st.download_button(
        label="Download as CSV",
        data=csv,
        file_name="quiz_scores.csv",
        mime="text/csv",
    )
else:
    st.info("No scores yet. Users need to answer questions first.")

