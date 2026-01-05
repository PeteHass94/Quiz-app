"""
Create Quiz Page - Admin only
"""
import streamlit as st
from lib.auth import get_current_user, get_profile_and_role
from lib.quiz import (
    create_quiz, get_all_quizzes, create_section, get_sections_by_quiz,
    get_questions_by_section, create_question, DEFAULT_HINT, DEFAULT_EXPLANATION,
    update_question, update_choice, set_correct_answer
)
from lib.navigation import render_sidebar_navigation

st.set_page_config(page_title="Create Quiz", page_icon="➕", layout="wide")

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

        # Show existing questions with edit functionality
        if section_questions:
            st.divider()
            st.subheader(f"📝 Existing Questions ({len(section_questions)})")
            
            for q_idx, question in enumerate(section_questions, 1):
                with st.expander(f"Question {q_idx}: {question.get('question_text', 'N/A')[:50]}...", expanded=False):
                    choices = question.get('choices', [])
                    
                    # Display current question info
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**Question:** {question.get('question_text', 'N/A')}")
                        st.write(f"**Hint:** {question.get('hint', 'N/A')}")
                        st.write(f"**Explanation:** {question.get('explanation', 'N/A')}")
                    with col2:
                        status = "✅ Active" if question.get('is_active') else "❌ Inactive"
                        st.write(f"**Status:** {status}")
                        st.write(f"**Order:** {question.get('order_index', 0)}")
                    
                    st.divider()
                    
                    # Edit question form
                    with st.form(f"edit_question_{question['id']}"):
                        st.write("**Edit Question:**")
                        new_question_text = st.text_area(
                            "Question Text",
                            value=question.get('question_text', ''),
                            height=100,
                            key=f"q_text_{question['id']}"
                        )
                        
                        new_hint = st.text_area(
                            "Hint",
                            value=question.get('hint', DEFAULT_HINT),
                            height=80,
                            key=f"q_hint_{question['id']}"
                        )
                        
                        new_explanation = st.text_area(
                            "Explanation",
                            value=question.get('explanation', DEFAULT_EXPLANATION),
                            height=80,
                            key=f"q_expl_{question['id']}"
                        )
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            new_order = st.number_input(
                                "Order Index",
                                min_value=1,
                                value=question.get('order_index', 1),
                                key=f"q_order_{question['id']}"
                            )
                        with col2:
                            new_active = st.checkbox(
                                "Active",
                                value=question.get('is_active', True),
                                key=f"q_active_{question['id']}"
                            )
                        
                        # Display choices and allow editing
                        st.write("**Choices:**")
                        choice_updates = {}
                        correct_choice_id = None
                        
                        for c_idx, choice in enumerate(choices, 1):
                            col1, col2 = st.columns([4, 1])
                            with col1:
                                new_choice_text = st.text_input(
                                    f"Choice {c_idx}",
                                    value=choice.get('choice_text', ''),
                                    key=f"choice_text_{choice['id']}"
                                )
                                choice_updates[choice['id']] = new_choice_text
                            
                            with col2:
                                is_correct = choice.get('is_correct', False)
                                if is_correct:
                                    correct_choice_id = choice['id']
                                st.write("")
                                st.write(f"{'✅ Correct' if is_correct else '○'}")
                        
                        # Set correct answer
                        if choices:
                            st.write("**Set Correct Answer:**")
                            choice_options = {
                                f"Choice {i+1}: {c.get('choice_text', 'N/A')}": c['id']
                                for i, c in enumerate(choices)
                            }
                            current_correct = next(
                                (f"Choice {i+1}: {c.get('choice_text', 'N/A')}" 
                                 for i, c in enumerate(choices) if c.get('is_correct')),
                                None
                            )
                            
                            selected_correct = st.selectbox(
                                "Which choice is correct?",
                                options=list(choice_options.keys()),
                                index=list(choice_options.keys()).index(current_correct) if current_correct else 0,
                                key=f"correct_{question['id']}"
                            )
                            new_correct_choice_id = choice_options[selected_correct]
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            update_btn = st.form_submit_button("💾 Update Question")
                        with col2:
                            delete_btn = st.form_submit_button("🗑️ Delete Question")
                        
                        if update_btn:
                            try:
                                # Update question
                                update_question(
                                    question['id'],
                                    question_text=new_question_text,
                                    hint=new_hint,
                                    explanation=new_explanation,
                                    is_active=new_active,
                                    order_index=new_order
                                )
                                
                                # Update choices text
                                for choice_id, new_text in choice_updates.items():
                                    if new_text.strip():
                                        update_choice(choice_id, choice_text=new_text)
                                
                                # Set correct answer
                                if new_correct_choice_id:
                                    set_correct_answer(question['id'], new_correct_choice_id)
                                
                                st.success("✅ Question updated successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error updating question: {e}")
                        
                        if delete_btn:
                            st.warning("⚠️ Delete functionality not implemented yet. Please delete manually from database if needed.")
        
        st.divider()
        
        with st.expander("➕ Add New Question to Section", expanded=True):
            # Use a form key that includes section ID to make it unique per section
            form_key = f"new_question_form_{selected_section_id}"
            with st.form(form_key, clear_on_submit=True):
                question_text = st.text_area("Question Text *", height=100, key=f"q_text_{form_key}")
                choice1 = st.text_input("Choice 1 *", key=f"c1_{form_key}")
                choice2 = st.text_input("Choice 2 *", key=f"c2_{form_key}")
                choice3 = st.text_input("Choice 3", key=f"c3_{form_key}")
                choice4 = st.text_input("Choice 4", key=f"c4_{form_key}")

                choices = [c for c in [choice1, choice2, choice3, choice4] if c.strip()]

                # Always show the correct answer selector if we have at least 2 choices
                if len(choices) >= 2:
                    st.divider()
                    st.write("**🎯 Select the Correct Answer:**")
                    correct_index = st.selectbox(
                        "Which choice is the correct answer?",
                        options=list(range(len(choices))),
                        format_func=lambda i: f"Choice {i+1}: {choices[i]}",
                        help="This choice will be marked as the correct answer. Users will get 1 point if they select this option.",
                        key=f"correct_{form_key}"
                    )
                    # Show preview of which choice will be marked correct
                    if correct_index is not None and correct_index < len(choices):
                        st.success(
                            f"✅ **Correct Answer Selected:** Choice {correct_index + 1} - '{choices[correct_index]}'"
                        )
                elif len(choices) == 1:
                    correct_index = 0
                    st.warning("⚠️ Please enter at least 2 choices to select the correct answer.")
                else:
                    correct_index = 0
                    st.info("💡 Enter at least 2 choices, then select which one is correct.")

                st.divider()
                hint = st.text_area("Hint (optional)", height=80, placeholder=f"Default: {DEFAULT_HINT}", key=f"hint_{form_key}")
                explanation = st.text_area(
                    "Explanation (optional)", height=80, placeholder=f"Default: {DEFAULT_EXPLANATION}", key=f"expl_{form_key}"
                )
                question_order = st.number_input(
                    "Question Order Index", min_value=1, value=len(section_questions) + 1, key=f"order_{form_key}"
                )
                is_active = st.checkbox("Active (visible to users)", value=True, key=f"active_{form_key}")

                submitted = st.form_submit_button("✅ Create Question", use_container_width=True)

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
                            # Form will auto-clear due to clear_on_submit=True
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creating question: {e}")
    else:
        st.info("No sections in this quiz yet. Create a section above!")
else:
    st.info("No quizzes yet. Create your first quiz above!")

