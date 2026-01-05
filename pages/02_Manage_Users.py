"""
Manage Users Page - Admin only
"""
import streamlit as st
from lib.auth import get_current_user, get_profile_and_role, get_pending_users, approve_user, add_user_directly
from lib.supabase_client import get_client

st.set_page_config(page_title="Manage Users", page_icon="👥", layout="wide")

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

st.title("👥 Manage Users")

# Add user directly
with st.expander("➕ Add User Directly", expanded=False):
    with st.form("add_user_form"):
        new_email = st.text_input("Email")
        new_name = st.text_input("Full Name")
        new_role = st.selectbox("Role", ["user", "admin"], index=0)
        new_group = st.text_input("Group", value="uncategorised", help="Enter group name (e.g., family, friends, colleagues) or leave as 'uncategorised'")

        submitted = st.form_submit_button("Add User")

        if submitted:
            if not (new_email and new_name):
                st.error("Please fill all required fields.")
            else:
                try:
                    # Add user and then update group
                    add_user_directly(new_email, new_name, new_role)
                    # Update group separately
                    if new_group:
                        supabase = get_client()
                        user_profile = supabase.table("profiles").select("id").eq("email", new_email).single().execute()
                        if user_profile.data:
                            supabase.table("profiles").update({"group": new_group}).eq("id", user_profile.data["id"]).execute()
                    st.success(f"User {new_name} ({new_email}) added successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding user: {e}")

st.divider()

# Pending users
st.subheader("⏳ Pending Approval")
pending_users = get_pending_users()

if pending_users:
    for u in pending_users:
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{u.get('full_name', 'N/A')}**")
                st.write(f"Email: {u.get('email', 'N/A')}")
            with col2:
                st.write("**Status:** Pending")
            with col3:
                if st.button("Approve", key=f"approve_{u['id']}"):
                    if approve_user(u['id']):
                        st.success("User approved!")
                        st.rerun()
            st.divider()
else:
    st.info("No users pending approval.")

st.divider()

# All users
st.subheader("📋 All Users")
supabase = get_client()
try:
    all_users = supabase.table("profiles").select(
        "id, email, full_name, role, approved, group, created_at"
    ).order("created_at", desc=True).execute()
    if all_users.data:
        import pandas as pd
        users_data = []
        for u in all_users.data:
            users_data.append({
                "Name": u.get('full_name', 'N/A'),
                "Email": u.get('email', 'N/A'),
                "Group": u.get('group', 'uncategorised'),
                "Role": u.get('role', 'user'),
                "Status": "✅ Approved" if u.get('approved') else "⏳ Pending",
                "Created": u.get('created_at', '')[:10] if u.get('created_at') else 'N/A'
            })
        df = pd.DataFrame(users_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Group management section
        st.divider()
        st.subheader("👥 Manage User Groups")
        
        # Get unique groups
        unique_groups = sorted(set([u.get('group', 'uncategorised') for u in all_users.data]))
        
        # Allow editing groups
        selected_user = st.selectbox(
            "Select user to change group:",
            options=[f"{u.get('full_name', 'N/A')} ({u.get('email', 'N/A')})" for u in all_users.data],
            key="user_group_select"
        )
        
        if selected_user:
            # Extract user ID from selection
            selected_email = selected_user.split('(')[1].split(')')[0]
            selected_user_data = next((u for u in all_users.data if u.get('email') == selected_email), None)
            
            if selected_user_data:
                current_group = selected_user_data.get('group', 'uncategorised')
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Allow selecting from existing groups or creating new
                    group_options = ["uncategorised"] + [g for g in unique_groups if g != "uncategorised"] + ["[Create New Group]"]
                    selected_group_index = 0
                    if current_group in group_options:
                        selected_group_index = group_options.index(current_group)
                    
                    group_choice = st.selectbox(
                        "Select or create group:",
                        options=group_options,
                        index=selected_group_index,
                        key="group_select"
                    )
                    
                    new_group_name = None
                    if group_choice == "[Create New Group]":
                        new_group_name = st.text_input("Enter new group name:", key="new_group_name")
                        if new_group_name:
                            group_choice = new_group_name
                
                with col2:
                    st.write("")  # Spacing
                    st.write("")  # Spacing
                    if st.button("Update Group", key="update_group_btn"):
                        try:
                            supabase.table("profiles").update({"group": group_choice}).eq("id", selected_user_data["id"]).execute()
                            st.success(f"✅ {selected_user_data.get('full_name')} moved to group: {group_choice}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error updating group: {e}")
    else:
        st.info("No users found.")
except Exception as e:
    st.error(f"Error fetching users: {e}")

