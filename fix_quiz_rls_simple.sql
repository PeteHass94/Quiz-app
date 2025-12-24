-- SIMPLER FIX: Just update RLS policies to allow inserts
-- This is less secure but works immediately without functions
-- Run this in your Supabase SQL Editor

-- Drop existing insert policies
DROP POLICY IF EXISTS "Admins can insert quizzes" ON quizzes;
DROP POLICY IF EXISTS "Admins can insert sections" ON sections;

-- Create simpler policies that allow inserts (less secure but works with bypass_auth)
-- NOTE: This allows ANY authenticated user to insert. For better security, use the function approach.
CREATE POLICY "Allow quiz inserts"
  ON quizzes FOR INSERT
  WITH CHECK (true);

CREATE POLICY "Allow section inserts"
  ON sections FOR INSERT
  WITH CHECK (true);

-- For questions and choices, keep the existing approach or update similarly
-- DROP POLICY IF EXISTS "Admins can insert choices" ON choices;
-- CREATE POLICY "Allow choice inserts" ON choices FOR INSERT WITH CHECK (true);

-- If you want better security, use the function approach in fix_quiz_rls.sql instead

