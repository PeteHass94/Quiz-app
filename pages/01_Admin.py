"""
Admin Dashboard - Manage questions and view scores
"""
import streamlit as st
from lib.auth import require_role, get_pending_users, approve_user, add_user_directly
from lib.quiz import (
    get_all_questions, create_question, get_all_scores, 
    get_question_stats, get_active_questions,
    create_quiz, get_all_quizzes, create_section, get_sections_by_quiz,
    get_questions_by_section, get_quiz_structure, DEFAULT_HINT, DEFAULT_EXPLANATION
)

st.set_page_config(page_title="Admin", page_icon="🔐", layout="wide")

# Require admin role
user, profile = require_role(("admin",))

st.title("🔐 Admin Dashboard")
st.success(f"Hello {profile['full_name']} (role: {profile['role']})")

# Tabs for different admin functions
tab_users, tab_quizzes, tab_questions, tab_scores, tab_stats = st.tabs(["Manage Users", "Create Quiz", "Manage Questions", "View Scores", "Statistics"])

# Tab 1: Manage Users
with tab_users:
    st.header("👥 User Management")
    
    # Add user directly
    with st.expander("➕ Add User Directly", expanded=False):
        with st.form("add_user_form"):
            st.write("Add a new user who will be immediately approved and can log in right away.")
            new_email = st.text_input("Email")
            new_name = st.text_input("Full Name")
            new_role = st.selectbox("Role", ["user", "admin"], index=0)
            
            submitted = st.form_submit_button("Add User")
            
            if submitted:
                if not (new_email and new_name):
                    st.error("Please fill all required fields.")
                else:
                    try:
                        add_user_directly(new_email, new_name, new_role)
                        st.success(f"User {new_name} ({new_email}) added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding user: {e}")
    
    st.divider()
    
    # Pending users (awaiting approval)
    st.subheader("⏳ Pending Approval")
    pending_users = get_pending_users()
    
    if pending_users:
        for user in pending_users:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**{user.get('full_name', 'N/A')}**")
                    st.write(f"Email: {user.get('email', 'N/A')}")
                    st.write(f"Role: `{user.get('role', 'user')}`")
                
                with col2:
                    st.write(f"**Status:** Pending")
                
                with col3:
                    if st.button("Approve", key=f"approve_{user['id']}"):
                        if approve_user(user['id']):
                            st.success("User approved!")
                            st.rerun()
                        else:
                            st.error("Failed to approve user")
                
                st.divider()
    else:
        st.info("No users pending approval.")
    
    st.divider()
    
    # All users (for reference)
    st.subheader("📋 All Users")
    from lib.supabase_client import get_client
    supabase = get_client()
    try:
        all_users = supabase.table("profiles").select("id, email, full_name, role, approved, created_at").order("created_at", desc=True).execute()
        
        if all_users.data:
            import pandas as pd
            users_data = []
            for u in all_users.data:
                users_data.append({
                    "Name": u.get('full_name', 'N/A'),
                    "Email": u.get('email', 'N/A'),
                    "Role": u.get('role', 'user'),
                    "Status": "✅ Approved" if u.get('approved') else "⏳ Pending",
                    "Created": u.get('created_at', '')[:10] if u.get('created_at') else 'N/A'
                })
            
            df = pd.DataFrame(users_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No users found.")
    except Exception as e:
        st.error(f"Error fetching users: {e}")

# Tab 2: Create Quiz
with tab_quizzes:
    st.header("📚 Quiz Builder")
    
    # Step 1: Create Quiz
    st.subheader("Step 1: Create a Quiz")
    with st.expander("➕ Create New Quiz", expanded=True):
        with st.form("create_quiz_form"):
            quiz_title = st.text_input("Quiz Title *", placeholder="e.g., General Knowledge Quiz 2024")
            quiz_description = st.text_area("Quiz Description (optional)", height=80, placeholder="Describe what this quiz covers...")
            quiz_active = st.checkbox("Active (visible to users)", value=True)
            
            quiz_submitted = st.form_submit_button("Create Quiz")
            
            if quiz_submitted:
                if not quiz_title.strip():
                    st.error("Please enter a quiz title.")
                else:
                    try:
                        quiz_id = create_quiz(quiz_title, quiz_description, quiz_active)
                        st.success(f"✅ Quiz '{quiz_title}' created successfully!")
                        st.session_state["selected_quiz_id"] = quiz_id
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creating quiz: {e}")
    
    st.divider()
    
    # Step 2: Select Quiz and Add Sections
    st.subheader("Step 2: Add Sections to Quiz")
    
    # Get all quizzes
    all_quizzes = get_all_quizzes()
    
    if all_quizzes:
        quiz_options = {f"{q['title']} ({'Active' if q.get('is_active') else 'Inactive'})": q['id'] for q in all_quizzes}
        selected_quiz_title = st.selectbox("Select a Quiz", options=list(quiz_options.keys()))
        selected_quiz_id = quiz_options[selected_quiz_title]
        
        # Store selected quiz in session
        if "selected_quiz_id" not in st.session_state:
            st.session_state["selected_quiz_id"] = selected_quiz_id
        
        # Get sections for selected quiz
        sections = get_sections_by_quiz(selected_quiz_id)
        
        # Add new section
        with st.expander("➕ Add New Section", expanded=False):
            with st.form("create_section_form"):
                section_title = st.text_input("Section Title *", placeholder="e.g., History, Science, etc.")
                section_description = st.text_area("Section Description (optional)", height=80)
                section_order = st.number_input("Order Index", min_value=0, value=len(sections))
                
                section_submitted = st.form_submit_button("Add Section")
                
                if section_submitted:
                    if not section_title.strip():
                        st.error("Please enter a section title.")
                    else:
                        try:
                            section_id = create_section(selected_quiz_id, section_title, section_description, section_order)
                            st.success(f"✅ Section '{section_title}' added!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creating section: {e}")
        
        st.divider()
        
        # Step 3: Add Questions to Sections
        st.subheader("Step 3: Add Questions to Sections")
        
        if sections:
            # Select section
            section_options = {f"{s['title']}": s['id'] for s in sections}
            selected_section_title = st.selectbox("Select a Section", options=list(section_options.keys()))
            selected_section_id = section_options[selected_section_title]
            
            # Get questions for selected section
            section_questions = get_questions_by_section(selected_section_id)
            
            # Add new question
            with st.expander("➕ Add New Question to Section", expanded=True):
                with st.form("new_question_form"):
                    question_text = st.text_area("Question Text *", height=100, placeholder="Enter your question here...")
                    
                    st.write("**Answer Choices:**")
                    choice1 = st.text_input("Choice 1 *")
                    choice2 = st.text_input("Choice 2 *")
                    choice3 = st.text_input("Choice 3")
                    choice4 = st.text_input("Choice 4")
                    
                    choices = [c for c in [choice1, choice2, choice3, choice4] if c.strip()]
                    
                    if choices:
                        correct_index = st.selectbox(
                            "Which choice is correct?",
                            options=list(range(len(choices))),
                            format_func=lambda i: f"Choice {i+1}: {choices[i]}"
                        )
                    else:
                        correct_index = 0
                    
                    hint = st.text_area("Hint (optional)", height=80, placeholder=f"Default: {DEFAULT_HINT}")
                    explanation = st.text_area("Explanation (optional)", height=80, placeholder=f"Default: {DEFAULT_EXPLANATION}")
                    
                    question_order = st.number_input("Question Order Index", min_value=0, value=len(section_questions))
                    is_active = st.checkbox("Active (visible to users)", value=True)
                    
                    submitted = st.form_submit_button("Create Question")
                    
                    if submitted:
                        if not question_text.strip():
                            st.error("Please enter a question.")
                        elif len(choices) < 2:
                            st.error("Please provide at least 2 answer choices.")
                        else:
                            try:
                                # Use defaults if empty
                                hint_text = hint.strip() if hint.strip() else DEFAULT_HINT
                                explanation_text = explanation.strip() if explanation.strip() else DEFAULT_EXPLANATION
                                
                                question_id = create_question(
                                    selected_section_id, 
                                    question_text, 
                                    choices, 
                                    correct_index,
                                    hint_text,
                                    explanation_text,
                                    is_active,
                                    question_order
                                )
                                st.success(f"✅ Question created successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error creating question: {e}")
            
            # Show existing questions in section
            if section_questions:
                st.divider()
                st.write(f"**Questions in this section ({len(section_questions)}):**")
                for idx, question in enumerate(section_questions, 1):
                    with st.container():
                        st.write(f"**Q{idx}:** {question.get('question_text', 'N/A')}")
                        choices_list = question.get('choices', [])
                        if choices_list:
                            st.write("**Choices:**")
                            for i, choice in enumerate(choices_list, 1):
                                marker = "✓" if choice.get('is_correct') else "○"
                                st.write(f"  {marker} {i}. {choice.get('choice_text', 'N/A')}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if question.get('hint'):
                                with st.expander("Hint"):
                                    st.write(question['hint'])
                        with col2:
                            if question.get('explanation'):
                                with st.expander("Explanation"):
                                    st.write(question['explanation'])
                        st.divider()
            else:
                st.info("No questions in this section yet. Add one above!")
        else:
            st.info("No sections in this quiz yet. Create a section above!")
    else:
        st.info("No quizzes yet. Create your first quiz above!")

# Tab 3: Manage Questions (Legacy - for viewing all questions)
with tab_questions:
    st.header("📝 Question Management")
    
    # Add new question form
    with st.expander("➕ Add New Question", expanded=True):
        with st.form("new_question_form"):
            question_text = st.text_area("Question Text", height=100, placeholder="Enter your question here...")
            
            st.write("**Answer Choices:**")
            choice1 = st.text_input("Choice 1")
            choice2 = st.text_input("Choice 2")
            choice3 = st.text_input("Choice 3")
            choice4 = st.text_input("Choice 4")
            
            choices = [c for c in [choice1, choice2, choice3, choice4] if c.strip()]
            
            if choices:
                correct_index = st.selectbox(
                    "Which choice is correct?",
                    options=list(range(len(choices))),
                    format_func=lambda i: f"Choice {i+1}: {choices[i]}"
                )
            else:
                correct_index = 0
            
            explanation = st.text_area("Explanation (optional)", height=80, placeholder="Explain why this answer is correct...")
            
            is_active = st.checkbox("Active (visible to users)", value=True)
            
            submitted = st.form_submit_button("Create Question")
            
            if submitted:
                if not question_text.strip():
                    st.error("Please enter a question.")
                elif len(choices) < 2:
                    st.error("Please provide at least 2 answer choices.")
                else:
                    try:
                        st.warning("⚠️ Please use the 'Create Quiz' tab to add questions to quizzes and sections.")
                        st.info("This form is for legacy questions. New questions should be added through the quiz builder.")
                    except Exception as e:
                        st.error(f"Error: {e}")
    
    st.divider()
    
    # List all questions
    st.subheader("All Questions")
    questions = get_all_questions()
    
    if questions:
        for question in questions:
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Q:** {question.get('question_text', 'N/A')}")
                    choices = question.get('choices', [])
                    if choices:
                        st.write("**Choices:**")
                        for i, choice in enumerate(choices, 1):
                            marker = "✓" if choice.get('is_correct') else "○"
                            st.write(f"  {marker} {i}. {choice.get('choice_text', 'N/A')}")
                    
                    if question.get('explanation'):
                        with st.expander("Explanation"):
                            st.write(question['explanation'])
                
                with col2:
                    status = "✅ Active" if question.get('is_active') else "❌ Inactive"
                    st.write(status)
                    st.write(f"**ID:** {question.get('id')}")
                
                st.divider()
    else:
        st.info("No questions yet. Create your first question above!")

# Tab 4: View Scores
with tab_scores:
    st.header("📊 All User Scores")
    
    scores = get_all_scores()
    
    if scores:
        # Create dataframe
        import pandas as pd
        df_data = []
        for entry in scores:
            df_data.append({
                "Rank": entry["rank"],
                "Name": entry["full_name"],
                "Email": entry["email"],
                "Score": entry["score"]
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Download option
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download as CSV",
            data=csv,
            file_name="quiz_scores.csv",
            mime="text/csv"
        )
    else:
        st.info("No scores yet. Users need to answer questions first.")

# Tab 5: Statistics
with tab_stats:
    st.header("📈 Statistics")
    
    stats = get_question_stats()
    active_questions = get_active_questions()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Questions", stats.get("total_questions", 0))
    
    with col2:
        st.metric("Active Questions", stats.get("active_questions", 0))
    
    with col3:
        st.metric("Total Answers", stats.get("total_answers", 0))
    
    st.divider()
    
    # Question breakdown
    if active_questions:
        st.subheader("Active Questions Breakdown")
        for question in active_questions:
            st.write(f"• {question.get('question_text', 'N/A')[:80]}...")
            choices = question.get('choices', [])
            st.write(f"  ({len(choices)} choices)")
