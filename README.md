# AI Interview Preparation System

A complete full-stack interview practice platform built with FastAPI, SQLAlchemy, SQLite/PostgreSQL support, JWT authentication, and a static HTML/CSS/JavaScript frontend.

## Features

- User registration and login with bcrypt password hashing and JWT-protected APIs
- Dynamic interview generation for Software Engineer, Data Scientist, and Web Developer roles
- Difficulty levels: Easy, Medium, and Hard
- Timed interview sessions with local draft persistence
- AI answer evaluation using the OpenAI API with a deterministic mock fallback
- Interview history, retry attempts, and dashboard-based progress tracking
- SQLite by default with PostgreSQL support through `DATABASE_URL`
- CORS enabled through environment configuration

## Project Structure

```text
backend/
├── main.py
├── database/
│   └── db.py
├── models/
│   ├── interview.py
│   └── user.py
├── routes/
│   ├── auth.py
│   ├── dashboard.py
│   └── interview.py
├── schemas/
│   ├── interview.py
│   └── user.py
├── services/
│   ├── ai_service.py
│   ├── auth_service.py
│   └── question_service.py
├── utils/
│   └── security.py
└── requirements.txt

frontend/
├── dashboard.html
├── index.html
├── interview.html
├── login.html
├── register.html
├── script.js
└── styles.css
```

## Setup Instructions

1. Create and activate a virtual environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install backend dependencies.

```bash
pip install -r backend/requirements.txt
```

3. Create your environment file.

```bash
cp .env.example .env
```

4. Optional: add an OpenAI API key in `.env` to enable live AI scoring. If the key is blank, the app uses the built-in mock evaluator automatically.

5. Start the application from the project root.

```bash
uvicorn backend.main:app --reload
```

6. Open the app in your browser:

```text
http://127.0.0.1:8000
```

## Environment Variables

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | SQLAlchemy connection string. Defaults to SQLite. |
| `JWT_SECRET_KEY` | Secret used to sign JWT tokens. |
| `JWT_ALGORITHM` | JWT signing algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime in minutes. |
| `OPENAI_API_KEY` | OpenAI key for live evaluation. |
| `OPENAI_MODEL` | OpenAI model name for evaluation requests. |
| `CORS_ORIGINS` | Comma-separated origins or `*`. |

## PostgreSQL Support

Set `DATABASE_URL` to a PostgreSQL URL, for example:

```env
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/ai_interview_prep
```

## API Routes

### Auth

- `POST /auth/register`
- `POST /auth/login`

### Interview

- `POST /interview/start`
- `POST /interview/submit`
- `GET /interview/history`

### Dashboard

- `GET /dashboard/stats`

## Sample API Requests

### Register

```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "candidate@example.com",
    "password": "Practice123"
  }'
```

### Login

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "candidate@example.com",
    "password": "Practice123"
  }'
```

### Start Interview

Replace `YOUR_TOKEN` with the JWT returned by login or register.

```bash
curl -X POST http://127.0.0.1:8000/interview/start \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "Software Engineer",
    "difficulty": "Medium",
    "num_questions": 5
  }'
```

### Submit Interview

```bash
curl -X POST http://127.0.0.1:8000/interview/submit \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "interview_id": 1,
    "answers": [
      "I would start by instrumenting the endpoint, reviewing logs, and checking the slowest database queries.",
      "A monolith can be faster to ship at first, but microservices help teams scale ownership when boundaries are clear.",
      "I would use retries, timeouts, circuit breakers, and queues for resilience.",
      "Caching hot reads reduces repeated database load and improves latency.",
      "I would review the rollout plan, test coverage, failure modes, and backward compatibility."
    ]
  }'
```

### Interview History

```bash
curl http://127.0.0.1:8000/interview/history \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Dashboard Stats

```bash
curl http://127.0.0.1:8000/dashboard/stats \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## System Flow Explanation

1. A user registers or logs in from the frontend. The backend hashes the password with bcrypt and returns a JWT.
2. The frontend stores the token in local storage and attaches it to protected API requests.
3. When the user starts an interview, the backend validates the selected role and difficulty, randomizes questions, creates an interview record, and returns the session payload.
4. The user answers questions in the browser while a timer runs. Draft answers are preserved locally so refreshes do not lose progress.
5. On submission, the backend stores answers and evaluates them with OpenAI when `OPENAI_API_KEY` is set. If the key is missing or the API call fails, a deterministic mock evaluator scores the answers.
6. The completed interview record persists questions, answers, score data, and detailed feedback in the database.
7. The dashboard aggregates interview history to show completion rate, average score, role-based performance, and recent feedback.

## Database Schema

### Users

- `id`
- `email`
- `password_hash`
- `created_at`

### Interviews

- `id`
- `user_id`
- `role`
- `difficulty`
- `questions`
- `answers`
- `scores`
- `feedback`
- `created_at`

## Run Notes

- The FastAPI app serves both API routes and the frontend pages.
- SQLite works out of the box with no setup.
- PostgreSQL support is enabled through the same ORM models and environment-based configuration.
- If you want to harden for deployment, start by setting a strong `JWT_SECRET_KEY`, configuring allowed CORS origins, and serving behind a production ASGI server setup.
