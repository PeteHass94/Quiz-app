import streamlit as st
from lib.supabase_client import get_client
import os
import secrets
import string
from datetime import datetime

# APP_URL = os.getenv("APP_URL", "http://localhost:8501")  # set this in your secrets for prod

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
    sess = {
        "user_id": user.id,
        "email": email,
        "role": "user",
        "full_name": full_name,
        "bypass_auth": True
    }
    st.session_state["sb_session"] = sess
    
    # Store in query params for persistence across refreshes
    st.query_params["user_id"] = user.id
    st.query_params["email"] = email
    
    return user

def sign_in(email: str, admin_password: str = None, full_name: str = None):
    """Sign in with just email. If new email, requires full_name. Admins need password 'quizapp'."""
    # Clear any existing expired session first
    if "sb_session" in st.session_state:
        st.session_state.pop("sb_session", None)
    
    # Clear query params to start fresh
    if "user_id" in st.query_params or "email" in st.query_params:
        st.query_params.clear()
    
    # Get a fresh client without any auth session
    supabase = get_client()
    # Ensure no auth session is set (clear any stale tokens)
    try:
        supabase.auth.sign_out()
    except:
        pass  # Ignore errors if no session exists
    
    try:
        # Check if profile exists (this should work with anon key, no auth needed)
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
        sess = {
            "user_id": profile["id"],
            "email": profile["email"],
            "role": profile.get("role", "user"),
            "full_name": profile.get("full_name", ""),
            "bypass_auth": True,
            "login_time": datetime.utcnow().isoformat()
        }
        st.session_state["sb_session"] = sess
        
        # Store in query params for persistence across refreshes
        st.query_params["user_id"] = profile["id"]
        st.query_params["email"] = profile["email"]
        
        class MockUser:
            def __init__(self, user_id, email):
                self.id = user_id
                self.email = email
        
        return MockUser(profile["id"], profile["email"])
    except Exception as e:
        error_msg = str(e)
        if error_msg == "NEW_EMAIL":
            raise  # Re-raise to handle in UI
        
        # Handle JWT expiration - retry with fresh client
        if "JWT" in error_msg or "expired" in error_msg.lower() or "PGRST303" in error_msg:
            st.session_state.pop("sb_session", None)
            # Clear query params
            st.query_params.clear()
            
            # Retry with completely fresh client
            try:
                # Create a fresh client directly (bypassing cache)
                from supabase import create_client
                url = st.secrets["supabase"]["url"]
                key = st.secrets["supabase"]["anon_key"]
                supabase = create_client(url, key)
                
                # Explicitly clear any auth
                try:
                    supabase.auth.sign_out()
                except:
                    pass
                
                # Retry the profile lookup
                profile_result = supabase.table("profiles").select("id, email, approved, role, full_name").eq("email", email).execute()
                if profile_result.data:
                    profile = profile_result.data[0]
                    if not profile.get("approved", False):
                        supabase.table("profiles").update({"approved": True}).eq("id", profile["id"]).execute()
                    if profile.get("role") == "admin":
                        ADMIN_PASSWORD = "quizapp"
                        if not admin_password or admin_password != ADMIN_PASSWORD:
                            raise ValueError("Admin account detected. Please enter the admin password.")
                    sess = {
                        "user_id": profile["id"],
                        "email": profile["email"],
                        "role": profile.get("role", "user"),
                        "full_name": profile.get("full_name", ""),
                        "bypass_auth": True,
                        "login_time": datetime.utcnow().isoformat()
                    }
                    st.session_state["sb_session"] = sess
                    # Store in query params for persistence
                    st.query_params["user_id"] = profile["id"]
                    st.query_params["email"] = profile["email"]
                    class MockUser:
                        def __init__(self, user_id, email):
                            self.id = user_id
                            self.email = email
                    return MockUser(profile["id"], profile["email"])
            except Exception as retry_error:
                # If retry also fails, re-raise the original error
                raise e
        
        # For other errors, re-raise
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
    
    # If no session in state, try to restore from query params (for persistence across refreshes)
    if not sess:
        # Check query params for session restoration
        query_params = st.query_params
        if "user_id" in query_params and "email" in query_params:
            user_id = query_params["user_id"]
            email = query_params["email"]
            
            # Verify user exists and restore session (use fresh client without auth)
            supabase = get_client()
            # Clear any stale auth session
            try:
                supabase.auth.sign_out()
            except:
                pass
            
            try:
                profile_result = supabase.table("profiles").select("id, email, role, full_name, approved").eq("id", user_id).eq("email", email).execute()
                if profile_result.data:
                    profile = profile_result.data[0]
                    if profile.get("approved", False):
                        # Restore session
                        sess = {
                            "user_id": profile["id"],
                            "email": profile["email"],
                            "role": profile.get("role", "user"),
                            "full_name": profile.get("full_name", ""),
                            "bypass_auth": True,
                            "login_time": datetime.utcnow().isoformat()
                        }
                        st.session_state["sb_session"] = sess
            except Exception as e:
                # If restoration fails, clear query params
                error_msg = str(e)
                if "JWT" in error_msg or "expired" in error_msg.lower() or "PGRST303" in error_msg:
                    st.query_params.clear()
                pass
    
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
            # Clear query params too
            st.query_params.clear()
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
    # Clear query params on sign out
    st.query_params.clear()

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


def delete_user(user_id: str):
    """Delete a user and all their data (admin only). 
    Deletes in this order: user_answers, feedback, profile, and auth user.
    Note: To fully delete from auth, add service_role_key to secrets.toml under [supabase]"""
    supabase = get_client()
    try:
        # 1. Delete all user answers
        try:
            supabase.table("user_answers").delete().eq("user_id", user_id).execute()
        except Exception as e:
            st.warning(f"Warning deleting user_answers: {e}")
        
        # 2. Delete feedback submissions
        try:
            supabase.table("feedback").delete().eq("user_id", user_id).execute()
        except Exception as e:
            # Feedback table might not exist yet, or RLS might prevent deletion
            pass
        
        # 3. Get profile email before deletion (for potential auth lookup)
        profile_email = None
        try:
            profile_result = supabase.table("profiles").select("email").eq("id", user_id).single().execute()
            if profile_result.data:
                profile_email = profile_result.data.get("email")
        except:
            pass  # Profile might not exist
        
        # 4. Delete the profile
        try:
            supabase.table("profiles").delete().eq("id", user_id).execute()
        except Exception as e:
            st.error(f"Error deleting profile: {e}")
            return False
        
        # 5. Delete from Supabase auth (requires service role key)
        # The user_id should match auth.users.id (profile.id = auth.users.id in Supabase)
        auth_deleted = False
        try:
            service_role_key = st.secrets.get("supabase", {}).get("service_role_key")
            if service_role_key:
                # Create admin client with service role key
                from supabase import create_client
                admin_supabase = create_client(
                    st.secrets["supabase"]["url"],
                    service_role_key
                )
                # Delete auth user using admin API
                # user_id should be the UUID from auth.users table
                admin_supabase.auth.admin.delete_user(user_id)
                auth_deleted = True
            else:
                # No service_role_key - user data is deleted but auth user remains
                # They can't log in without a profile anyway
                pass
        except Exception as e:
            # Auth deletion failed - user data is deleted, but auth user remains
            error_msg = str(e)
            if not auth_deleted and service_role_key:
                # Only show warning if we had the key and it still failed
                st.warning(f"⚠️ User data deleted, but auth user deletion failed: {e}")
        
        return True
    except Exception as e:
        st.error(f"Error deleting user: {e}")
        return False



# Note: get_client is imported from lib.supabase_client

# def request_password_reset(email: str):
#     """
#     Sends a password reset email. The link will redirect back to your app.
#     """
#     supabase = get_client()
#     # IMPORTANT: Add APP_URL to Supabase Auth > URL Configuration > Redirect URLs
#     supabase.auth.reset_password_for_email(
#         email,
#         options={"redirect_to": f"{APP_URL}?type=recovery"}
#     )

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
