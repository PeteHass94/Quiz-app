"""
Feedback and submission functions
"""
import streamlit as st
from lib.supabase_client import get_client
from datetime import datetime


def submit_feedback(user_id: str, submission_type: str, title: str, content: str, question_answer: str = None):
    """Submit feedback, topic, or question."""
    supabase = get_client()
    try:
        result = supabase.table("feedback").insert({
            "user_id": user_id,
            "submission_type": submission_type,
            "title": title,
            "content": content,
            "question_answer": question_answer,
            "status": "pending"
        }).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        st.error(f"Error submitting feedback: {e}")
        return None


def get_user_feedback(user_id: str):
    """Get all feedback submitted by a user."""
    supabase = get_client()
    try:
        result = supabase.table("feedback").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return result.data
    except Exception as e:
        st.error(f"Error fetching feedback: {e}")
        return []


def get_all_feedback(status: str = None):
    """Get all feedback (admin only). Optionally filter by status."""
    supabase = get_client()
    try:
        query = supabase.table("feedback").select("*, profiles:user_id(full_name, email)")
        
        if status:
            query = query.eq("status", status)
        
        result = query.order("created_at", desc=True).execute()
        return result.data
    except Exception as e:
        # Fallback if nested select doesn't work
        try:
            result = supabase.table("feedback").select("*")
            if status:
                result = result.eq("status", status)
            result = result.order("created_at", desc=True).execute()
            
            # Manually get user info
            if result.data:
                user_ids = list(set([f.get("user_id") for f in result.data if f.get("user_id")]))
                if user_ids:
                    profiles = supabase.table("profiles").select("id, full_name, email").in_("id", user_ids).execute()
                    profile_map = {p["id"]: p for p in profiles.data}
                    
                    for feedback in result.data:
                        user_id = feedback.get("user_id")
                        profile = profile_map.get(user_id, {})
                        feedback["submitted_by"] = {
                            "full_name": profile.get("full_name", "Unknown"),
                            "email": profile.get("email", "")
                        }
            
            return result.data
        except Exception as e2:
            st.error(f"Error fetching feedback: {e2}")
            return []
    except:
        return []


def update_feedback_status(feedback_id: str, status: str, reviewed_by: str, notes: str = None):
    """Update feedback status (admin only)."""
    supabase = get_client()
    try:
        update_data = {
            "status": status,
            "reviewed_by": reviewed_by,
            "reviewed_at": datetime.utcnow().isoformat()
        }
        if notes:
            update_data["notes"] = notes
        
        result = supabase.table("feedback").update(update_data).eq("id", feedback_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        st.error(f"Error updating feedback: {e}")
        return None

