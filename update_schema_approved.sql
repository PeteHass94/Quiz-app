-- Add approved column to profiles table
-- Run this in your Supabase SQL Editor

ALTER TABLE profiles ADD COLUMN IF NOT EXISTS approved BOOLEAN DEFAULT false;

-- Update existing users to be approved (optional - only if you want existing users to remain active)
-- UPDATE profiles SET approved = true WHERE approved IS NULL OR approved = false;

-- Make sure admins are approved
UPDATE profiles SET approved = true WHERE role = 'admin';

