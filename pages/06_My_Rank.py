"""
My Rank Page - Per quiz and overall rankings
"""
import streamlit as st
from lib.auth import get_current_user, get_profile_and_role
from lib.quiz import get_user_score, get_user_rank, get_user_group_rank, get_leaderboard_with_dates, get_quiz_leaderboard, get_active_quizzes, get_all_quizzes

st.set_page_config(page_title="My Rank", page_icon="🏆", layout="wide")

from lib.navigation import render_sidebar_navigation
render_sidebar_navigation()

# Check authentication
user, sess = get_current_user()
if not user:
    from lib.login_component import show_login_section
    show_login_section()
    st.stop()

st.title("🏆 My Rank")

prof = get_profile_and_role(user.id)
user_group = prof.get('group', 'uncategorised')
user_group_rank = get_user_group_rank(user.id, user_group) if user_group != 'uncategorised' else None

# Get overall metrics
user_score = get_user_score(user.id)
user_rank = get_user_rank(user.id)

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
        st.metric("Group", user_group.title())

st.divider()

# Get all quizzes (active and inactive for historical data)
all_quizzes = get_all_quizzes()

if not all_quizzes:
    st.info("No quizzes available.")
    st.stop()

# Create tabs for each quiz + overall
tab_names = ["Overall"] + [q['title'] for q in all_quizzes]
tabs = st.tabs(tab_names)

# Overall tab
with tabs[0]:
    st.subheader("🏆 Overall Leaderboard")
    leaderboard = get_leaderboard_with_dates(limit=100)
    
    if leaderboard:
        import pandas as pd
        from datetime import datetime
        
        leaderboard_data = []
        for entry in leaderboard:
            # Format date
            last_date = ""
            if entry.get("last_answer_date"):
                try:
                    date_obj = datetime.fromisoformat(entry["last_answer_date"].replace('Z', '+00:00'))
                    last_date = date_obj.strftime("%Y-%m-%d")
                except:
                    last_date = entry["last_answer_date"][:10] if len(entry["last_answer_date"]) >= 10 else entry["last_answer_date"]
            
            leaderboard_data.append({
                "Rank": entry["rank"],
                "Name": entry["full_name"],
                "Score": entry["score"],
                "Last Completed": last_date if last_date else "Never",
            })
        
        df = pd.DataFrame(leaderboard_data)
        
        # Highlight user's row using pandas Styler
        def highlight_user_row(row):
            is_user = row["Name"] == prof.get('full_name', '')
            styles = [''] * len(row)
            if is_user:
                styles = ['background-color: #9F8000; font-weight: bold'] * len(row)
            return styles
        
        styled_df = df.style.apply(highlight_user_row, axis=1)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
    else:
        st.info("No scores yet. Be the first to answer questions!")

# Per-quiz tabs
for idx, quiz in enumerate(all_quizzes, 1):
    with tabs[idx]:
        st.subheader(f"🏆 {quiz['title']} Leaderboard")
        quiz_leaderboard = get_quiz_leaderboard(quiz['id'], limit=100)
        
        if quiz_leaderboard:
            import pandas as pd
            from datetime import datetime
            
            leaderboard_data = []
            for entry in quiz_leaderboard:
                # Format date
                last_date = ""
                if entry.get("last_answer_date"):
                    try:
                        date_obj = datetime.fromisoformat(entry["last_answer_date"].replace('Z', '+00:00'))
                        last_date = date_obj.strftime("%Y-%m-%d")
                    except:
                        last_date = entry["last_answer_date"][:10] if len(entry["last_answer_date"]) >= 10 else entry["last_answer_date"]
                
                leaderboard_data.append({
                    "Rank": entry["rank"],
                    "Name": entry["full_name"],
                    "Score": entry["score"],
                    "Last Completed": last_date if last_date else "Never",
                })
            
            df = pd.DataFrame(leaderboard_data)
            
            # Highlight user's row using pandas Styler
            def highlight_user_row(row):
                is_user = row["Name"] == prof.get('full_name', '')
                styles = [''] * len(row)
                if is_user:
                    styles = ['background-color: #9F8000; font-weight: bold'] * len(row)
                return styles
            
            styled_df = df.style.apply(highlight_user_row, axis=1)
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
        else:
            st.info(f"No scores yet for {quiz['title']}. Be the first to answer questions!")

# Show group leaderboard if user is in a group
if user_group != 'uncategorised':
    st.divider()
    st.subheader(f"🏆 {user_group.title()} Group Leaderboard")
    from lib.quiz import get_group_leaderboard
    group_leaderboard = get_group_leaderboard(user_group, limit=20)
    
    if group_leaderboard:
        import pandas as pd
        group_leaderboard_data = []
        for entry in group_leaderboard:
            group_leaderboard_data.append({
                "Rank": entry["rank"],
                "Name": entry["full_name"],
                "Score": entry["score"],
            })
        
        df_group = pd.DataFrame(group_leaderboard_data)
        
        # Highlight user's row using pandas Styler
        def highlight_user_row(row):
            is_user = row["Name"] == prof.get('full_name', '')
            styles = [''] * len(row)
            if is_user:
                styles = ['background-color: #9F8000; font-weight: bold'] * len(row)
            return styles
        
        styled_df = df_group.style.apply(highlight_user_row, axis=1)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
    else:
        st.info(f"No scores yet in the {user_group} group.")
