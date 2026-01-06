"""
Quiz History Page - Shows completed sections
"""
import streamlit as st
from lib.auth import get_current_user
from lib.quiz import get_user_answers, get_all_quizzes, get_quiz_structure, DEFAULT_HINT, DEFAULT_EXPLANATION

st.set_page_config(page_title="Quiz History", page_icon="📚", layout="wide")

from lib.navigation import render_sidebar_navigation
render_sidebar_navigation()

# Check authentication
user, sess = get_current_user()
if not user:
    from lib.login_component import show_login_section
    show_login_section()
    st.stop()

st.title("📚 Quiz History")

# Helper function to check if section is completed
def is_section_completed(section, user_answers):
    """Check if all active questions in a section have been answered."""
    questions = section.get('questions', [])
    active_questions = [q for q in questions if q.get('is_active', True)]
    if not active_questions:
        return False  # Don't show sections with no questions
    for question in active_questions:
        if question['id'] not in user_answers:
            return False
    return True

# Helper function to get section score
def get_section_score(section, user_answers):
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

# Get all quizzes and user answers
all_quizzes = get_all_quizzes()
user_answers = {ans['question_id']: ans for ans in get_user_answers(user.id)}

if not user_answers:
    st.info("You haven't answered any questions yet. Go to 'Take Quiz' to get started!")
    st.stop()

# Get completed sections for each quiz
completed_sections_data = []

for quiz in all_quizzes:
    quiz_data = get_quiz_structure(quiz['id'])
    if not quiz_data or not quiz_data.get('sections'):
        continue
    
    sections = quiz_data['sections']
    quiz_completed_sections = []
    
    for section in sections:
        if is_section_completed(section, user_answers):
            quiz_completed_sections.append({
                'quiz': quiz,
                'section': section
            })
    
    if quiz_completed_sections:
        completed_sections_data.extend(quiz_completed_sections)

if not completed_sections_data:
    st.info("You haven't completed any sections yet. Complete a section in 'Take Quiz' to see your history here!")
    st.stop()

# Display completed sections grouped by quiz
st.write(f"**Completed Sections:** {len(completed_sections_data)}")
st.divider()

# Group by quiz
current_quiz_id = None
for item in completed_sections_data:
    quiz = item['quiz']
    section = item['section']
    
    # Show quiz header when quiz changes
    if current_quiz_id != quiz['id']:
        if current_quiz_id is not None:
            st.divider()
        st.header(f"📝 {quiz.get('title', 'Untitled Quiz')}")
        if quiz.get('description'):
            st.write(quiz.get('description'))
        current_quiz_id = quiz['id']
    
    # Show section results
    st.subheader(f"Section: {section.get('title', 'Untitled')}")
    
    questions = section.get('questions', [])
    active_questions = [q for q in questions if q.get('is_active', True)]
    
    if not active_questions:
        continue
    
    section_correct, section_total = get_section_score(section, user_answers)
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
