# Quiz Structure Guide

The quiz system now supports a hierarchical structure:

## Structure

```
Quiz
  └── Section 1
      └── Question 1
          └── Choice 1 (correct)
          └── Choice 2
          └── Choice 3
          └── Choice 4
      └── Question 2
          └── ...
  └── Section 2
      └── Question 1
      └── ...
```

## Creating a Quiz (Admin)

### Step 1: Create Quiz
1. Go to Admin page → "Create Quiz" tab
2. Enter quiz title and description
3. Set active status
4. Click "Create Quiz"

### Step 2: Add Sections
1. Select the quiz you just created
2. Click "Add New Section"
3. Enter section title and description
4. Set order index (for ordering sections)
5. Click "Add Section"

### Step 3: Add Questions
1. Select a section
2. Click "Add New Question to Section"
3. Enter question text
4. Add 2-4 answer choices
5. Select which choice is correct
6. Add hint (optional, defaults to "there is no hint for this question")
7. Add explanation (optional, defaults to "there is no explanation for this question")
8. Set order index and active status
9. Click "Create Question"

## Question Features

### Hints
- Optional field
- Default: "there is no hint for this question"
- Shown to users before they answer (in an expandable section)
- Users can click to reveal the hint

### Explanations
- Optional field
- Default: "there is no explanation for this question"
- Shown to users after they answer
- Helps users understand why an answer is correct/incorrect

### Choices
- Each question must have at least 2 choices
- Only 1 choice can be marked as correct
- Choices are displayed as radio buttons

## User Experience

1. Users select a quiz from the dropdown
2. Quiz displays all sections in order
3. Each section shows its questions
4. Users can:
   - View hints (before answering)
   - Select an answer
   - Submit their answer
   - See if they were correct/incorrect
   - View explanations (after answering)

## Database Tables

- `quizzes` - Top level quiz container
- `sections` - Sections within quizzes
- `questions` - Questions within sections (now has `section_id` and `hint` fields)
- `choices` - Answer choices for questions

## Migration

Run `migrate_to_quiz_structure.sql` in your Supabase SQL Editor to:
- Create new tables
- Add new columns to existing tables
- Set up RLS policies

