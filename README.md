# Skill Learning AI Agent (LangGraph + PostgreSQL)

This project provides a chatbot-style AI learning coach that:

- asks for skill-learning inputs (target skill, level, weekly time, timeline, goal)
- generates a skill tree and weekly timetable
- recommends resources (YouTube, websites, books)
- stores plan and schedule in PostgreSQL
- tracks learning progress by task completion
- includes a built-in web chatbot UI

## Tech Stack

- FastAPI (API layer)
- LangGraph (agent conversation flow)
- PostgreSQL + SQLAlchemy (storage)
- Gemini via LangChain (optional personalized planner)

## Project Structure

- `app/main.py` - FastAPI app startup
- `app/agent/graph.py` - LangGraph conversation workflow
- `app/services/planner.py` - LLM-personalized skill tree + timetable generator (with fallback)
- `app/services/learning_service.py` - business logic and persistence flow
- `app/db/models.py` - PostgreSQL models
- `app/api/routes.py` - REST endpoints
- `app/static/` - frontend chatbot UI files

## Setup (Without Docker)

1. Create a PostgreSQL database named `skill_agent`.
2. Copy `.env.example` to `.env` and adjust `DATABASE_URL`.
3. (Optional) Add `GOOGLE_API_KEY` for personalized LLM plans. Without it, fallback planner is used.
4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Run the API:

```bash
uvicorn app.main:app --reload
```

Server starts at `http://127.0.0.1:8000` by default.

UI is available at `http://127.0.0.1:8000/app`.

## API Flow

1. Chat to collect profile

POST `/api/chat`

```json
{
  "learner_name": "Tusha",
  "message": "skill: Python"
}
```

Keep chatting until `ready_for_plan` is `true`.

2. Generate the learning plan

POST `/api/plans`

```json
{
  "learner_id": 1
}
```

3. List tasks in the generated timetable

GET `/api/plans/{plan_id}/tasks`

4. Update task completion

PATCH `/api/tasks/{task_id}/progress`

```json
{
  "completed": true
}
```

5. View learner progress summary

GET `/api/learners/{learner_id}/plans/{plan_id}/progress`

## Notes

- Planner mode is automatic:
  - If `GOOGLE_API_KEY` is present, the plan/resources are personalized via Gemini (`gemini-2.5-flash-lite` by default).
  - If not, deterministic fallback planning is used.
