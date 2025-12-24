# 🧠 Quiz App

A Streamlit-based quiz application with Supabase backend for authentication and data storage.

## Features

### User Features
- ✅ User registration and login
- ✅ Create and manage profile
- ✅ Take quizzes by answering questions
- ✅ View personal score and rank
- ✅ See leaderboard
- ✅ View answer history

### Admin Features
- ✅ Admin login (role-based access)
- ✅ Add new questions with multiple choice answers
- ✅ View all user scores and leaderboard
- ✅ View statistics (total questions, answers, etc.)
- ✅ Manage question visibility (active/inactive)

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Supabase

1. Create a Supabase project at [supabase.com](https://supabase.com)
2. Go to Project Settings > API to get your:
   - Project URL
   - Anon (public) key

### 3. Configure Streamlit Secrets

Create a `.streamlit/secrets.toml` file in your project root:

```toml
[supabase]
url = "your-supabase-project-url"
anon_key = "your-supabase-anon-key"
```

### 4. Set Up Database Schema

Run the SQL commands from `DATABASE_SCHEMA.md` in your Supabase SQL Editor to create the required tables and Row Level Security (RLS) policies.

**Important:** Make sure to:
- Enable Row Level Security (RLS) on all tables
- Create all the policies as described in `DATABASE_SCHEMA.md`
- Set up at least one admin user by updating the `profiles` table

### 5. Create an Admin User

After signing up a user account, make them an admin by running this SQL in Supabase:

```sql
UPDATE profiles
SET role = 'admin'
WHERE email = 'your-admin-email@example.com';
```

### 6. Run the App

```bash
streamlit run streamlit_app.py
```

## Project Structure

```
Quiz-app/
├── streamlit_app.py          # Main app entry point
├── pages/
│   ├── 01_Admin.py           # Admin dashboard
│   └── 02_Dashboard.py       # User dashboard
├── lib/
│   ├── auth.py               # Authentication functions
│   ├── supabase_client.py   # Supabase client setup
│   └── quiz.py               # Quiz-related database operations
├── DATABASE_SCHEMA.md        # Database setup instructions
└── requirements.txt          # Python dependencies
```

## Database Tables

- `profiles` - User profiles with roles (user/admin)
- `questions` - Quiz questions
- `choices` - Answer choices for questions
- `user_answers` - User submissions and scores

See `DATABASE_SCHEMA.md` for detailed schema and RLS policies.

## Usage

1. **For Users:**
   - Sign up or log in on the main page
   - Answer questions on the main quiz interface
   - View your score and rank on the Dashboard page

2. **For Admins:**
   - Log in with an admin account
   - Go to the Admin page (from sidebar)
   - Add questions in the "Manage Questions" tab
   - View all scores in the "View Scores" tab
   - Check statistics in the "Statistics" tab

## Notes

- Users can only answer each question once (but can update their answer)
- Only active questions are visible to regular users
- Admins can see all questions regardless of active status
- Scores are calculated based on correct answers
- Leaderboard ranks users by total correct answers
