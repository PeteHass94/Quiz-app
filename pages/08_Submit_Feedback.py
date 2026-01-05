"""
Submit Feedback Page - For users and admins
"""
import streamlit as st
from lib.auth import get_current_user, get_profile_and_role
from lib.feedback import submit_feedback, get_user_feedback

st.set_page_config(page_title="Submit Feedback", page_icon="💬", layout="wide")

from lib.navigation import render_sidebar_navigation
render_sidebar_navigation()

# Check authentication
user, sess = get_current_user()
if not user:
    from lib.login_component import show_login_section
    show_login_section()
    st.stop()

st.title("💬 Submit Feedback")

prof = get_profile_and_role(user.id)

# Tabs for different submission types
tab1, tab2, tab3 = st.tabs(["📝 General Feedback", "💡 Topic Suggestion", "❓ Question Suggestion"])

# General Feedback Tab
with tab1:
    st.subheader("Share Your Feedback")
    st.info("We'd love to hear your thoughts, suggestions, or any issues you've encountered!")
    
    with st.form("feedback_form", clear_on_submit=True):
        feedback_title = st.text_input("Title (optional)", placeholder="Brief summary of your feedback")
        feedback_content = st.text_area("Your Feedback *", height=150, placeholder="Please share your feedback, suggestions, or report any issues...")
        
        submitted = st.form_submit_button("Submit Feedback", use_container_width=True, type="primary")
        
        if submitted:
            if not feedback_content.strip():
                st.error("Please enter your feedback.")
            else:
                result = submit_feedback(
                    user_id=user.id,
                    submission_type="feedback",
                    title=feedback_title.strip() if feedback_title else None,
                    content=feedback_content.strip()
                )
                if result:
                    st.success("✅ Thank you! Your feedback has been submitted.")
                else:
                    st.error("Failed to submit feedback. Please try again.")

# Topic Suggestion Tab
with tab2:
    st.subheader("Suggest a Topic")
    st.info("Have an idea for a quiz topic? Let us know!")
    
    with st.form("topic_form", clear_on_submit=True):
        topic_title = st.text_input("Topic Title *", placeholder="e.g., World History, Science Facts, etc.")
        topic_description = st.text_area("Topic Description *", height=150, placeholder="Describe the topic and why it would make a good quiz...")
        
        submitted = st.form_submit_button("Submit Topic", use_container_width=True, type="primary")
        
        if submitted:
            if not topic_title.strip() or not topic_description.strip():
                st.error("Please fill in both the title and description.")
            else:
                result = submit_feedback(
                    user_id=user.id,
                    submission_type="topic",
                    title=topic_title.strip(),
                    content=topic_description.strip()
                )
                if result:
                    st.success("✅ Thank you! Your topic suggestion has been submitted.")
                else:
                    st.error("Failed to submit topic. Please try again.")

# Question Suggestion Tab
with tab3:
    st.subheader("Suggest a Question")
    st.info("Have a great question idea? Share it with us! You can include an answer or leave it for us to research.")
    
    with st.form("question_form", clear_on_submit=True):
        question_text = st.text_area("Question *", height=100, placeholder="Enter your question here...")
        question_answer = st.text_area("Answer (optional)", height=80, placeholder="If you know the answer, you can include it here. Otherwise, leave it blank.")
        
        submitted = st.form_submit_button("Submit Question", use_container_width=True, type="primary")
        
        if submitted:
            if not question_text.strip():
                st.error("Please enter a question.")
            else:
                result = submit_feedback(
                    user_id=user.id,
                    submission_type="question",
                    title=None,
                    content=question_text.strip(),
                    question_answer=question_answer.strip() if question_answer.strip() else None
                )
                if result:
                    st.success("✅ Thank you! Your question has been submitted.")
                else:
                    st.error("Failed to submit question. Please try again.")

st.divider()

# Show user's previous submissions
st.subheader("📋 Your Previous Submissions")
user_feedback = get_user_feedback(user.id)

if user_feedback:
    import pandas as pd
    from datetime import datetime
    
    feedback_data = []
    for item in user_feedback:
        # Format date
        created_date = ""
        if item.get("created_at"):
            try:
                date_obj = datetime.fromisoformat(item["created_at"].replace('Z', '+00:00'))
                created_date = date_obj.strftime("%Y-%m-%d %H:%M")
            except:
                created_date = item["created_at"][:16] if len(item["created_at"]) >= 16 else item["created_at"]
        
        status_emoji = {
            "pending": "⏳",
            "reviewed": "👀",
            "implemented": "✅",
            "rejected": "❌"
        }.get(item.get("status", "pending"), "⏳")
        
        feedback_data.append({
            "Type": item.get("submission_type", "").title(),
            "Title": item.get("title", item.get("content", "")[:50] + "...") if item.get("title") else (item.get("content", "")[:50] + "..." if len(item.get("content", "")) > 50 else item.get("content", "")),
            "Status": f"{status_emoji} {item.get('status', 'pending').title()}",
            "Submitted": created_date
        })
    
    df = pd.DataFrame(feedback_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("You haven't submitted any feedback yet.")

