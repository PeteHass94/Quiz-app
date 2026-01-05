"""
Quiz helper functions for database operations.
"""
import streamlit as st
from lib.supabase_client import get_client
from datetime import datetime

# Default values
DEFAULT_HINT = "there is no hint for this question"
DEFAULT_EXPLANATION = "there is no explanation for this question"


def get_all_questions():
    """Get all questions with their answer choices."""
    supabase = get_client()
    try:
        # Get questions with their choices
        questions = supabase.table("questions").select("*, choices(*)").order("created_at", desc=True).execute()
        return questions.data
    except Exception as e:
        st.error(f"Error fetching questions: {e}")
        return []


def get_active_questions():
    """Get all active questions from all active quizzes (for backward compatibility)."""
    supabase = get_client()
    try:
        # Get all active quizzes
        active_quizzes = supabase.table("quizzes").select("id").eq("is_active", True).execute()
        quiz_ids = [q["id"] for q in active_quizzes.data]
        
        if not quiz_ids:
            return []
        
        # Get all sections from active quizzes
        sections = supabase.table("sections").select("id").in_("quiz_id", quiz_ids).execute()
        section_ids = [s["id"] for s in sections.data]
        
        if not section_ids:
            return []
        
        # Get all active questions from those sections
        questions = supabase.table("questions").select("*, choices(*)").eq("is_active", True).in_("section_id", section_ids).order("created_at", desc=True).execute()
        return questions.data
    except Exception as e:
        st.error(f"Error fetching active questions: {e}")
        return []


def create_quiz(title: str, description: str = "", is_active: bool = True):
    """Create a new quiz using database function to bypass RLS."""
    supabase = get_client()
    try:
        # Use database function to bypass RLS
        result = supabase.rpc(
            "create_quiz",
            {
                "p_title": title,
                "p_description": description if description else None,
                "p_is_active": is_active
            }
        ).execute()
        # RPC returns the UUID directly
        if result.data:
            return result.data
        return result.data[0] if isinstance(result.data, list) else result.data
    except Exception as e:
        # Fallback to direct insert if function doesn't exist
        try:
            result = supabase.table("quizzes").insert({
                "title": title,
                "description": description,
                "is_active": is_active
            }).execute()
            return result.data[0]["id"]
        except Exception as e2:
            st.error(f"Error creating quiz: {e2}")
            raise

def get_all_quizzes():
    """Get all quizzes."""
    supabase = get_client()
    try:
        result = supabase.table("quizzes").select("*").order("created_at", desc=True).execute()
        return result.data
    except Exception as e:
        st.error(f"Error fetching quizzes: {e}")
        return []

def get_active_quizzes():
    """Get only active quizzes."""
    supabase = get_client()
    try:
        result = supabase.table("quizzes").select("*").eq("is_active", True).order("created_at", desc=True).execute()
        return result.data
    except Exception as e:
        st.error(f"Error fetching active quizzes: {e}")
        return []

def create_section(quiz_id: str, title: str, description: str = "", order_index: int = 0):
    """Create a new section within a quiz using database function to bypass RLS."""
    supabase = get_client()
    try:
        # Use database function to bypass RLS
        result = supabase.rpc(
            "create_section",
            {
                "p_quiz_id": quiz_id,
                "p_title": title,
                "p_description": description if description else None,
                "p_order_index": order_index
            }
        ).execute()
        # RPC returns the UUID directly
        if result.data:
            return result.data if not isinstance(result.data, list) else result.data[0]
        return result.data
    except Exception as e:
        # Fallback to direct insert if function doesn't exist
        try:
            result = supabase.table("sections").insert({
                "quiz_id": quiz_id,
                "title": title,
                "description": description,
                "order_index": order_index
            }).execute()
            return result.data[0]["id"]
        except Exception as e2:
            st.error(f"Error creating section: {e2}")
            raise

def get_sections_by_quiz(quiz_id: str):
    """Get all sections for a specific quiz."""
    supabase = get_client()
    try:
        result = supabase.table("sections").select("*").eq("quiz_id", quiz_id).order("order_index", desc=False).execute()
        return result.data
    except Exception as e:
        st.error(f"Error fetching sections: {e}")
        return []

def create_question(section_id: str, question_text: str, choices: list, correct_choice_index: int, 
                   hint: str = DEFAULT_HINT, explanation: str = DEFAULT_EXPLANATION, 
                   is_active: bool = True, order_index: int = 0):
    """Create a new question with choices within a section.
    
    Args:
        section_id: ID of the section this question belongs to
        question_text: The question text
        choices: List of choice text strings
        correct_choice_index: 0-based index of the correct choice in the choices list
        hint: Optional hint text
        explanation: Optional explanation text
        is_active: Whether the question is active
        order_index: Order index for sorting
        
    Returns:
        The ID of the created question
    """
    supabase = get_client()
    try:
        # Validate correct_choice_index
        if correct_choice_index < 0 or correct_choice_index >= len(choices):
            raise ValueError(f"Invalid correct_choice_index: {correct_choice_index}. Must be between 0 and {len(choices)-1}")
        
        # Insert question
        question_result = supabase.table("questions").insert({
            "section_id": section_id,
            "question_text": question_text,
            "hint": hint if hint else DEFAULT_HINT,
            "explanation": explanation if explanation else DEFAULT_EXPLANATION,
            "is_active": is_active,
            "order_index": order_index
        }).execute()
        
        question_id = question_result.data[0]["id"]
        
        # Insert choices - mark the one at correct_choice_index as correct
        choices_data = []
        for i, choice_text in enumerate(choices):
            is_correct = (i == correct_choice_index)
            choices_data.append({
                "question_id": question_id,
                "choice_text": choice_text,
                "is_correct": is_correct
            })
        
        supabase.table("choices").insert(choices_data).execute()
        
        return question_id
    except Exception as e:
        st.error(f"Error creating question: {e}")
        raise

def get_questions_by_section(section_id: str):
    """Get all questions for a specific section."""
    supabase = get_client()
    try:
        # Get questions
        questions_result = supabase.table("questions").select("*").eq("section_id", section_id).order("order_index", desc=False).execute()
        questions = questions_result.data
        
        # Get choices for these questions
        if questions:
            question_ids = [q['id'] for q in questions]
            choices_result = supabase.table("choices").select("*").in_("question_id", question_ids).execute()
            choices_map = {}
            for c in choices_result.data:
                q_id = c.get('question_id')
                if q_id not in choices_map:
                    choices_map[q_id] = []
                choices_map[q_id].append(c)
            
            # Add choices to questions
            for q in questions:
                q['choices'] = choices_map.get(q['id'], [])
        
        return questions
    except Exception as e:
        st.error(f"Error fetching questions: {e}")
        return []

def update_question(question_id: str, question_text: str = None, hint: str = None, 
                   explanation: str = None, is_active: bool = None, order_index: int = None):
    """Update a question's properties."""
    supabase = get_client()
    try:
        update_data = {}
        if question_text is not None:
            update_data["question_text"] = question_text
        if hint is not None:
            update_data["hint"] = hint
        if explanation is not None:
            update_data["explanation"] = explanation
        if is_active is not None:
            update_data["is_active"] = is_active
        if order_index is not None:
            update_data["order_index"] = order_index
        
        if update_data:
            supabase.table("questions").update(update_data).eq("id", question_id).execute()
        return True
    except Exception as e:
        st.error(f"Error updating question: {e}")
        return False

def update_choice(choice_id: str, choice_text: str = None, is_correct: bool = None):
    """Update a choice's properties."""
    supabase = get_client()
    try:
        update_data = {}
        if choice_text is not None:
            update_data["choice_text"] = choice_text
        if is_correct is not None:
            update_data["is_correct"] = is_correct
        
        if update_data:
            supabase.table("choices").update(update_data).eq("id", choice_id).execute()
        return True
    except Exception as e:
        st.error(f"Error updating choice: {e}")
        return False

def set_correct_answer(question_id: str, correct_choice_id: str):
    """Set which choice is the correct answer for a question."""
    supabase = get_client()
    try:
        # First, set all choices for this question to incorrect
        supabase.table("choices").update({"is_correct": False}).eq("question_id", question_id).execute()
        
        # Then set the specified choice as correct
        supabase.table("choices").update({"is_correct": True}).eq("id", correct_choice_id).execute()
        
        return True
    except Exception as e:
        st.error(f"Error setting correct answer: {e}")
        return False

def get_quiz_structure(quiz_id: str):
    """Get full quiz structure with sections and questions."""
    supabase = get_client()
    try:
        # Get quiz
        quiz = supabase.table("quizzes").select("*").eq("id", quiz_id).single().execute()
        
        # Get sections
        sections = supabase.table("sections").select("*").eq("quiz_id", quiz_id).order("order_index", desc=False).execute()
        
        # Get questions for each section
        for section in sections.data:
            questions = supabase.table("questions").select("*, choices(*)").eq("section_id", section["id"]).order("order_index", desc=False).execute()
            section["questions"] = questions.data
        
        return {
            "quiz": quiz.data,
            "sections": sections.data
        }
    except Exception as e:
        st.error(f"Error fetching quiz structure: {e}")
        return None


def submit_answer(user_id: str, question_id: str, choice_id: str, is_correct: bool):
    """Submit a user's answer to a question."""
    supabase = get_client()
    try:
        # Check if user already answered this question
        existing = supabase.table("user_answers").select("*").eq("user_id", user_id).eq("question_id", question_id).execute()
        
        if existing.data:
            # Update existing answer
            supabase.table("user_answers").update({
                "choice_id": choice_id,
                "is_correct": is_correct,
                "answered_at": datetime.utcnow().isoformat()
            }).eq("user_id", user_id).eq("question_id", question_id).execute()
        else:
            # Insert new answer
            supabase.table("user_answers").insert({
                "user_id": user_id,
                "question_id": question_id,
                "choice_id": choice_id,
                "is_correct": is_correct,
                "answered_at": datetime.utcnow().isoformat()
            }).execute()
        
        return True
    except Exception as e:
        st.error(f"Error submitting answer: {e}")
        return False


def get_user_score(user_id: str):
    """Get user's total score (number of correct answers)."""
    supabase = get_client()
    try:
        result = supabase.table("user_answers").select("is_correct").eq("user_id", user_id).eq("is_correct", True).execute()
        return len(result.data)
    except Exception as e:
        st.error(f"Error fetching user score: {e}")
        return 0


def get_user_answers(user_id: str):
    """Get all answers submitted by a user with related question and choice data."""
    supabase = get_client()
    try:
        # First get user answers - no nested selects
        answers_result = supabase.table("user_answers").select("*").eq("user_id", user_id).execute()
        answers = answers_result.data
        
        if not answers:
            return []
        
        # Get unique question IDs and choice IDs
        question_ids = [ans['question_id'] for ans in answers if ans.get('question_id')]
        choice_ids = [ans['choice_id'] for ans in answers if ans.get('choice_id')]
        
        question_ids = list(set(question_ids))
        choice_ids = list(set(choice_ids))
        
        # Fetch questions separately (no nested selects)
        questions_data = {}
        if question_ids:
            questions_result = supabase.table("questions").select("*").in_("id", question_ids).execute()
            for q in questions_result.data:
                questions_data[q['id']] = q
        
        # Fetch choices for those questions (separate query)
        question_choices_map = {}
        if question_ids:
            choices_for_questions = supabase.table("choices").select("*").in_("question_id", question_ids).execute()
            for c in choices_for_questions.data:
                q_id = c.get('question_id')
                if q_id not in question_choices_map:
                    question_choices_map[q_id] = []
                question_choices_map[q_id].append(c)
        
        # Add choices to questions data
        for q_id, choices_list in question_choices_map.items():
            if q_id in questions_data:
                questions_data[q_id]['choices'] = choices_list
        
        # Fetch choices separately by ID (as fallback)
        choices_data = {}
        if choice_ids:
            choices_result = supabase.table("choices").select("*").in_("id", choice_ids).execute()
            for c in choices_result.data:
                choices_data[c['id']] = c
        
        # Combine the data
        enriched_answers = []
        for answer in answers:
            question_id = answer.get('question_id')
            choice_id = answer.get('choice_id')
            
            enriched_answer = answer.copy()
            enriched_answer['questions'] = questions_data.get(question_id, {})
            
            # Get choice from question's choices or from choices_data
            choice = None
            if question_id and question_id in questions_data:
                question_choices = questions_data[question_id].get('choices', [])
                if question_choices:
                    choice = next((c for c in question_choices if c.get('id') == choice_id), None)
            
            if not choice and choice_id:
                choice = choices_data.get(choice_id, {})
            
            enriched_answer['choices'] = choice if choice else {}
            enriched_answers.append(enriched_answer)
        
        return enriched_answers
    except Exception as e:
        # Don't show error if it's just that user has no answers yet
        error_msg = str(e)
        if "relationship" not in error_msg.lower() and "PGRST200" not in error_msg:
            st.error(f"Error fetching user answers: {e}")
        return []


def get_leaderboard(limit: int = 100):
    """Get leaderboard with user scores and ranks."""
    supabase = get_client()
    try:
        # Get all users with their correct answer counts
        # Using a raw query approach - count correct answers per user
        all_answers = supabase.table("user_answers").select("user_id, is_correct").execute()
        
        # Calculate scores
        user_scores = {}
        for answer in all_answers.data:
            user_id = answer["user_id"]
            if answer["is_correct"]:
                user_scores[user_id] = user_scores.get(user_id, 0) + 1
        
        # Get user profiles
        if user_scores:
            user_ids = list(user_scores.keys())
            profiles = supabase.table("profiles").select("id, full_name, email").in_("id", user_ids).execute()
            profile_map = {p["id"]: p for p in profiles.data}
        else:
            profile_map = {}
        
        # Build leaderboard
        leaderboard = []
        for user_id, score in user_scores.items():
            profile = profile_map.get(user_id, {})
            leaderboard.append({
                "user_id": user_id,
                "full_name": profile.get("full_name", "Unknown"),
                "email": profile.get("email", ""),
                "score": score
            })
        
        # Sort by score descending
        leaderboard.sort(key=lambda x: x["score"], reverse=True)
        
        # Add ranks
        for i, entry in enumerate(leaderboard):
            entry["rank"] = i + 1
        
        return leaderboard[:limit]
    except Exception as e:
        st.error(f"Error fetching leaderboard: {e}")
        return []


def get_user_rank(user_id: str):
    """Get user's rank on the leaderboard."""
    leaderboard = get_leaderboard()
    for entry in leaderboard:
        if entry["user_id"] == user_id:
            return entry["rank"]
    return None


def get_all_scores():
    """Get all user scores for admin view."""
    return get_leaderboard(limit=1000)


def get_group_leaderboard(group_name: str, limit: int = 100):
    """Get leaderboard for a specific group."""
    supabase = get_client()
    try:
        # Get all users in the group with their correct answer counts
        all_answers = supabase.table("user_answers").select("user_id, is_correct").execute()
        
        # Calculate scores
        user_scores = {}
        for answer in all_answers.data:
            user_id = answer["user_id"]
            if answer["is_correct"]:
                user_scores[user_id] = user_scores.get(user_id, 0) + 1
        
        # Get user profiles for the group
        if user_scores:
            user_ids = list(user_scores.keys())
            profiles = supabase.table("profiles").select("id, full_name, email, group").in_("id", user_ids).eq("group", group_name).execute()
            profile_map = {p["id"]: p for p in profiles.data}
        else:
            profile_map = {}
        
        # Build leaderboard for the group
        leaderboard = []
        for user_id, score in user_scores.items():
            profile = profile_map.get(user_id)
            if profile:  # Only include users in this group
                leaderboard.append({
                    "user_id": user_id,
                    "full_name": profile.get("full_name", "Unknown"),
                    "email": profile.get("email", ""),
                    "score": score,
                    "group": profile.get("group", "uncategorised")
                })
        
        # Sort by score descending
        leaderboard.sort(key=lambda x: x["score"], reverse=True)
        
        # Add ranks
        for i, entry in enumerate(leaderboard):
            entry["rank"] = i + 1
        
        return leaderboard[:limit]
    except Exception as e:
        st.error(f"Error fetching group leaderboard: {e}")
        return []


def get_user_group_rank(user_id: str, group_name: str):
    """Get user's rank within their group."""
    if not group_name or group_name == "uncategorised":
        return None
    leaderboard = get_group_leaderboard(group_name)
    for entry in leaderboard:
        if entry["user_id"] == user_id:
            return entry["rank"]
    return None


def get_quiz_leaderboard(quiz_id: str, limit: int = 100):
    """Get leaderboard for a specific quiz with scores and last answer date."""
    supabase = get_client()
    try:
        # Get all sections for this quiz
        sections_result = supabase.table("sections").select("id").eq("quiz_id", quiz_id).execute()
        section_ids = [s["id"] for s in sections_result.data]
        
        if not section_ids:
            return []
        
        # Get all questions for these sections
        questions_result = supabase.table("questions").select("id").in_("section_id", section_ids).execute()
        question_ids = [q["id"] for q in questions_result.data]
        
        if not question_ids:
            return []
        
        # Get all answers for these questions
        all_answers = supabase.table("user_answers").select("user_id, is_correct, answered_at").in_("question_id", question_ids).execute()
        
        # Calculate scores per user and get last answer date
        user_scores = {}
        user_last_dates = {}
        
        for answer in all_answers.data:
            user_id = answer["user_id"]
            if answer["is_correct"]:
                user_scores[user_id] = user_scores.get(user_id, 0) + 1
            
            # Track last answer date
            answered_at = answer.get("answered_at")
            if answered_at:
                if user_id not in user_last_dates or answered_at > user_last_dates[user_id]:
                    user_last_dates[user_id] = answered_at
        
        # Get user profiles
        if user_scores:
            user_ids = list(user_scores.keys())
            profiles = supabase.table("profiles").select("id, full_name, email").in_("id", user_ids).execute()
            profile_map = {p["id"]: p for p in profiles.data}
        else:
            profile_map = {}
        
        # Build leaderboard
        leaderboard = []
        for user_id, score in user_scores.items():
            profile = profile_map.get(user_id, {})
            leaderboard.append({
                "user_id": user_id,
                "full_name": profile.get("full_name", "Unknown"),
                "email": profile.get("email", ""),
                "score": score,
                "last_answer_date": user_last_dates.get(user_id, "")
            })
        
        # Sort by score descending
        leaderboard.sort(key=lambda x: x["score"], reverse=True)
        
        # Add ranks
        for i, entry in enumerate(leaderboard):
            entry["rank"] = i + 1
        
        return leaderboard[:limit]
    except Exception as e:
        st.error(f"Error fetching quiz leaderboard: {e}")
        return []


def get_leaderboard_with_dates(limit: int = 100):
    """Get overall leaderboard with last answer dates."""
    supabase = get_client()
    try:
        # Get all answers with dates
        all_answers = supabase.table("user_answers").select("user_id, is_correct, answered_at").execute()
        
        # Calculate scores and track last answer dates
        user_scores = {}
        user_last_dates = {}
        
        for answer in all_answers.data:
            user_id = answer["user_id"]
            if answer["is_correct"]:
                user_scores[user_id] = user_scores.get(user_id, 0) + 1
            
            # Track last answer date
            answered_at = answer.get("answered_at")
            if answered_at:
                if user_id not in user_last_dates or answered_at > user_last_dates[user_id]:
                    user_last_dates[user_id] = answered_at
        
        # Get user profiles
        if user_scores:
            user_ids = list(user_scores.keys())
            profiles = supabase.table("profiles").select("id, full_name, email").in_("id", user_ids).execute()
            profile_map = {p["id"]: p for p in profiles.data}
        else:
            profile_map = {}
        
        # Build leaderboard
        leaderboard = []
        for user_id, score in user_scores.items():
            profile = profile_map.get(user_id, {})
            leaderboard.append({
                "user_id": user_id,
                "full_name": profile.get("full_name", "Unknown"),
                "email": profile.get("email", ""),
                "score": score,
                "last_answer_date": user_last_dates.get(user_id, "")
            })
        
        # Sort by score descending
        leaderboard.sort(key=lambda x: x["score"], reverse=True)
        
        # Add ranks
        for i, entry in enumerate(leaderboard):
            entry["rank"] = i + 1
        
        return leaderboard[:limit]
    except Exception as e:
        st.error(f"Error fetching leaderboard: {e}")
        return []


def get_question_stats():
    """Get statistics about questions for admin."""
    supabase = get_client()
    try:
        total_questions = supabase.table("questions").select("id", count="exact").execute()
        active_questions = supabase.table("questions").select("id", count="exact").eq("is_active", True).execute()
        total_answers = supabase.table("user_answers").select("id", count="exact").execute()
        
        return {
            "total_questions": total_questions.count if hasattr(total_questions, 'count') else len(total_questions.data),
            "active_questions": active_questions.count if hasattr(active_questions, 'count') else len(active_questions.data),
            "total_answers": total_answers.count if hasattr(total_answers, 'count') else len(total_answers.data)
        }
    except Exception as e:
        st.error(f"Error fetching stats: {e}")
        return {"total_questions": 0, "active_questions": 0, "total_answers": 0}

