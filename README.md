# Adaptive AI Tutor

A full-stack Python tutoring app built with FastAPI, SQLite, and a responsive browser interface. It supports student, teacher, and parent accounts, course and lesson workflows, adaptive multiple-choice quizzes, a configurable AI tutor, saved answers, and a searchable open-resource hub.

## Run on Windows

Use Python 3.10 or later. In PowerShell, open this folder and run:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8765
```

Open http://127.0.0.1:8765. Interactive API docs are at http://127.0.0.1:8765/docs. SQLite and sample courses are initialized automatically. Set `TUTOR_DB` to move the database outside the source folder. The app migrates databases made by the earlier starter build and upgrades a legacy password hash when that account next logs in.

## AI provider setup

The tutor does not generate placeholder answers. Without a configured provider, the page reports that AI setup is required and tutoring requests return HTTP 503. Configure an OpenAI-compatible provider on the server to enable generated answers. Set these environment variables in PowerShell before launching the server:

```powershell
$env:AI_API_KEY="your-provider-key"
$env:AI_MODEL="gpt-4o-mini"
$env:AI_BASE_URL="https://api.openai.com/v1/chat/completions"
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8765
```

An OpenAI-compatible local model service can use the same settings with its own base URL and model name. For example, an Ollama server reachable from Windows can use `http://localhost:11434/v1/chat/completions` and `AI_API_KEY=ollama`. Never place provider keys in the browser or commit them. The `/healthz` endpoint reports whether a key is configured without returning its value. For a hosted service, add the key through the host's secret or environment-variable settings.

## Question files and OCR

Text-based PDFs are extracted with PyMuPDF. Image questions and scanned PDFs use Tesseract OCR through `pytesseract`. Install the Tesseract OCR application separately, make sure its executable is on `PATH`, or set `TESSERACT_CMD` to its full path. Uploads are limited to 10 MB and 20 PDF pages, processed in memory, and not stored. If OCR is unavailable, the app explains what is missing and still accepts pasted questions.

## Roles and flows

- **Student:** browse courses, read/complete lessons, see a 30-minute daily goal, take quizzes selected by recent topic mastery, ask the tutor, extract question text from files, save solutions, share a parent link code, and join teacher classes.
- **Teacher:** create courses, add lessons and question-bank quizzes, share a class code, view enrolled students, and see results only for their own courses.
- **Parent:** link a student with the student's code and view that linked student's progress and quiz history. Other student records are blocked.
- **Learning hub:** search and filter links to the original sources; licence details are shown cautiously and point learners to each source's terms.

Adaptive quiz bands use the student's last five scores per topic: under 50% selects beginner questions, 50–75% selects intermediate, and above 75% selects advanced. Reassessment updates subsequent recommendations.

## Docker deployment

Build and run with Docker Compose. The named volume keeps SQLite data across container rebuilds:

```powershell
Copy-Item .env.example .env
# Edit .env and set AI_API_KEY to enable generated tutoring.
docker compose up --build
```

Open http://localhost:8765. For a public HTTPS deployment, set `COOKIE_SECURE=1`, keep the database volume persistent, use a managed secret for the AI key, and put the app behind a TLS-terminating reverse proxy. Do not use SQLite on ephemeral storage. A PostgreSQL adapter and migration are needed before scaling to multiple app instances.

## Security notes

- Passwords use PBKDF2-HMAC-SHA256 with an individual random salt and 310,000 iterations. Old starter hashes are upgraded on successful login.
- Session IDs are random, stored as hashes, expire after seven days, and are delivered in HttpOnly, SameSite=Strict cookies. Set `COOKIE_SECURE=1` over HTTPS.
- API keys remain server-side. Student tutor history and saved solutions are scoped to the owning account.
- Parent and teacher data access is constrained to explicit links/enrollments.
- The project is suitable for a college demonstration. Before handling real minors' or student records, add operational controls such as backups, audit retention, rate limiting, account recovery, consent/retention policy, and a security review.

## GitHub

The source repository should include `main.py`, `index.html`, `requirements.txt`, `README.md`, `.gitignore`, `Dockerfile`, `docker-compose.yml`, and `.env.example`. The SQLite database, OCR samples, `.env`, and virtual environment are excluded. To push this checkout after creating a GitHub repository:

```powershell
git remote add origin https://github.com/YOUR_ACCOUNT/adaptive-ai-tutor.git
git branch -M main
git push -u origin main
```

