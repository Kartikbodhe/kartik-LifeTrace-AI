# LifeTrace AI — Your Personal Memory & Smart Reminder Assistant ⚡

> **A self-hosted, privacy-first personal intelligence hub for tasks, financial loans, promises, college milestones, document renewals, and smart reminders.**

---

## 📖 Table of Contents
1. [Project Overview](#-project-overview)
2. [Key Modules & Features](#-key-modules--features)
3. [Technology Stack](#-technology-stack)
4. [Software Architecture & Project Structure](#-software-architecture--project-structure)
5. [Windows PowerShell Setup Guide (Beginner-Friendly)](#-windows-powershell-setup-guide)
6. [Running the Application](#-running-the-application)
7. [Running Automated Tests](#-running-automated-tests)
8. [Git & GitHub Setup Guide](#-git--github-setup-guide)
9. [Security & Privacy Principles](#-security--privacy-principles)
10. [Limitations & Production Architecture](#-limitations--production-architecture)
11. [Future Roadmap & AI Integration](#-future-roadmap--ai-integration)
12. [License](#-license)

---

## 🌟 Project Overview

**LifeTrace AI** is designed to serve as an external cognitive assistant. In daily life, individuals juggle:
- Crucial assignments, exams, and project deadlines.
- Money lent to or borrowed from classmates, colleagues, and family (₹ INR).
- Commitments and personal promises made to professors, mentors, and friends.
- Critical document numbers, renewal dates, and notes (insurance policies, leases, IDs).
- Scheduled reminders and follow-up notices.

LifeTrace AI eliminates mental clutter by organizing these commitments into a single, cohesive dashboard with proactive in-app reminders and deterministic natural language capture.

---

## 🚀 Key Modules & Features

### 1. 📊 Real-Time Productivity Dashboard
- **Live Database Statistics**: Active tasks, tasks due today, dynamically calculated overdue tasks, money lent to collect (₹), money borrowed to repay (₹), pending promises, and scheduled reminders.
- **Quick Action Bar**: One-click shortcuts to add tasks, record payments, capture memories, or schedule reminders.
- **Empty States**: Encouraging, helpful onboarding guidance for first-time users.

### 2. 🧠 Personal Memory Vault
- **Structured Fields**: Title, detailed description, category (`Personal`, `College`, `Work`, `Finance`, `Project`, `Documents`, `Other`), tags, and relevant renewal/event dates.
- **Database Search & Filter**: Instant search across titles and notes, category filtering, tag chips, and sorting by newest, oldest, or upcoming event date.

### 3. 📋 Smart Task Management
- **Dynamic Overdue Calculations**: Overdue status is computed dynamically against UTC/local time; completed tasks are never marked overdue.
- **Priority & Categorization**: `High`, `Medium`, `Low` priorities with color-coded badges and custom category tags.
- **One-Click Completion**: Instantly toggle tasks between completed and active status.

### 4. 💰 Financial Payment & Loan Tracker (₹ INR)
- **Clear Separation**: Distinguishes **Money Lent** (receivables owed to you) from **Money Borrowed** (liabilities you owe).
- **Exact Decimal Precision**: Built using Python's `Decimal` module to prevent floating-point rounding errors.
- **Partial Repayment Audit Trail**: Records partial installments in a separate `repayments` table. Automatically calculates the exact remaining balance and transitions the transaction to `Settled` once the balance reaches ₹0.00.
- **Disclaimer**: Operates purely as a private ledger; does not initiate real bank transfers.

### 5. 🤝 Promises & Follow-Up Tracker
- **Accountability Logs**: Track commitments made to specific individuals or organizations (`person_or_org`).
- **Follow-Up Alarms**: Alerts when follow-up dates arrive or become overdue.

### 6. ⏰ Proactive Reminder & Notification Engine
- **Background Scheduler**: Integrated with APScheduler running background jobs every 30 seconds.
- **In-App Notification Center**: Dedicated notification log with real-time unread badges, mark-as-read toggles, and dismiss buttons.

### 7. 📅 Unified Interactive Calendar
- **Multi-View Modes**: Seamlessly toggle between **Month Grid View** and **Chronological Agenda List View**.
- **Aggregated Timeline**: Consolidates tasks (Indigo), money lent (Emerald), money borrowed (Amber), promises (Purple), memories (Cyan), and reminders (Rose).
- **Modal Inspection**: Click any event pill to view details and jump directly into the editing record.

### 8. 📈 Visual Analytics & Insights
- **Powered by Chart.js**:
  - Task completion doughnut breakdown.
  - 7-Day task completion and creation trends.
  - Financial balance bar charts (Lent vs Borrowed vs Settled).
  - Activity distribution across categories.

### 9. ✨ AI-Ready Smart Capture
- **Deterministic Pattern Parsing**: Type natural English sentences such as:
  - *"Remind me on Friday to submit my college project report"*
  - *"Lent ₹500 to Rahul until tomorrow"*
  - *"Borrowed ₹2000 from Priya due next month"*
  - *"Promised Dr. Sharma to send thesis draft by Monday"*
- **Human-in-the-Loop Confirmation**: Displays extracted parameters (Intent, Title, Amount, Person, Date, Category) in an interactive card for review before saving to the database.

---

## 🛠 Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend** | Python 3.10+, Flask 3.x, Werkzeug (Password Hashing) |
| **Authentication** | Flask-Login (Session management, user loaders) |
| **Database & ORM** | SQLite 3, SQLAlchemy ORM (Declarative models, cascades) |
| **Security** | Flask-WTF (CSRF Protection), Strict user query scoping |
| **Scheduler** | APScheduler (Background thread executor) |
| **Frontend** | Semantic HTML5, Vanilla CSS3 (Custom Dark Navy Theme), JavaScript (ES6+), Jinja2 |
| **Visualization** | Chart.js |
| **Testing** | pytest (Automated unit and integration test suite) |

---

## 📂 Software Architecture & Project Structure

```
LifeTrace-AI/
├── app.py                      # Flask application factory and server entrypoint
├── config.py                   # Environment configuration (Dev, Test, Prod)
├── extensions.py               # Extension instances (db, login_manager, csrf)
├── models.py                   # SQLAlchemy models (User, Memory, Task, Payment, etc.)
├── seed.py                     # Demo data generator
├── requirements.txt            # Dependency manifest
├── .env.example                # Template configuration variables
├── .env                        # Local development variables (git-ignored)
├── .gitignore                  # Git ignore rules
├── instance/
│   └── lifetrace.db            # SQLite database file (git-ignored)
├── routes/
│   ├── __init__.py             # Blueprint registration router
│   ├── auth.py                 # User authentication (Login, Register, Logout, Demo)
│   ├── dashboard.py            # Overview dashboard with real metric calculations
│   ├── memories.py             # Memory vault CRUD & filtering
│   ├── tasks.py                # Smart task management CRUD & toggle
│   ├── payments.py             # Payment ledger & partial repayment logs
│   ├── promises.py             # Commitments & follow-ups
│   ├── reminders.py            # Scheduled reminders & in-app notifications
│   ├── calendar.py             # Interactive calendar view & event APIs
│   ├── analytics.py            # Productivity analytics & chart feeds
│   ├── smart_capture.py        # Natural language capture preview & confirmation
│   └── settings.py             # Preferences, JSON data backup & account control
├── services/
│   ├── __init__.py
│   ├── reminder_service.py     # APScheduler background worker
│   ├── notification_service.py # In-app notification dispatcher
│   └── smart_capture_service.py# Deterministic regex & pattern parser
├── static/
│   ├── css/
│   │   └── style.css           # Premium Dark Navy CSS Design System
│   └── js/
│       ├── app.js              # Core layout, mobile drawer & notification poller
│       ├── calendar.js         # Month & agenda interactive calendar
│       ├── analytics.js        # Chart.js visualizer configurations
│       └── smart_capture.js    # Smart capture preview & submission handler
├── templates/
│   ├── base.html               # Global responsive layout shell with sidebar
│   ├── landing.html            # Public landing page
│   ├── dashboard.html          # Main user dashboard
│   ├── auth/                   # Login & registration views
│   ├── memories/               # Memory cards, forms, and detail views
│   ├── tasks/                  # Task lists and editing forms
│   ├── payments/               # Payment ledger, detail views, and repayment modal
│   ├── promises/               # Promise lists and editing forms
│   ├── reminders/              # Reminder management & notification center
│   ├── calendar/               # Calendar template
│   ├── analytics/              # Analytics charts template
│   ├── smart_capture/          # AI-ready smart capture interface
│   ├── settings/               # Settings & data export view
│   └── errors/                 # 400, 403, 404, 500 error pages
└── tests/
    ├── conftest.py             # Isolated in-memory SQLite fixtures
    ├── test_auth.py            # Authentication & validation tests
    ├── test_tasks.py           # Task CRUD & overdue calculation tests
    ├── test_payments.py        # Partial repayment & balance math tests
    ├── test_reminders.py       # Scheduler & notification tests
    └── test_smart_capture.py   # Pattern parser & entity extraction tests
```

---

## 💻 Windows PowerShell Setup Guide

Follow these exact steps in **Windows PowerShell**:

### Step 1: Open PowerShell and Navigate to Your Work Directory
```powershell
cd "d:\User Data ( Do Not Delete )\Desktop\LifeTrace-AI"
```

### Step 2: Create a Python Virtual Environment
```powershell
python -m venv .venv
```

### Step 3: Activate the Virtual Environment
```powershell
.\.venv\Scripts\Activate.ps1
```
*(If PowerShell displays an execution policy error, run `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` and try again).*

### Step 4: Install Project Dependencies
```powershell
pip install -r requirements.txt
```

### Step 5: Configure Environment Variables
Copy the template configuration into `.env`:
```powershell
Copy-Item .env.example .env
```

### Step 6: Seed Demo Data (Optional but Recommended)
Populates realistic sample tasks, memories, loans, and promises:
```powershell
python seed.py
```

---

## 🏃 Running the Application

### Start the Flask Local Development Server:
```powershell
python app.py
```

### Open in Your Browser:
Visit:
```
http://127.0.0.1:5000/
```

- Click **⚡ Try Demo Account** to explore immediately with pre-loaded data!
- Or click **Create Free Account** to register a new private account.

---

## 🧪 Running Automated Tests

Run the complete automated test suite using `pytest`:
```powershell
pytest -v
```

All 21 test scenarios verify:
- Registration, password hashing, and login credentials.
- Cross-user data isolation (preventing User A from accessing User B's records).
- Dynamic task overdue calculations.
- Decimal arithmetic during partial loan repayments.
- Settlement status transitions when remaining balance reaches ₹0.00.
- Reminder scheduling and in-app notification dispatching.
- Deterministic regex entity extraction for tasks, loans, and promises.

---

## 🐙 Git & GitHub Setup Guide

To push this codebase to your GitHub account:

### 1. Initialize Git and Stage Files
```powershell
git init
git add .
git commit -m "feat: complete functional LifeTrace AI application"
```

### 2. Rename Default Branch to `main`
```powershell
git branch -M main
```

### 3. Link Your GitHub Repository
Create a new empty repository on [GitHub](https://github.com/new) named `LifeTrace-AI` (do **not** check initialize with README), then run:
```powershell
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/LifeTrace-AI.git
```

### 4. Push Code to GitHub
```powershell
git push -u origin main
```

---

## 🔒 Security & Privacy Principles

1. **Strict User Scoping**: Every database query filters by `user_id == current_user.id`. Direct URL manipulation (`/tasks/99`) against another user's record triggers an immediate `404 Not Found`.
2. **Password Protection**: Passwords are encrypted using Werkzeug's secure PBKDF2/scrypt hashing. Plaintext passwords are never persisted.
3. **CSRF Protection**: All state-modifying POST requests require a valid CSRF session token.
4. **Data Isolation**: SQLite databases are stored in the git-ignored `instance/` folder to prevent leaking private information in public repositories.
5. **No Blind Financial Actions**: The payment tracker operates strictly as an offline record; it never connects to bank accounts or initiates external financial requests.

---

## ⚠️ Limitations & Production Architecture

- **Scheduler in Multi-Worker Environments**: APScheduler is configured for local single-process development. In multi-worker production deployments (e.g., Gunicorn with 4 workers), use Celery with Redis or a dedicated standalone cron worker to prevent duplicate scheduled triggers.
- **Local Timezones**: Stored timestamps utilize standard UTC and can be adjusted according to the user's configured regional preference in Settings.

---

## 🔮 Future Roadmap & AI Integration

- **LLM API Provider Interface**: Plug-in hooks ready to connect OpenAI, Google Gemini, or Anthropic models for conversational natural language memory extraction.
- **Push Notification Channels**: Optional integrations for Telegram bots, WhatsApp Webhooks, and SMTP email delivery.
- **Mobile PWA**: Progressive Web App manifest for offline caching and home screen installation.

---

## 📄 License
Released under the **MIT License**. Free for personal and commercial productivity use.
