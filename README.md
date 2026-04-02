# 🐳 Docker Playground — Command Validator

A full-stack AI-powered web application that validates Docker commands, explains every flag in plain English, detects typos, and provides pro tips — all running locally with no external APIs.

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Running the App](#running-the-app)
- [Running with Docker](#running-with-docker)
- [How the AI Works](#how-the-ai-works)
- [Features](#features)
- [API Reference](#api-reference)
- [Storage Options](#storage-options)
- [Environment Variables](#environment-variables)
- [Common Errors & Fixes](#common-errors--fixes)
- [File Reference](#file-reference)

---

## Overview

Docker Playground lets you paste any Docker command and instantly get:

- A full breakdown of every flag with descriptions
- Typo detection with suggestions
- Confidence scoring
- Pro tips per subcommand
- Session history in a sidebar

Everything runs locally. The AI engine is a Python Flask service using NLTK, NumPy, and a hand-curated knowledge base of 150+ flags and 50+ subcommands.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend Framework | Next.js 14 (App Router) |
| Language | TypeScript |
| Animations | GSAP |
| AI Engine | Python (Flask + NLTK + NumPy + scikit-learn) |
| Fonts | JetBrains Mono, Space Grotesk |
| Storage | In-memory (default) / MongoDB / Firebase |

---

## Project Structure

```
playsite/
├── Dockerfile
├── requirements.txt              # Python dependencies
├── package.json                  # Node dependencies
├── .env.example                  # Environment variable template
├── next.config.js
├── tsconfig.json
│
└── src/
    ├── app/
    │   ├── layout.tsx            # Root HTML layout + fonts
    │   ├── page.tsx              # Main page
    │   └── api/
    │       ├── validate/
    │       │   └── route.ts      # POST /api/validate
    │       └── history/
    │           └── route.ts      # GET / DELETE /api/history
    │
    ├── components/
    │   ├── Terminal.tsx          # Terminal UI, input, chips, live description
    │   ├── ResultCard.tsx        # AI result card with flag breakdown
    │   └── HistoryPanel.tsx      # Sidebar session history
    │
    ├── hooks/
    │   └── useDockerPlayground.ts  # Core state management & API calls
    │
    ├── lib/
    │   ├── ai/
    │   │   ├── dockerValidator.py  # AI logic — flags, typos, scoring
    │   │   └── index.py            # Flask HTTP server on :5001
    │   │
    │   └── db/
    │       ├── storage.ts          # Storage abstraction layer
    │       ├── mongodb/
    │       │   ├── client.ts       # Mongoose connection (commented)
    │       │   ├── schema.ts       # CommandHistory schema (commented)
    │       │   └── repository.ts   # CRUD helpers (commented)
    │       └── firebase/
    │           ├── client.ts       # Firebase browser client (commented)
    │           ├── admin.ts        # Firebase Admin SDK (commented)
    │           └── repository.ts   # Firestore CRUD helpers (commented)
    │
    ├── styles/
    │   └── globals.css           # All styles
    │
    └── types/
        └── global.d.ts           # CSS module type declarations
```

---

## Prerequisites

Make sure you have these installed before starting:

| Tool | Version | Check |
|------|---------|-------|
| Node.js | 18 or higher | `node -v` |
| npm | 9 or higher | `npm -v` |
| Python | 3.9 or higher | `python --version` |
| pip | Latest | `pip --version` |

For Docker deployment:

| Tool | Version | Check |
|------|---------|-------|
| Docker | 24 or higher | `docker --version` |

---

## Installation & Setup

### Step 1 — Clone or extract the project

```bash
cd D:\Docker-Playground\playsite
```

### Step 2 — Install Node dependencies

```bash
npm install
```

### Step 3 — Install Python dependencies

```bash
pip install -r requirements.txt
```

If `pip` is not recognised, try:

```bash
pip3 install -r requirements.txt
```

Or on Windows with the Python launcher:

```bash
py -m pip install -r requirements.txt
```

### Step 4 — Configure environment

```bash
cp .env.example .env.local
```

The default `.env.local` values work out of the box for local development:

```env
STORAGE_PROVIDER=local
PYTHON_AI_URL=http://localhost:5001
```

No changes needed unless you want MongoDB or Firebase storage.

---

## Running the App

You need **two terminals running at the same time**.

### Terminal 1 — Start the Python AI service

```bash
cd D:\Docker-Playground\playsite
python src/lib/ai/index.py
```

You should see:

```
🐳 Docker AI service starting on http://localhost:5001
Press Ctrl+C to stop.
```

Keep this terminal open. If you close it, validation will stop working.

### Terminal 2 — Start Next.js

```bash
cd D:\Docker-Playground\playsite
npm run dev
```

You should see:

```
▲ Next.js 14.2.3
- Local: http://localhost:3000
✓ Ready in 2.2s
```

### Open the app

Go to **http://localhost:3000** in your browser.

---

## Running with Docker

Run everything in a single Docker container — no separate terminals needed.

### Step 1 — Make sure your Dockerfile is inside the playsite folder

```
D:\Docker-Playground\playsite\
├── Dockerfile        ← must be here
├── package.json
├── requirements.txt
└── src\
```

### Step 2 — Build the image

```bash
cd D:\Docker-Playground\playsite
docker build -t docker-playground .
```

This will take a few minutes on first build (downloading base image, installing dependencies).

### Step 3 — Run the container

```bash
docker run -p 3000:3000 docker-playground
```

### Step 4 — Open the app

Go to **http://localhost:3000**

### Useful Docker commands

```bash
# Run in background
docker run -d -p 3000:3000 --name playground docker-playground

# View logs
docker logs -f playground

# Stop the container
docker stop playground

# Remove the container
docker rm playground

# Rebuild after code changes
docker build -t docker-playground .
```

---

## How the AI Works

The Python service (`src/lib/ai/dockerValidator.py`) uses entirely local libraries — no cloud APIs.

### Libraries Used

| Library | Purpose |
|---------|---------|
| NLTK | Tokenisation and edit-distance for typo detection |
| NumPy | Cosine similarity for confidence scoring |
| difflib | Fuzzy subcommand matching |
| scikit-learn | Available for extension and vectorisation |

### Validation Pipeline

When you submit a command, the following happens:

1. The Next.js frontend sends `POST /api/validate` with the command string
2. The Next.js API route forwards it to the Python Flask service at `http://localhost:5001/validate`
3. Python tokenises the command and strips the leading `docker` keyword
4. The first token is checked against the known subcommand list
5. If unrecognised, fuzzy matching suggests the closest valid subcommand
6. Each flag token is looked up in the FLAG_DB knowledge base
7. Edit-distance is used to detect typos in flags
8. A confidence score is calculated from subcommand validity, flag recognition ratio, typo count, and presence of positional args
9. The result is returned as JSON and rendered in the ResultCard component

### Confidence Score Breakdown

| Factor | Weight |
|--------|--------|
| Known subcommand | +40% |
| Flag recognition ratio | +35% |
| Has positional args (image name etc.) | +15% |
| Each typo found | -8% |

A command is marked **valid** when the confidence is 45% or above and no typos are found.

---

## Features

| Feature | Description |
|---------|-------------|
| Flag Breakdown | Every flag explained with description and category |
| Typo Detection | Edit-distance matching catches misspelled flags |
| Confidence Score | Shows how confident the AI is in the validation |
| Pro Tips | Subcommand-specific tips from the knowledge base |
| Live Description | Shows what the subcommand does as you type |
| Session History | Sidebar tracks all commands validated in the session |
| Arrow Key Navigation | Use Up/Down arrows to cycle through command history |
| Quick Start Chips | Pre-built example commands to get started fast |
| Collapsible Cards | Click the result card header to collapse it |
| GSAP Animations | Smooth mount, stagger, and card reveal animations |

---

## API Reference

### POST /api/validate

Validates a Docker command.

**Request:**
```json
{
  "command": "run -d -p 8080:80 --name web nginx",
  "sessionId": "7ccf7de6-2b41-4e9b-8bd6-a39223ac22fa"
}
```

**Response:**
```json
{
  "valid": true,
  "command": "run -d -p 8080:80 --name web nginx",
  "subcommand": "run",
  "confidence": 0.90,
  "flags": [
    {
      "flag": "-d",
      "description": "Run container in detached (background) mode.",
      "category": "execution"
    },
    {
      "flag": "-p",
      "value": "8080:80",
      "description": "Publish port(s): HOST_PORT:CONTAINER_PORT.",
      "category": "network"
    },
    {
      "flag": "--name",
      "value": "web",
      "description": "Assign a custom name to the container.",
      "category": "container"
    }
  ],
  "typos": [],
  "pro_tips": [
    "Use '--rm' with one-off tasks to auto-clean containers.",
    "Set '--restart=unless-stopped' for long-running services."
  ],
  "summary": "Valid 'docker run' command using: -d, -p, --name."
}
```

### GET /api/history?sessionId=uuid

Returns all commands validated in the session.

**Response:**
```json
{
  "history": [
    {
      "id": "1714123456789",
      "command": "run -d -p 8080:80 nginx",
      "valid": true,
      "timestamp": "2024-04-26T10:30:00.000Z"
    }
  ]
}
```

### DELETE /api/history?sessionId=uuid

Clears all history for the session.

**Response:**
```json
{ "ok": true }
```

---

## Storage Options

The app ships with three storage backends controlled by `STORAGE_PROVIDER` in `.env.local`.

| Value | Description | Setup needed |
|-------|-------------|-------------|
| `local` | In-memory (default) | None |
| `mongodb` | MongoDB via Mongoose | See below |
| `firebase` | Firestore via Firebase | See below |

### Switching to MongoDB

1. Set in `.env.local`:
```env
STORAGE_PROVIDER=mongodb
MONGODB_URI=mongodb://localhost:27017/docker-playground
```

2. Uncomment all code in `src/lib/db/mongodb/client.ts`
3. Uncomment all code in `src/lib/db/mongodb/schema.ts`
4. Uncomment all code in `src/lib/db/mongodb/repository.ts`
5. In `src/lib/db/storage.ts`, uncomment the MongoDB import line and the three `mongoSave`, `mongoGet`, `mongoClear` calls

### Switching to Firebase

1. Set in `.env.local`:
```env
STORAGE_PROVIDER=firebase
NEXT_PUBLIC_FIREBASE_API_KEY=your_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your_domain
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your_project
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your_bucket
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
NEXT_PUBLIC_FIREBASE_APP_ID=your_app_id
FIREBASE_ADMIN_PROJECT_ID=your_project
FIREBASE_ADMIN_CLIENT_EMAIL=your_email
FIREBASE_ADMIN_PRIVATE_KEY=your_key
```

2. Uncomment all code in `src/lib/db/firebase/client.ts`
3. Uncomment all code in `src/lib/db/firebase/admin.ts`
4. Uncomment all code in `src/lib/db/firebase/repository.ts`
5. In `src/lib/db/storage.ts`, uncomment the Firebase import line and the three `firebaseSave`, `firebaseGet`, `firebaseClear` calls

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `STORAGE_PROVIDER` | `local` | Storage backend: local, mongodb, firebase |
| `PYTHON_AI_URL` | `http://localhost:5001` | URL of the Python AI service |
| `MONGODB_URI` | — | MongoDB connection string |
| `NEXT_PUBLIC_FIREBASE_API_KEY` | — | Firebase API key |
| `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN` | — | Firebase auth domain |
| `NEXT_PUBLIC_FIREBASE_PROJECT_ID` | — | Firebase project ID |
| `NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET` | — | Firebase storage bucket |
| `NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID` | — | Firebase messaging sender ID |
| `NEXT_PUBLIC_FIREBASE_APP_ID` | — | Firebase app ID |
| `FIREBASE_ADMIN_PROJECT_ID` | — | Firebase Admin project ID |
| `FIREBASE_ADMIN_CLIENT_EMAIL` | — | Firebase Admin client email |
| `FIREBASE_ADMIN_PRIVATE_KEY` | — | Firebase Admin private key |

---

## Common Errors & Fixes

### ECONNREFUSED on /api/validate

```
TypeError: fetch failed — AggregateError ECONNREFUSED
```

**Cause:** The Python AI service is not running.

**Fix:** Open a new terminal and run:
```bash
python src/lib/ai/index.py
```

---

### React Hydration Error

```
Error: Text content does not match server-rendered HTML
```

**Cause:** Session ID was generated differently on server and client.

**Fix:** Already handled in `useDockerPlayground.ts` — sessionId is initialised with `""` and set client-side via `useEffect`.

---

### CSS Import TypeScript Warning

```
Cannot find module or type declarations for '@/styles/globals.css'
```

**Fix:** Create `src/types/global.d.ts` with:
```ts
declare module "*.css";
```

Then restart the TypeScript server in VS Code: `Ctrl+Shift+P` → TypeScript: Restart TS Server.

---

### Python not recognised on Windows

```
'python' is not recognized as an internal or external command
```

**Fix:** Try one of:
```bash
python3 src/lib/ai/index.py
py src/lib/ai/index.py
py -3 src/lib/ai/index.py
```

---

### pip install fails

```
error: externally-managed-environment
```

**Fix:**
```bash
pip install --break-system-packages -r requirements.txt
```

---

### Docker build fails — file not found

```
ERROR: failed to solve: "/requirements.txt": not found
```

**Cause:** You ran `docker build` from the wrong folder.

**Fix:**
```bash
cd D:\Docker-Playground\playsite
docker build -t docker-playground .
```

---

### Port 3000 already in use

```
Error: listen EADDRINUSE: address already in use :::3000
```

**Fix:**
```bash
# Find what's using port 3000
netstat -ano | findstr :3000

# Kill it (replace PID with the number found above)
taskkill /PID <PID> /F
```

---

### Port 5001 already in use

**Fix:**
```bash
netstat -ano | findstr :5001
taskkill /PID <PID> /F
```

Or change the port in `src/lib/ai/index.py`:
```python
port = int(os.environ.get("AI_PORT", 5002))  # change to any free port
```

And update `.env.local`:
```env
PYTHON_AI_URL=http://localhost:5002
```

---

## File Reference

| File | Purpose |
|------|---------|
| `src/app/page.tsx` | Main page — header, layout, GSAP animations |
| `src/app/layout.tsx` | Root HTML shell, font imports |
| `src/app/api/validate/route.ts` | Receives command, calls Python, saves to storage |
| `src/app/api/history/route.ts` | Returns or clears session history |
| `src/components/Terminal.tsx` | Terminal UI, textarea input, live description bar, chips |
| `src/components/ResultCard.tsx` | Collapsible result card with flags, typos, tips |
| `src/components/HistoryPanel.tsx` | Sticky sidebar with session history list |
| `src/hooks/useDockerPlayground.ts` | All state, API calls, history navigation |
| `src/lib/ai/dockerValidator.py` | Core AI — knowledge base, tokeniser, typo detector, scorer |
| `src/lib/ai/index.py` | Flask server exposing /validate and /health |
| `src/lib/db/storage.ts` | Abstraction over local/mongodb/firebase |
| `src/styles/globals.css` | All CSS — variables, layout, terminal, cards, history |
| `src/types/global.d.ts` | TypeScript declaration for CSS imports |
| `requirements.txt` | Python packages: flask, flask-cors, numpy, nltk, scikit-learn |
| `Dockerfile` | Single-stage Docker build for the full app |
| `.env.example` | Template for environment variables |
