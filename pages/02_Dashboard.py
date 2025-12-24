"""
User Dashboard - View score and rank
"""
import streamlit as st
from lib.auth import get_current_user, get_profile_and_role, require_role
from lib.quiz import get_user_score, get_user_rank, get_user_answers, get_leaderboard

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

# Require user to be logged in
user, sess = get_current_user()
if not user:
    st.warning("Please log in to view your dashboard.")
    st.stop()

prof = get_profile_and_role(user.id)

# Only allow regular users (admins have their own page)
if prof.get('role') == 'admin':
    st.info("Admins should use the Admin page. Redirecting...")
    st.stop()

st.title("📊 Your Dashboard")
st.write(f"Welcome, **{prof['full_name']}**!")

# Get user stats
user_score = get_user_score(user.id)
user_rank = get_user_rank(user.id)
user_answers = get_user_answers(user.id)

# Display stats in columns
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Your Score", user_score)

with col2:
    if user_rank:
        st.metric("Your Rank", f"#{user_rank}")
    else:
        st.metric("Your Rank", "Not ranked")

with col3:
    total_answered = len(user_answers)
    st.metric("Questions Answered", total_answered)

st.divider()

# Show leaderboard
st.subheader("🏆 Leaderboard")
leaderboard = get_leaderboard(limit=20)

if leaderboard:
    # Create a table
    leaderboard_data = []
    for entry in leaderboard:
        leaderboard_data.append({
            "Rank": entry["rank"],
            "Name": entry["full_name"],
            "Score": entry["score"]
        })
    
    st.dataframe(leaderboard_data, use_container_width=True, hide_index=True)
else:
    st.info("No scores yet. Be the first to answer questions!")

st.divider()

# Show user's answer history
st.subheader("📋 Your Answer History")

if user_answers:
    for answer in user_answers:
        question = answer.get('questions', {})
        choice = answer.get('choices', {})
        
        if question and choice:
            with st.expander(f"Question: {question.get('question_text', 'N/A')[:50]}..."):
                col1, col2 = st.columns(2)
                with col1:
                    if answer.get('is_correct'):
                        st.success(f"✓ Your answer: {choice.get('choice_text', 'N/A')}")
                    else:
                        st.error(f"✗ Your answer: {choice.get('choice_text', 'N/A')}")
                with col2:
                    st.write(f"**Answered:** {answer.get('answered_at', 'N/A')[:10]}")
                
                if question.get('explanation'):
                    st.write(f"**Explanation:** {question['explanation']}")
else:
    st.info("You haven't answered any questions yet. Go to the main page to start!")

