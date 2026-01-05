"""
Quiz History Page
"""
import streamlit as st
from lib.auth import get_current_user
from lib.quiz import get_user_answers

st.set_page_config(page_title="Quiz History", page_icon="📚", layout="wide")

from lib.navigation import render_sidebar_navigation
render_sidebar_navigation()

# Check authentication
user, sess = get_current_user()
if not user:
    from lib.login_component import show_login_section
    show_login_section()
    st.stop()

st.title("📚 Quiz History")

user_answers = get_user_answers(user.id)

if not user_answers:
    st.info("You haven't answered any questions yet. Go to 'Take Quiz' to get started!")
else:
    st.write(f"**Total Questions Answered:** {len(user_answers)}")
    st.divider()

    for answer in user_answers:
        question = answer.get('questions', {})
        choice = answer.get('choices', {})

        if question and choice:
            with st.expander(f"Question: {question.get('question_text', 'N/A')[:60]}..."):
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

