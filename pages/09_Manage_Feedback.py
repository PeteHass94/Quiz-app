"""
Manage Feedback Page - Admin only
"""
import streamlit as st
from lib.auth import get_current_user, get_profile_and_role, require_role
from lib.feedback import get_all_feedback, update_feedback_status

st.set_page_config(page_title="Manage Feedback", page_icon="📋", layout="wide")

from lib.navigation import render_sidebar_navigation
render_sidebar_navigation()

# Check authentication and admin role
user, sess = get_current_user()
if not user:
    from lib.login_component import show_login_section
    show_login_section()
    st.stop()

prof = get_profile_and_role(user.id)
if prof.get('role') != 'admin':
    st.error("Access denied. Admin only.")
    st.stop()

st.title("📋 Manage Feedback & Submissions")

# Filter options
col1, col2 = st.columns([2, 1])
with col1:
    status_filter = st.selectbox(
        "Filter by Status:",
        options=["All", "pending", "reviewed", "implemented", "rejected"],
        index=0
    )
with col2:
    type_filter = st.selectbox(
        "Filter by Type:",
        options=["All", "feedback", "topic", "question"],
        index=0
    )

# Get feedback
status = None if status_filter == "All" else status_filter
all_feedback = get_all_feedback(status)

# Filter by type if needed
if type_filter != "All":
    all_feedback = [f for f in all_feedback if f.get("submission_type") == type_filter]

# Display feedback
if not all_feedback:
    st.info("No feedback found with the selected filters.")
else:
    st.metric("Total Submissions", len(all_feedback))
    
    # Group by status for better organization
    pending_feedback = [f for f in all_feedback if f.get("status") == "pending"]
    other_feedback = [f for f in all_feedback if f.get("status") != "pending"]
    
    if pending_feedback:
        st.subheader(f"⏳ Pending Review ({len(pending_feedback)})")
        
        for idx, feedback in enumerate(pending_feedback):
            with st.expander(f"{feedback.get('submission_type', '').title()}: {feedback.get('title', feedback.get('content', 'No title'))[:50]}...", expanded=(idx == 0)):
                # Get submitter info
                submitted_by = feedback.get("submitted_by", {})
                if not submitted_by:
                    # Try to get from user_id
                    from lib.supabase_client import get_client
                    supabase = get_client()
                    try:
                        user_id = feedback.get("user_id")
                        if user_id:
                            profile = supabase.table("profiles").select("full_name, email").eq("id", user_id).single().execute()
                            if profile.data:
                                submitted_by = {
                                    "full_name": profile.data.get("full_name", "Unknown"),
                                    "email": profile.data.get("email", "")
                                }
                    except:
                        pass
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**Submitted by:** {submitted_by.get('full_name', 'Unknown')} ({submitted_by.get('email', 'N/A')})")
                    st.write(f"**Type:** {feedback.get('submission_type', '').title()}")
                    if feedback.get("title"):
                        st.write(f"**Title:** {feedback.get('title')}")
                    st.write(f"**Content:**")
                    st.write(feedback.get("content", ""))
                    
                    if feedback.get("question_answer"):
                        st.write(f"**Suggested Answer:**")
                        st.info(feedback.get("question_answer"))
                    
                    # Show date
                    if feedback.get("created_at"):
                        from datetime import datetime
                        try:
                            date_obj = datetime.fromisoformat(feedback["created_at"].replace('Z', '+00:00'))
                            st.caption(f"Submitted: {date_obj.strftime('%Y-%m-%d %H:%M:%S')}")
                        except:
                            st.caption(f"Submitted: {feedback['created_at']}")
                
                with col2:
                    st.write("**Update Status:**")
                    new_status = st.selectbox(
                        "Status",
                        options=["pending", "reviewed", "implemented", "rejected"],
                        index=["pending", "reviewed", "implemented", "rejected"].index(feedback.get("status", "pending")),
                        key=f"status_{feedback['id']}"
                    )
                    notes = st.text_area(
                        "Admin Notes",
                        value=feedback.get("notes", ""),
                        height=100,
                        key=f"notes_{feedback['id']}"
                    )
                    
                    if st.button("Update", key=f"update_{feedback['id']}", use_container_width=True):
                        result = update_feedback_status(
                            feedback_id=feedback["id"],
                            status=new_status,
                            reviewed_by=user.id,
                            notes=notes if notes.strip() else None
                        )
                        if result:
                            st.success("✅ Status updated!")
                            st.rerun()
                        else:
                            st.error("Failed to update status.")
    
    if other_feedback:
        st.divider()
        st.subheader(f"📚 Other Submissions ({len(other_feedback)})")
        
        # Show in a table format
        import pandas as pd
        from datetime import datetime
        
        feedback_data = []
        for item in other_feedback:
            # Get submitter info
            submitted_by = item.get("submitted_by", {})
            if not submitted_by:
                from lib.supabase_client import get_client
                supabase = get_client()
                try:
                    user_id = item.get("user_id")
                    if user_id:
                        profile = supabase.table("profiles").select("full_name, email").eq("id", user_id).single().execute()
                        if profile.data:
                            submitted_by = {
                                "full_name": profile.data.get("full_name", "Unknown"),
                                "email": profile.data.get("email", "")
                            }
                except:
                    pass
            
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
                "Submitted By": submitted_by.get("full_name", "Unknown"),
                "Email": submitted_by.get("email", ""),
                "Status": f"{status_emoji} {item.get('status', 'pending').title()}",
                "Date": created_date
            })
        
        df = pd.DataFrame(feedback_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

