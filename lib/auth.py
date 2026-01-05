import streamlit as st
from lib.supabase_client import get_client
import os
import secrets
import string
from datetime import datetime

APP_URL = os.getenv("APP_URL", "http://localhost:8501")  # set this in your secrets for prod

def generate_password(length=32):
    """Generate a random password for internal use."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))

def sign_up(email: str, full_name: str):
    """Sign up with just email and name. Password is auto-generated. Auto-approved as user."""
    supabase = get_client()
    
    # Check if user already exists
    existing_profile = supabase.table("profiles").select("id, email, approved").eq("email", email).execute()
    if existing_profile.data:
        profile = existing_profile.data[0]
        if profile.get("approved"):
            raise ValueError("An account with this email already exists. Please log in instead.")
        else:
            # If exists but not approved, approve them now
            supabase.table("profiles").update({
                "full_name": full_name,
                "approved": True,
                "group": "uncategorised"
            }).eq("id", profile["id"]).execute()
            # Create session
            st.session_state["sb_session"] = {
                "user_id": profile["id"],
                "email": email,
                "role": "user",
                "full_name": full_name,
                "bypass_auth": True
            }
            class MockUser:
                def __init__(self, user_id, email):
                    self.id = user_id
                    self.email = email
            return MockUser(profile["id"], email)
    
    # Generate a random password (users won't need to know it)
    password = generate_password()
    
    # 1) Create auth user
    res = supabase.auth.sign_up({
        "email": email, 
        "password": password,
        "options": {
            "data": {
                "full_name": full_name
            }
        }
    })
    user = res.user
    if not user:
        raise ValueError(res)
    
    # 2) Create profile with approved=True (auto-approved) and group='uncategorised'
    try:
        supabase.table("profiles").upsert({
            "id": user.id,
            "email": email,
            "full_name": full_name,
            "role": "user",
            "approved": True,  # Auto-approved
            "group": "uncategorised"  # Default group
        }).execute()
    except Exception as e:
        # If profile already exists (from trigger), update it
        try:
            supabase.table("profiles").update({
                "full_name": full_name,
                "approved": True,
                "group": "uncategorised"
            }).eq("id", user.id).execute()
        except:
            pass
    
    # Create session immediately
    st.session_state["sb_session"] = {
        "user_id": user.id,
        "email": email,
        "role": "user",
        "full_name": full_name,
        "bypass_auth": True
    }
    
    return user

def sign_in(email: str, admin_password: str = None, full_name: str = None):
    """Sign in with just email. If new email, requires full_name. Admins need password 'quizapp'."""
    # Clear any existing expired session first
    if "sb_session" in st.session_state:
        try:
            old_sess = st.session_state.get("sb_session", {})
            if not old_sess.get("bypass_auth"):
                try:
                    supabase = get_client()
                    supabase.auth.sign_out()
                except:
                    pass
        except:
            pass
        st.session_state.pop("sb_session", None)
    
    supabase = get_client()
    
    try:
        # Check if profile exists
        profile_result = supabase.table("profiles").select("id, email, approved, role, full_name").eq("email", email).execute()
        
        if not profile_result.data:
            # New email - need full_name to sign up
            if not full_name:
                raise ValueError("NEW_EMAIL")  # Special error to prompt for name
            # Sign up the new user (auto-approved)
            return sign_up(email, full_name)
        
        profile = profile_result.data[0]
        
        # If not approved, approve them automatically
        if not profile.get("approved", False):
            supabase.table("profiles").update({"approved": True}).eq("id", profile["id"]).execute()
            profile["approved"] = True
        
        # Check if user is an admin - if so, require password
        if profile.get("role") == "admin":
            ADMIN_PASSWORD = "quizapp"
            if not admin_password or admin_password != ADMIN_PASSWORD:
                raise ValueError("Admin account detected. Please enter the admin password.")
        
        # Create session
        st.session_state["sb_session"] = {
            "user_id": profile["id"],
            "email": profile["email"],
            "role": profile.get("role", "user"),
            "full_name": profile.get("full_name", ""),
            "bypass_auth": True,
            "login_time": datetime.utcnow().isoformat()
        }
        
        class MockUser:
            def __init__(self, user_id, email):
                self.id = user_id
                self.email = email
        
        return MockUser(profile["id"], profile["email"])
    except Exception as e:
        error_msg = str(e)
        if error_msg == "NEW_EMAIL":
            raise  # Re-raise to handle in UI
        if "JWT" in error_msg or "expired" in error_msg.lower() or "PGRST303" in error_msg:
            st.session_state.pop("sb_session", None)
            try:
                supabase = get_client()
                profile_result = supabase.table("profiles").select("id, email, approved, role, full_name").eq("email", email).execute()
                if profile_result.data:
                    profile = profile_result.data[0]
                    if not profile.get("approved", False):
                        supabase.table("profiles").update({"approved": True}).eq("id", profile["id"]).execute()
                    if profile.get("role") == "admin":
                        ADMIN_PASSWORD = "quizapp"
                        if not admin_password or admin_password != ADMIN_PASSWORD:
                            raise ValueError("Admin account detected. Please enter the admin password.")
                    st.session_state["sb_session"] = {
                        "user_id": profile["id"],
                        "email": profile["email"],
                        "role": profile.get("role", "user"),
                        "full_name": profile.get("full_name", ""),
                        "bypass_auth": True,
                        "login_time": datetime.utcnow().isoformat()
                    }
                    class MockUser:
                        def __init__(self, user_id, email):
                            self.id = user_id
                            self.email = email
                    return MockUser(profile["id"], profile["email"])
            except:
                pass
        raise

def check_if_admin_email(email: str):
    """Check if an email belongs to an admin user."""
    supabase = get_client()
    try:
        profile_result = supabase.table("profiles").select("role").eq("email", email).execute()
        if profile_result.data:
            return profile_result.data[0].get("role") == "admin"
        return False
    except:
        return False

def check_if_profile_exists(email: str):
    """Check if a profile with the given email exists."""
    supabase = get_client()
    try:
        profile_result = supabase.table("profiles").select("id").eq("email", email).execute()
        return len(profile_result.data) > 0
    except:
        return False

def sign_in_with_admin(email: str, admin_password: str = None):
    """Admin can sign in users directly. For regular users, use sign_in()."""
    # This is a fallback - for now we'll use the session-based approach
    return sign_in(email)

def get_current_user():
    """Get current user, supporting both Supabase Auth and session-based auth."""
    sess = st.session_state.get("sb_session")
    if not sess:
        return None, None
    
    # Check if we're using bypass auth (email-only login) - this doesn't expire
    if sess.get("bypass_auth"):
        class MockUser:
            def __init__(self, user_id, email):
                self.id = user_id
                self.email = email
        return MockUser(sess["user_id"], sess["email"]), sess
    
    # Otherwise, use Supabase Auth - handle expired tokens
    supabase = get_client()
    try:
        supabase.auth.set_session(sess["access_token"], sess["refresh_token"])
        user = supabase.auth.get_user().user
        return user, sess
    except Exception as e:
        # If JWT expired, clear the session
        error_msg = str(e)
        if "JWT" in error_msg or "expired" in error_msg.lower() or "PGRST303" in error_msg:
            st.session_state.pop("sb_session", None)
            return None, None
        # For other errors, just return None
        return None, None

def get_profile_and_role(user_id: str):
    """Get profile and role. Supports both Supabase Auth and session-based auth."""
    # If using bypass auth, get info from session
    sess = st.session_state.get("sb_session", {})
    if sess.get("bypass_auth"):
        # Try to get group from database if not in session
        supabase = get_client()
        try:
            profile_data = supabase.table("profiles").select("group").eq("id", user_id).single().execute()
            group = profile_data.data.get("group", "uncategorised") if profile_data.data else "uncategorised"
        except:
            group = sess.get("group", "uncategorised")
        
        return {
            "email": sess.get("email", ""),
            "full_name": sess.get("full_name", ""),
            "role": sess.get("role", "user"),
            "approved": True,
            "group": group
        }
    
    # Otherwise, query database
    supabase = get_client()
    try:
        data = supabase.table("profiles").select("email, full_name, role, approved, group").eq("id", user_id).single().execute()
        result = data.data if data.data else {}
        # Ensure group has a default value
        if "group" not in result or not result["group"]:
            result["group"] = "uncategorised"
        return result  # {'email':..., 'full_name':..., 'role': 'user'|'admin', 'approved': True/False, 'group': '...'}
    except:
        # Fallback to session if database query fails
        return {
            "email": sess.get("email", ""),
            "full_name": sess.get("full_name", ""),
            "role": sess.get("role", "user"),
            "approved": True,
            "group": sess.get("group", "uncategorised")
        }

def sign_out():
    sess = st.session_state.get("sb_session", {})
    if not sess.get("bypass_auth"):
        supabase = get_client()
        try:
            supabase.auth.sign_out()
        except Exception as e:
            st.error(f"Error signing out: {e}")
        except:
            pass
    st.session_state.pop("sb_session", None)

def require_role(roles=("admin",)):
    """Call at top of admin pages to block unauthorized access."""
    import streamlit as st
    user, _ = get_current_user()
    if not user:
        st.warning("Please log in.")
        st.stop()
    profile = get_profile_and_role(user.id)
    if profile is None or profile.get("role") not in roles:
        st.error("You do not have permission to view this page.")
        st.stop()
    return user, profile

def get_pending_users():
    """Get all users pending approval."""
    supabase = get_client()
    try:
        result = supabase.table("profiles").select("*").eq("approved", False).order("created_at", desc=True).execute()
        return result.data
    except Exception as e:
        st.error(f"Error fetching pending users: {e}")
        return []

def approve_user(user_id: str):
    """Approve a user account."""
    supabase = get_client()
    try:
        supabase.table("profiles").update({"approved": True}).eq("id", user_id).execute()
        return True
    except Exception as e:
        st.error(f"Error approving user: {e}")
        return False

def add_user_directly(email: str, full_name: str, role: str = "user"):
    """Admin can add a user directly (creates both auth user and profile)."""
    supabase = get_client()
    
    # Check if user already exists
    existing = supabase.table("profiles").select("id").eq("email", email).execute()
    if existing.data:
        raise ValueError(f"User with email {email} already exists.")
    
    # Generate password
    password = generate_password()
    
    # Create auth user
    res = supabase.auth.sign_up({
        "email": email,
        "password": password,
        "options": {
            "data": {
                "full_name": full_name
            }
        }
    })
    user = res.user
    if not user:
        raise ValueError("Failed to create auth user")
    
    # Create profile with approved=True and group='uncategorised'
    try:
        supabase.table("profiles").insert({
            "id": user.id,
            "email": email,
            "full_name": full_name,
            "role": role,
            "approved": True,
            "group": "uncategorised"  # Default group
        }).execute()
        return user
    except Exception as e:
        # If profile creation fails, try to clean up auth user
        raise ValueError(f"Failed to create profile: {e}")



# Note: get_client is imported from lib.supabase_client

def request_password_reset(email: str):
    """
    Sends a password reset email. The link will redirect back to your app.
    """
    supabase = get_client()
    # IMPORTANT: Add APP_URL to Supabase Auth > URL Configuration > Redirect URLs
    supabase.auth.reset_password_for_email(
        email,
        options={"redirect_to": f"{APP_URL}?type=recovery"}
    )

def set_recovery_session(access_token: str, refresh_token: str):
    """
    When user opens your app via the email link, you’ll get tokens in the URL.
    Attach them to the client so update_user() is allowed.
    """
    supabase = get_client()
    # set_session returns a Session; you can ignore the return if not needed
    supabase.auth.set_session(access_token=access_token, refresh_token=refresh_token)

def update_password(new_password: str):
    """
    Update password for the current (recovery or logged-in) session.
    """
    supabase = get_client()
    supabase.auth.update_user({"password": new_password})
