# Learnwell — Adaptive AI Tutor

A full-stack college learning app: FastAPI + SQLAlchemy + SQLite for the API, and React + Vite + Tailwind CSS for the interface.

## Teacher demo

Temporary live link: <https://depth-offset-brussels-living.trycloudflare.com>

This demo URL is temporary. It works only while the host computer, Learnwell, and Ollama are running, and the URL changes when the temporary tunnel restarts. Visitors must sign in or create an account to use the app.

## Permanent cloud deployment

The repository includes `../render.yaml` and this folder's `Dockerfile` for Render. The blueprint creates a public web service and a persistent PostgreSQL database. The database is a paid Render resource (currently about $6/month); the web service uses the free plan and may take about a minute to wake after 15 minutes idle. The hostname remains stable.

Ollama runs on the desktop computer and is not available from a cloud service. To enable cloud AI, enter an OpenAI-compatible provider's base URL, API key, and model name as the `LLM_BASE_URL`, `LLM_API_KEY`, and `LLM_MODEL` secrets when configuring the Render deployment. Never put the API key in GitHub. Without those values, the app uses its clearly labeled offline guidance.

## Start locally

Requirements: Python 3.8+ and Node.js 18+ with pnpm (npm also works).

1. Copy `backend/.env.example` to `backend/.env`. Set a long random `SECRET_KEY`. For a local administrator account, set `ADMIN_EMAIL` and `ADMIN_PASSWORD` (at least 8 characters).
2. Start the API:

   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

   The API creates `backend/tutor.db`, seeds ten subjects and 360 weekly lessons on startup, and serves interactive API documentation at http://localhost:8000/docs.
3. In another terminal, start the website:

   ```powershell
   cd frontend
   pnpm install
   pnpm dev
   ```

   Open http://localhost:5173. Create a student account from the sign-in page.

## Windows desktop app

The project includes a Python desktop window powered by pywebview. It starts the FastAPI service locally, serves the built React interface inside the window, and closes the API when the window closes. The SQLite database and AI model remain on this computer.

1. Install Python 3.10+ and Node.js 18+ (with pnpm or npm). On Windows, install the Microsoft Edge WebView2 Runtime if it is not already present.
2. In `backend/.env`, set a private random `SECRET_KEY`. Keep `LLM_BASE_URL=http://localhost:11434`, `LLM_MODEL=qwen2.5:3b`, and an empty `LLM_API_KEY` for the local Ollama model. Start Ollama and make sure that model is available (`ollama pull qwen2.5:3b`).
3. Build the interface once: from `frontend`, run `pnpm install` and `pnpm build` (or `npm install` and `npm run build`).
4. Double-click `start_desktop.bat`. It creates an isolated desktop Python environment, installs the backend and pywebview dependencies, then opens the tutor window. Later launches reuse the environment and build.

The first setup needs internet access to install Python packages. The local model runs through Ollama; if Ollama is stopped, the app displays its clearly labeled offline study guidance instead. The Windows launcher source is `desktop/run_desktop.py`.

## AI tutor

The tutor accepts OpenAI-compatible chat completions endpoints and Ollama's native local API. To use Ollama, pull the local `qwen2.5:3b` model, start Ollama, and set these values in `backend/.env`:

```dotenv
LLM_BASE_URL=http://localhost:11434
LLM_API_KEY=
LLM_MODEL=qwen2.5:3b
```

For hosted providers, use their compatible `/v1` base URL, model name, and API key. The key stays on the backend. If no model is available, the tutor uses clearly labeled study guidance and never presents it as an AI response.

## Adaptive learning

- Below 50%: the quiz result recommends foundational revision.
- 50–75%: the result recommends more practice.
- Above 75%: the result recommends advanced lessons and challenges.
- Lesson completion, quiz attempts, marks, grades, feedback and progress are stored per account.

The curriculum contains nine monthly themes per subject and four weekly lessons in each month (36 lessons per subject). Each lesson includes an explanation, worked example and practice exercise. Every subject quiz contains ten questions: three subject concepts and seven questions about that subject's curriculum sequence. Quiz questions are auto-marked and results show selected answers, correct answers and explanations.

## Admin

Set `ADMIN_EMAIL` and `ADMIN_PASSWORD` before the first startup to create the initial administrator. The admin dashboard shows registered students, curriculum counts and recent quiz marks. Never use the development secret in a deployed app; set a unique secret and restrict the API to trusted origins.

Administrators can also create and edit subjects and lessons, and update or remove student records through the protected `/api/admin/*` routes (try them in `/docs` after signing in with an admin bearer token).

## Parent and teacher updates

Register separate accounts as `parent` or `teacher`. A student opens **My profile**, enters the registered account email, and sends a link request. The parent or teacher accepts it in **Notifications**. After approval, they see the student's linked progress and receive in-app notifications when the student completes lessons or submits quizzes. No marks are sent by email or to an unlinked account.

## Tests

From `backend`, install the requirements and run `python -m pytest`. Tests cover password hashing and token creation, all ten subjects, 360 lessons, ten-question-per-subject banks, lesson completions, saved quiz attempts, adaptive grading, notification routing, and truthful offline tutor guidance. A live API smoke check also verified parent linking and lesson/quiz notifications.

## Project layout

```text
backend/app/       FastAPI routes, authentication, models, SQLite seed data
backend/tests/     API integration tests
frontend/src/      React app and responsive styles
```
