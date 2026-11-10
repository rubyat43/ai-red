# AI Red Team–Driven Security Validation Platform

An automated security validation platform for autonomous AI agents that utilizes an AI Red Team and Blue-Green deployment strategies. The system automatically attacks candidate "Green" agents with adversarial payloads (Prompt Injection, Data Leakage, etc.), scores them using an LLM-as-a-Judge, and promotes them to production ("Blue") only if they pass strict security thresholds.

## Requirements
- **Python 3.12+**
- **Node.js 20+**
- **Docker & Docker Compose** (Optional, but recommended)

---

## 🐳 Option 1: Running with Docker (Recommended)

If you have Docker Desktop installed, you can spin up the entire stack with a single command.

1. Open a terminal in the root of the project (`AI RED`).
2. Build and start the containers:
   ```bash
   docker-compose up --build
   ```
3. Access the applications:
   - **Frontend Dashboard:** http://localhost:3000
   - **Backend API & Swagger Docs:** http://localhost:8000/docs

---

## 💻 Option 2: Running Locally (Manual Setup)

If you prefer not to use Docker, you can run the backend and frontend independently in two separate terminal windows.

### 1. Start the Backend API
Open a terminal in the root of the project and run the following commands:

```powershell
# Navigate to the backend directory
cd backend

# Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\activate  # On Windows
# source venv/bin/activate # On macOS/Linux

# Install dependencies
pip install -r requirements.txt
pip install "fastapi[all]" sqlalchemy prometheus-client pydantic httpx

# Set PYTHONPATH and start the server
$env:PYTHONPATH=(Get-Location).Path
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
*The backend API will be running at http://localhost:8000*


### 2. Start the Frontend Dashboard
Open a **new** terminal window in the root of the project and run:

```powershell
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Start the Next.js development server
npm run dev
```
*The frontend dashboard will be running at http://localhost:3000*

---

## Project Structure
- `/backend`: FastAPI Python server containing the core logic, Red Team attack registry, LLM-as-a-judge, and Deployment Driver.
- `/frontend`: Next.js 16+ application featuring a strict monochrome, borderless design system. Built with TailwindCSS v4.
- `docker-compose.yml`: Unified container orchestration for easy deployment.
- `.github/workflows/ci.yml`: GitHub Actions pipeline for automated testing.
