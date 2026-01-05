"""
Take Quiz Page - Simplified, one question at a time with button answers
"""
import streamlit as st
from lib.auth import get_current_user, get_profile_and_role
from lib.quiz import get_active_quizzes, get_quiz_structure, submit_answer, get_user_answers, DEFAULT_HINT, DEFAULT_EXPLANATION

st.set_page_config(page_title="Take Quiz", page_icon="📝", layout="wide")

from lib.navigation import render_sidebar_navigation
render_sidebar_navigation()

# Check authentication
user, sess = get_current_user()
if not user:
    from lib.login_component import show_login_section
    show_login_section()
    st.stop()

# Initialize session state for quiz navigation
if 'current_quiz_id' not in st.session_state:
    st.session_state.current_quiz_id = None
if 'current_section_idx' not in st.session_state:
    st.session_state.current_section_idx = 0
if 'current_question_idx' not in st.session_state:
    st.session_state.current_question_idx = 0
if 'show_results' not in st.session_state:
    st.session_state.show_results = False
if 'show_section_summary' not in st.session_state:
    st.session_state.show_section_summary = {}

st.title("📝 Take Quiz")

quizzes = get_active_quizzes()

if not quizzes:
    st.info("No quizzes available at the moment. Check back later!")
    st.stop()

# Quiz selection
quiz_options = {q['title']: q['id'] for q in quizzes}
selected_quiz_title = st.selectbox(
    "Select a Quiz", 
    options=list(quiz_options.keys()),
    key="quiz_selector",
    on_change=lambda: st.session_state.update({
        'current_quiz_id': None,
        'current_section_idx': 0,
        'current_question_idx': 0,
        'show_results': False,
        'show_section_summary': {}
    })
)

selected_quiz_id = quiz_options[selected_quiz_title]
st.session_state.current_quiz_id = selected_quiz_id

quiz_data = get_quiz_structure(selected_quiz_id)

if not quiz_data or not quiz_data.get('sections'):
    st.info("This quiz has no sections yet.")
    st.stop()

sections = quiz_data['sections']
user_answers = {ans['question_id']: ans for ans in get_user_answers(user.id)}

# Helper function to check if section is completed
def is_section_completed(section):
    """Check if all active questions in a section have been answered."""
    questions = section.get('questions', [])
    active_questions = [q for q in questions if q.get('is_active', True)]
    if not active_questions:
        return True
    for question in active_questions:
        if question['id'] not in user_answers:
            return False
    return True

# Helper function to get section score
def get_section_score(section):
    """Calculate score for a section."""
    questions = section.get('questions', [])
    active_questions = [q for q in questions if q.get('is_active', True)]
    if not active_questions:
        return 0, 0
    total = len(active_questions)
    correct = 0
    for question in active_questions:
        answer = user_answers.get(question['id'])
        if answer and answer.get('is_correct'):
            correct += 1
    return correct, total

# Determine what to show
if st.session_state.show_results:
    # Show final results
    st.header("🎯 Quiz Results")
    
    total_correct = 0
    total_questions = 0
    
    for section_idx, section in enumerate(sections, 1):
        st.subheader(f"Section {section_idx}: {section.get('title', 'Untitled')}")
        
        questions = section.get('questions', [])
        active_questions = [q for q in questions if q.get('is_active', True)]
        
        if not active_questions:
            continue
        
        section_correct, section_total = get_section_score(section)
        total_correct += section_correct
        total_questions += section_total
        
        # Section score
        st.metric(f"Section {section_idx} Score", f"{section_correct}/{section_total}")
        
        # Show each question with answer and explanation
        for q_idx, question in enumerate(active_questions, 1):
            st.divider()
            st.write(f"**Question {q_idx}**")
            st.write(question.get('question_text', ''))
            
            answer = user_answers.get(question['id'])
            choices = question.get('choices', [])
            
            if answer:
                selected_choice_id = answer['choice_id']
                is_correct = answer['is_correct']
                selected_choice = next((c for c in choices if c['id'] == selected_choice_id), None)
                correct_choice = next((c for c in choices if c.get('is_correct')), None)
                
                if selected_choice:
                    if is_correct:
                        st.success(f"✓ Your answer: {selected_choice['choice_text']} (Correct)")
                    else:
                        st.error(f"✗ Your answer: {selected_choice['choice_text']} (Incorrect)")
                        if correct_choice:
                            st.info(f"✓ Correct answer: {correct_choice['choice_text']}")
                
                # Show explanation
                if question.get('explanation') and question.get('explanation') != DEFAULT_EXPLANATION:
                    st.write("**📖 Explanation:**", question['explanation'])
            else:
                st.warning("No answer submitted")
    
    st.divider()
    st.header(f"🏆 Total Score: {total_correct}/{total_questions}")
    
    # if st.button("Take Another Quiz", use_container_width=True):
    #     st.session_state.update({
    #         'current_quiz_id': None,
    #         'current_section_idx': 0,
    #         'current_question_idx': 0,
    #         'show_results': False,
    #         'show_section_summary': {}
    #     })
    #     st.rerun()
    
else:
    # Check if all sections are completed
    all_completed = all(is_section_completed(section) for section in sections)
    
    if all_completed:
        # Show final results button
        st.success("🎉 You've completed all sections!")
        if st.button("View Results", use_container_width=True, type="primary"):
            st.session_state.show_results = True
            st.rerun()
    else:
        # Find current section
        current_section_idx = st.session_state.current_section_idx
        current_section = sections[current_section_idx]
        questions = current_section.get('questions', [])
        active_questions = [q for q in questions if q.get('is_active', True)]
        
        if not active_questions:
            st.info("This section has no questions yet.")
            st.stop()
        
        section_completed = is_section_completed(current_section)
        
        # Check if we should show section summary
        section_key = f"section_{current_section_idx}"
        show_summary = st.session_state.show_section_summary.get(section_key, False)
        
        if section_completed and not show_summary:
            # Show section summary
            st.subheader(f"Section {current_section_idx + 1}: {current_section.get('title', 'Untitled')} - Results")
            
            section_correct, section_total = get_section_score(current_section)
            st.metric("Section Score", f"{section_correct}/{section_total}")
            
            st.divider()
            
            # Show all questions with answers, hints, and explanations
            for q_idx, question in enumerate(active_questions, 1):
                st.write(f"**Question {q_idx}**")
                st.write(question.get('question_text', ''))
                
                answer = user_answers.get(question['id'])
                choices = question.get('choices', [])
                
                if answer:
                    selected_choice_id = answer['choice_id']
                    is_correct = answer['is_correct']
                    selected_choice = next((c for c in choices if c['id'] == selected_choice_id), None)
                    correct_choice = next((c for c in choices if c.get('is_correct')), None)
                    
                    if selected_choice:
                        if is_correct:
                            st.success(f"✓ Your answer: {selected_choice['choice_text']} (Correct)")
                        else:
                            st.error(f"✗ Your answer: {selected_choice['choice_text']} (Incorrect)")
                            if correct_choice:
                                st.info(f"✓ Correct answer: {correct_choice['choice_text']}")
                
                # Show hint
                if question.get('hint') and question.get('hint') != DEFAULT_HINT:
                    st.write(f"**💡 Hint:** {question['hint']}")
                
                # Show explanation
                if question.get('explanation') and question.get('explanation') != DEFAULT_EXPLANATION:
                    st.write(f"**📖 Explanation:** {question['explanation']}")
                
                st.divider()
            
            # Button to continue to next section
            if current_section_idx < len(sections) - 1:
                if st.button("Continue to Next Section", use_container_width=True, type="primary"):
                    st.session_state.current_section_idx = current_section_idx + 1
                    st.session_state.current_question_idx = 0
                    st.session_state.show_section_summary[section_key] = True
                    st.rerun()
            else:
                # Last section - show button to view final results
                if st.button("View Final Results", use_container_width=True, type="primary"):
                    st.session_state.show_results = True
                    st.rerun()
        
        elif not section_completed:
            # Show current question
            current_question_idx = st.session_state.current_question_idx
            if current_question_idx >= len(active_questions):
                current_question_idx = 0
                st.session_state.current_question_idx = 0
            
            current_question = active_questions[current_question_idx]
            
            # Section header
            st.subheader(f"Section {current_section_idx + 1}: {current_section.get('title', 'Untitled')}")
            if current_section.get('description'):
                st.write(current_section['description'])
            
            # Question progress
            progress = (current_question_idx + 1) / len(active_questions)
            st.progress(progress)
            st.caption(f"Question {current_question_idx + 1} of {len(active_questions)}")
            
            st.divider()
            
            # Display question
            st.markdown(f"### {current_question.get('question_text', '')}")
            
            choices = current_question.get('choices', [])
            if not choices:
                st.warning("No choices available for this question.")
                st.stop()
            
            question_id = current_question['id']
            previous_answer = user_answers.get(question_id)
            
            # Show hint if available and not answered yet
            if not previous_answer and current_question.get('hint') and current_question.get('hint') != DEFAULT_HINT:
                hint_col1, hint_col2 = st.columns([0.3, 0.7])
                with hint_col1:
                    show_hint = st.button("💡 Hint (click to reveal)", key=f"hint_btn_{question_id}", use_container_width=True)
                with hint_col2:
                    if show_hint:
                        st.markdown(f'<span style="display:inline-block;vertical-align:bottom; padding:0.25em 0.75em;border-radius:8px; font-size:1.2em;">`{current_question["hint"]}`</span>', unsafe_allow_html=True)
            
            # Answer buttons in 2 columns
            st.write("**Select your answer:**")
            
            # Randomize choices before displaying
            import random

            # Store a random order per-question (by question ID) in session state to ensure stable order per render
            random_choices_key = f"randomized_choices_{question_id}"
            if random_choices_key not in st.session_state:
                # Store the ids in a random order to preserve button keys consistent per rerun
                shuffled_choices = choices.copy()
                random.shuffle(shuffled_choices)
                st.session_state[random_choices_key] = [c['id'] for c in shuffled_choices]
            else:
                # Rebuild the random order with current choices (in case choices structure is dynamic)
                id_to_choice = {c['id']: c for c in choices}
                session_choice_ids = st.session_state[random_choices_key]
                # Only use ids still present in choices
                shuffled_choices = [id_to_choice[id_] for id_ in session_choice_ids if id_ in id_to_choice]
                # Add any new choices not in the stored shuffle (edge case handling)
                extra_choices = [c for c in choices if c['id'] not in session_choice_ids]
                shuffled_choices += extra_choices

            num_choices = len(shuffled_choices)
            for i in range(0, num_choices, 2):
                col1, col2 = st.columns(2)
                
                with col1:
                    choice1 = shuffled_choices[i]
                    button_key1 = f"answer_{question_id}_{choice1['id']}"
                    if st.button(choice1['choice_text'], key=button_key1, use_container_width=True):
                        # Submit answer and move to next question
                        is_correct = choice1.get('is_correct', False)
                        if submit_answer(user.id, question_id, choice1['id'], is_correct):
                            # Move to next question or next section
                            if current_question_idx < len(active_questions) - 1:
                                st.session_state.current_question_idx = current_question_idx + 1
                            else:
                                # Last question in section - will show summary on next render
                                pass
                            st.rerun()
                
                with col2:
                    if i + 1 < num_choices:
                        choice2 = shuffled_choices[i + 1]
                        button_key2 = f"answer_{question_id}_{choice2['id']}"
                        if st.button(choice2['choice_text'], key=button_key2, use_container_width=True):
                            # Submit answer and move to next question
                            is_correct = choice2.get('is_correct', False)
                            if submit_answer(user.id, question_id, choice2['id'], is_correct):
                                # Move to next question or next section
                                if current_question_idx < len(active_questions) - 1:
                                    st.session_state.current_question_idx = current_question_idx + 1
                                else:
                                    # Last question in section - will show summary on next render
                                    pass
                                st.rerun()
        
        else:
            # Section completed but summary not shown yet - this shouldn't happen, but handle it
            st.session_state.show_section_summary[section_key] = True
            st.rerun()
