-- Fix RLS policies for quizzes, sections, and questions
-- This creates SECURITY DEFINER functions that bypass RLS for admin operations
-- Run this in your Supabase SQL Editor

-- Function to create a quiz (bypasses RLS)
CREATE OR REPLACE FUNCTION public.create_quiz(
  p_title TEXT,
  p_description TEXT DEFAULT NULL,
  p_is_active BOOLEAN DEFAULT true
)
RETURNS UUID
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  v_quiz_id UUID;
BEGIN
  INSERT INTO public.quizzes (title, description, is_active)
  VALUES (p_title, p_description, p_is_active)
  RETURNING id INTO v_quiz_id;

  RETURN v_quiz_id;
END;
$$;

-- Function to create a section (bypasses RLS)
CREATE OR REPLACE FUNCTION public.create_section(
  p_quiz_id UUID,
  p_title TEXT,
  p_order_index INTEGER DEFAULT 0,
  p_description TEXT DEFAULT NULL
)
RETURNS UUID
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  v_section_id UUID;
BEGIN
  INSERT INTO public.sections (quiz_id, title, description, order_index)
  VALUES (p_quiz_id, p_title, p_description, p_order_index)
  RETURNING id INTO v_section_id;

  RETURN v_section_id;
END;
$$;

-- Function to create a question (bypasses RLS)
CREATE OR REPLACE FUNCTION public.create_question_with_choices(
  p_section_id UUID,
  p_question_text TEXT,
  p_is_active BOOLEAN DEFAULT true,
  p_order_index INTEGER DEFAULT 0,
  p_hint TEXT DEFAULT 'there is no hint for this question',
  p_explanation TEXT DEFAULT 'there is no explanation for this question',
  p_choices JSONB
)
RETURNS UUID
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  v_question_id UUID;
  choice_item JSONB;
BEGIN
  -- Insert question
  INSERT INTO public.questions (
    section_id, question_text, hint, explanation, is_active, order_index
  )
  VALUES (
    p_section_id, p_question_text, p_hint, p_explanation, p_is_active, p_order_index
  )
  RETURNING id INTO v_question_id;

  -- Insert choices
  FOR choice_item IN SELECT * FROM jsonb_array_elements(p_choices)
  LOOP
    INSERT INTO public.choices (question_id, choice_text, is_correct)
    VALUES (
      v_question_id,
      choice_item->>'choice_text',
      (choice_item->>'is_correct')::BOOLEAN
    );
  END LOOP;

  RETURN v_question_id;
END;
$$;

-- Grant execute permissions to authenticated users
GRANT EXECUTE ON FUNCTION public.create_quiz TO authenticated;
GRANT EXECUTE ON FUNCTION public.create_section TO authenticated;
GRANT EXECUTE ON FUNCTION public.create_question_with_choices TO authenticated;

-- Also grant to anon (since we're using anon key)
GRANT EXECUTE ON FUNCTION public.create_quiz TO anon;
GRANT EXECUTE ON FUNCTION public.create_section TO anon;
GRANT EXECUTE ON FUNCTION public.create_question_with_choices TO anon;

-- Alternative: Update RLS policies to allow inserts if user is admin
-- But this requires auth.uid() which won't work with bypass_auth
-- So the function approach above is better

-- If you prefer to fix RLS policies instead, you can drop the insert policies
-- and create new ones that don't check auth.uid() but this is less secure
-- DROP POLICY IF EXISTS "Admins can insert quizzes" ON quizzes;
-- CREATE POLICY "Allow quiz inserts" ON quizzes FOR INSERT WITH CHECK (true);

