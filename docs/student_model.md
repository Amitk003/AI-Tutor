# Student Modeling, Adaptive Intelligence & Assessment Specification
## Adaptive AI Learning Platform

---

## 1. Subsystem Overview

The Adaptive Assessment & Quiz Engine consumes outputs from the Adaptive Tutor, Student Model ($\theta$), IRT, BKT ($P(L)$), SM-2, and Concept Graph to generate schema-constrained adaptive quiz items and update psychometrics:

```
[Adaptive Tutor & Student Model State]
(Theta θ, Mastery P(L), Weak Topics, Revision Queue)
          │
          ▼
   [QuizPlanner]
   (Plans assessment objectives & targets difficulty θ ± 0.30)
          │
          ▼
   [QuestionGenerator & Pydantic Validator]
   (Generates schema-constrained items: MCQ, Multiple Select, True/False, Fill Blank, Short Answer, Code)
          │
          ▼
   [Distractor Generator]
   (Generates plausible wrong options with misconception representations)
          │
          ▼
   [QuizEvaluator & Psychometric Synchronizer]
   (Evaluates answer correctness and updates IRT θ, BKT P(L), and SM-2 in PostgreSQL)
```

---

## 2. Question Types & JSON Schema Validation

All generated questions adhere strictly to the `QuestionSchema` Pydantic model:

```json
{
  "question_id": "uuid-string",
  "question_type": "MCQ | MULTIPLE_SELECT | TRUE_FALSE | FILL_BLANK | SHORT_ANSWER | CODE_COMPLETION",
  "question_text": "Prompt text...",
  "code_snippet": "Optional code block...",
  "correct_answer": "Exact correct answer choice...",
  "distractors": [
    {
      "option_text": "Plausible wrong choice...",
      "misconception_represented": "Specific conceptual flaw...",
      "explanation": "Why this choice is incorrect..."
    }
  ],
  "calibrated_difficulty": 0.50,
  "explanation": "Detailed explanation why the correct answer is right..."
}
```

---

## 3. Quiz Domain Events Matrix

| Event Name | Trigger Condition | Payload Properties |
| :--- | :--- | :--- |
| `QuizStarted` | Quiz session initialized | `user_id`, `quiz_id`, `concept_name`, `target_difficulty` |
| `QuestionGenerated` | Calibrated question generated | `quiz_id`, `question_type`, `calibrated_difficulty` |
| `QuestionAnswered` | Student submits answer | `user_id`, `quiz_id`, `question_id`, `is_correct`, `time_spent_seconds` |
| `QuizCompleted` | All quiz items answered | `user_id`, `quiz_id`, `score_percentage`, `total_questions` |
| `AssessmentUpdated` | Psychometric models recalibrated | `user_id`, `new_theta`, `new_mastery` |
