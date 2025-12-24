"""
Entrypoint for streamlit app.
Runs top to bottom every time the user interacts with the app (other than imports and cached functions).

conda create --name streamlit_env
conda activate streamlit_env
pip install -r requirements.txt
streamlit run streamlit_app.py
"""

import streamlit as st
from lib.auth import (
    sign_up,
    sign_in,
    get_current_user,
    get_profile_and_role,
    sign_out,
    check_if_admin_email,
    require_role,
    get_pending_users,
    approve_user,
)
from lib.quiz import (
    get_active_questions,
    submit_answer,
    get_user_answers,
    get_active_quizzes,
    get_quiz_structure,
    get_user_score,
    get_user_rank,
    get_leaderboard,
    get_all_scores,
    create_quiz,
    get_all_quizzes,
    create_section,
    get_sections_by_quiz,
    get_questions_by_section,
    create_question,
    DEFAULT_HINT,
    DEFAULT_EXPLANATION,
)
from lib.navigation import render_sidebar_navigation

st.set_page_config(
    page_title="Quiz App",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for page navigation
if 'page' not in st.session_state:
    st.session_state['page'] = 'take_quiz'

# Page functions

def show_dashboard_page(user):
    """Admin dashboard page."""
    prof = get_profile_and_role(user.id)
    if prof.get('role') != 'admin':
        st.error("Access denied. Admin only.")
        return

    st.title("📊 Admin Dashboard")
    st.success(f"Hello {prof['full_name']} (role: {prof['role']})")

    # Quick stats
    from lib.quiz import get_question_stats
    stats = get_question_stats()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Questions", stats.get("total_questions", 0))
    with col2:
        st.metric("Active Questions", stats.get("active_questions", 0))
    with col3:
        st.metric("Total Answers", stats.get("total_answers", 0))
    with col4:
        pending = len(get_pending_users())
        st.metric("Pending Users", pending)

    st.divider()
    st.info("Use the sidebar to navigate to different admin functions.")


def show_manage_users_page(user):
    """Page for managing users (admin only)."""
    prof = get_profile_and_role(user.id)
    if prof.get('role') != 'admin':
        st.error("Access denied. Admin only.")
        return

    st.title("👥 Manage Users")

    # Add user directly
    with st.expander("➕ Add User Directly", expanded=False):
        with st.form("add_user_form"):
            from lib.auth import add_user_directly
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
    from lib.supabase_client import get_client
    supabase = get_client()
    try:
        all_users = supabase.table("profiles").select(
            "id, email, full_name, role, approved, created_at"
        ).order("created_at", desc=True).execute()
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


def show_create_quiz_page(user):
    """Page for creating quizzes (admin only)."""
    prof = get_profile_and_role(user.id)
    if prof.get('role') != 'admin':
        st.error("Access denied. Admin only.")
        return

    st.title("➕ Create Quiz")

    # Step 1: Create Quiz
    st.subheader("Step 1: Create a Quiz")
    with st.expander("➕ Create New Quiz", expanded=True):
        with st.form("create_quiz_form"):
            quiz_title = st.text_input("Quiz Title *", placeholder="e.g., General Knowledge Quiz 2024")
            quiz_description = st.text_area("Quiz Description (optional)", height=80)
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

    # Step 2: Add Sections
    st.subheader("Step 2: Add Sections to Quiz")
    all_quizzes = get_all_quizzes()

    if all_quizzes:
        quiz_options = {
            f"{q['title']} ({'Active' if q.get('is_active') else 'Inactive'})": q['id']
            for q in all_quizzes
        }
        selected_quiz_title = st.selectbox("Select a Quiz", options=list(quiz_options.keys()))
        selected_quiz_id = quiz_options[selected_quiz_title]

        sections = get_sections_by_quiz(selected_quiz_id)

        with st.expander("➕ Add New Section", expanded=False):
            with st.form("create_section_form"):
                section_title = st.text_input("Section Title *")
                section_description = st.text_area("Section Description (optional)", height=80)
                section_order = st.number_input("Order Index", min_value=1, value=len(sections) + 1)

                section_submitted = st.form_submit_button("Add Section")

                if section_submitted:
                    if not section_title.strip():
                        st.error("Please enter a section title.")
                    else:
                        try:
                            section_id = create_section(
                                selected_quiz_id, section_title, section_description, section_order
                            )
                            st.success(f"✅ Section '{section_title}' added!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creating section: {e}")

        st.divider()

        # Step 3: Add Questions
        st.subheader("Step 3: Add Questions to Sections")
        if sections:
            section_options = {f"{s['title']}": s['id'] for s in sections}
            selected_section_title = st.selectbox("Select a Section", options=list(section_options.keys()))
            selected_section_id = section_options[selected_section_title]

            section_questions = get_questions_by_section(selected_section_id)

            with st.expander("➕ Add New Question to Section", expanded=True):
                with st.form("new_question_form"):
                    question_text = st.text_area("Question Text *", height=100)
                    choice1 = st.text_input("Choice 1 *")
                    choice2 = st.text_input("Choice 2 *")
                    choice3 = st.text_input("Choice 3")
                    choice4 = st.text_input("Choice 4")

                    choices = [c for c in [choice1, choice2, choice3, choice4] if c.strip()]

                    if choices:
                        st.write("**Select the correct answer:**")
                        correct_index = st.selectbox(
                            "Which choice is correct?",
                            options=list(range(len(choices))),
                            format_func=lambda i: f"Choice {i+1}: {choices[i]}",
                            help="This choice will be marked as the correct answer. Users will get a point if they select this option."
                        )
                        # Show preview of which choice will be marked correct
                        if correct_index is not None and correct_index < len(choices):
                            st.info(
                                f"✅ **Correct Answer:** Choice {correct_index + 1} - '{choices[correct_index]}' will be marked as correct"
                            )
                    else:
                        correct_index = 0
                        st.warning("⚠️ Please enter at least 2 choices before selecting the correct answer.")

                    hint = st.text_area("Hint (optional)", height=80, placeholder=f"Default: {DEFAULT_HINT}")
                    explanation = st.text_area(
                        "Explanation (optional)", height=80, placeholder=f"Default: {DEFAULT_EXPLANATION}"
                    )
                    question_order = st.number_input(
                        "Question Order Index", min_value=1, value=len(section_questions) + 1
                    )
                    is_active = st.checkbox("Active (visible to users)", value=True)

                    submitted = st.form_submit_button("Create Question")

                    if submitted:
                        if not question_text.strip():
                            st.error("Please enter a question.")
                        elif len(choices) < 2:
                            st.error("Please provide at least 2 answer choices.")
                        elif correct_index is None or correct_index < 0 or correct_index >= len(choices):
                            st.error("Please select a valid correct answer choice.")
                        else:
                            try:
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
                                    question_order,
                                )
                                st.success(
                                    f"✅ Question created successfully! Choice {correct_index + 1} ('{choices[correct_index]}') is marked as the correct answer."
                                )
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error creating question: {e}")
        else:
            st.info("No sections in this quiz yet. Create a section above!")
    else:
        st.info("No quizzes yet. Create your first quiz above!")


def show_take_quiz_page(user):
    """Page for taking quizzes."""
    st.title("📝 Take Quiz")

    quizzes = get_active_quizzes()

    if not quizzes:
        st.info("No quizzes available at the moment. Check back later!")
    else:
        quiz_options = {q['title']: q['id'] for q in quizzes}
        selected_quiz_title = st.selectbox("Select a Quiz", options=list(quiz_options.keys()))
        selected_quiz_id = quiz_options[selected_quiz_title]

        quiz_data = get_quiz_structure(selected_quiz_id)

        if not quiz_data or not quiz_data.get('sections'):
            st.info("This quiz has no sections yet.")
        else:
            user_answers = {ans['question_id']: ans for ans in get_user_answers(user.id)}

            for section_idx, section in enumerate(quiz_data['sections'], 1):
                st.subheader(f"Section {section_idx}: {section.get('title', 'Untitled')}")
                if section.get('description'):
                    st.write(section['description'])

                questions = section.get('questions', [])
                if not questions:
                    st.info("No questions in this section yet.")
                    st.divider()
                    continue

                active_questions = [q for q in questions if q.get('is_active', True)]

                for q_idx, question in enumerate(active_questions, 1):
                    with st.container():
                        st.write(f"**Question {q_idx}**")
                        st.write(question.get('question_text', ''))

                        choices = question.get('choices', [])
                        if not choices:
                            st.warning("No choices available for this question.")
                            continue

                        question_id = question['id']
                        previous_answer = user_answers.get(question_id)

                        if previous_answer:
                            selected_choice_id = previous_answer['choice_id']
                            is_correct = previous_answer['is_correct']
                            selected_choice = next((c for c in choices if c['id'] == selected_choice_id), None)

                            if selected_choice:
                                if is_correct:
                                    st.success(f"✓ You answered: {selected_choice['choice_text']} (Correct!)")
                                else:
                                    st.error(f"✗ You answered: {selected_choice['choice_text']} (Incorrect)")
                                    correct_choice = next((c for c in choices if c['is_correct']), None)
                                    if correct_choice:
                                        st.info(f"Correct answer: {correct_choice['choice_text']}")

                            col1, col2 = st.columns(2)
                            with col1:
                                if question.get('hint'):
                                    with st.expander("💡 Hint"):
                                        st.write(question['hint'])
                            with col2:
                                if question.get('explanation'):
                                    with st.expander("📖 Explanation"):
                                        st.write(question['explanation'])
                        else:
                            if question.get('hint') and question.get('hint') != DEFAULT_HINT:
                                with st.expander("💡 Hint (click to reveal)"):
                                    st.write(question['hint'])

                            choice_options = {c['choice_text']: c['id'] for c in choices}
                            selected_text = st.radio(
                                "Select your answer:",
                                options=list(choice_options.keys()),
                                key=f"q_{question_id}"
                            )

                            if st.button(f"Submit Answer", key=f"submit_{question_id}"):
                                selected_choice_id = choice_options[selected_text]
                                selected_choice_obj = next(
                                    (c for c in choices if c['id'] == selected_choice_id), None
                                )

                                if selected_choice_obj:
                                    is_correct = selected_choice_obj.get('is_correct', False)
                                    if submit_answer(user.id, question_id, selected_choice_id, is_correct):
                                        if is_correct:
                                            st.success("✅ Correct! You earned 1 point!")
                                        else:
                                            st.error("❌ Incorrect. No points awarded.")
                                        st.rerun()
                                else:
                                    st.error("Error: Could not find selected choice. Please try again.")

                        st.divider()

                st.divider()


def show_quiz_history_page(user):
    """Page showing user's quiz history."""
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


def show_my_rank_page(user):
    """Page showing user's rank."""
    st.title("🏆 My Rank")

    user_score = get_user_score(user.id)
    user_rank = get_user_rank(user.id)
    prof = get_profile_and_role(user.id)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Your Score", user_score)
    with col2:
        if user_rank:
            st.metric("Your Rank", f"#{user_rank}")
        else:
            st.metric("Your Rank", "Not ranked")

    st.divider()

    # Show leaderboard with user highlighted
    st.subheader("🏆 Leaderboard")
    leaderboard = get_leaderboard(limit=20)

    if leaderboard:
        import pandas as pd
        leaderboard_data = []
        for entry in leaderboard:
            leaderboard_data.append({
                "Rank": entry["rank"],
                "Name": entry["full_name"],
                "Score": entry["score"],
                "You": "⭐" if entry["user_id"] == user.id else "",
            })

        df = pd.DataFrame(leaderboard_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No scores yet. Be the first to answer questions!")


def show_all_ranks_page(user):
    """Page showing all ranks (admin only)."""
    prof = get_profile_and_role(user.id)
    if prof.get('role') != 'admin':
        st.error("Access denied. Admin only.")
        return

    st.title("📈 All Ranks")

    scores = get_all_scores()

    if scores:
        import pandas as pd
        df_data = []
        for entry in scores:
            df_data.append({
                "Rank": entry["rank"],
                "Name": entry["full_name"],
                "Email": entry["email"],
                "Score": entry["score"],
            })

        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        csv = df.to_csv(index=False)
        st.download_button(
            label="Download as CSV",
            data=csv,
            file_name="quiz_scores.csv",
            mime="text/csv",
        )
    else:
        st.info("No scores yet. Users need to answer questions first.")


# Check if user is logged in
user, sess = get_current_user()

if not user:
    # Show login/signup interface
    tab_login, tab_signup = st.tabs(["Login", "Sign up"])

    with tab_signup:
        st.subheader("Create an account")
        st.info(
            "📝 Just enter your name and email. No password needed! Your account will need admin approval before you can log in."
        )
        full_name = st.text_input("Full name")
        email_su = st.text_input("Email", key="su_email")
        if st.button("Sign up"):
            if not (full_name and email_su):
                st.error("Please fill all fields.")
            else:
                try:
                    sign_up(email_su, full_name)
                    st.success(
                        "✅ Account created! Your account is pending admin approval. You'll be able to log in once approved."
                    )
                except Exception as e:
                    st.error(f"Sign-up failed: {e}")

    with tab_login:
        st.subheader("Log in")
        email = st.text_input("Email", key="li_email")

        # Check if email belongs to an admin (show password field if so)
        is_admin_email = False
        if email:
            is_admin_email = check_if_admin_email(email)

        admin_password = None
        if is_admin_email:
            st.warning("🔐 Admin account detected. Please enter the admin password.")
            admin_password = st.text_input("Admin Password", type="password", key="admin_pwd")
        else:
            st.info("📧 Just enter your email to log in. No password needed!")

        if st.button("Log in"):
            if not email:
                st.error("Please enter your email.")
            elif is_admin_email and not admin_password:
                st.error("Please enter the admin password.")
            else:
                try:
                    user = sign_in(email, admin_password)
                    st.success(f"Welcome back!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Login failed: {e}")

else:
    # User is logged in - render sidebar navigation first
    render_sidebar_navigation()

    # Get current page from session state
    current_page = st.session_state.get('page', 'take_quiz')

    # Route to appropriate page
    if current_page == 'dashboard':
        show_dashboard_page(user)
    elif current_page == 'manage_users':
        show_manage_users_page(user)
    elif current_page == 'create_quiz':
        show_create_quiz_page(user)
    elif current_page == 'take_quiz':
        show_take_quiz_page(user)
    elif current_page == 'quiz_history':
        show_quiz_history_page(user)
    elif current_page == 'my_rank':
        show_my_rank_page(user)
    elif current_page == 'all_ranks':
        show_all_ranks_page(user)
    else:
        show_take_quiz_page(user)  # Default page