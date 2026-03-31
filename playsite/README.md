# 🐳 Docker Playground — Command Validator

An AI-powered Next.js app that validates Docker commands and explains every flag, using a **100% local Python AI** (no external APIs).

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | Next.js 14 (App Router), TypeScript |
| Animations | GSAP |
| AI Engine | Python (Flask + NLTK + NumPy + scikit-learn) |
| Storage | In-memory (local) / MongoDB / Firebase |

---

## Quick Start

### 1. Install Node dependencies

```bash
npm install
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env.local
```

`.env.local` defaults are fine for local development (in-memory storage, Python AI on port 5001).

### 4. Start the Python AI service

Open a terminal and run:

```bash
python src/lib/ai/index.py
```

You should see:
```
🐳 Docker AI service starting on http://localhost:5001
```

### 5. Start Next.js

In another terminal:

```bash
npm run dev
```

Open **http://localhost:3000**

---

## How the Local AI Works

The Python service (`src/lib/ai/dockerValidator.py`) uses:

- **NLTK** — tokenisation and edit-distance for typo detection
- **NumPy** — cosine-similarity scoring for flag confidence
- **difflib** — fuzzy subcommand matching
- **scikit-learn** (available for extension) — vectorisation scaffolding
- A hand-curated **knowledge base** of 80+ Docker flags with descriptions, categories, and pro tips

No LLMs, no cloud APIs, no rate limits.

---

## Project Structure

```
src/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   └── api/
│       ├── validate/route.ts     # POST /api/validate
│       └── history/route.ts      # GET|DELETE /api/history
├── components/
│   ├── Terminal.tsx              # Terminal UI + chips
│   ├── ResultCard.tsx            # Animated result breakdown
│   └── HistoryPanel.tsx          # Sidebar history
├── hooks/
│   └── useDockerPlayground.ts    # Core state & API calls
├── lib/
│   ├── ai/
│   │   ├── dockerValidator.py    # AI logic (flags, typos, scoring)
│   │   └── index.py              # Flask HTTP server
│   └── db/
│       ├── storage.ts            # Storage abstraction
│       ├── mongodb/              # MongoDB (commented, ready to enable)
│       └── firebase/             # Firebase (commented, ready to enable)
└── styles/
    └── globals.css
```

---

## Storage Options

Set `STORAGE_PROVIDER` in `.env.local`:

| Value | Description |
|-------|-------------|
| `local` | In-memory (default, no setup) |
| `mongodb` | MongoDB via Mongoose |
| `firebase` | Firestore via Firebase Admin SDK |

### Enable MongoDB

1. Set `STORAGE_PROVIDER=mongodb`
2. Set `MONGODB_URI=mongodb://...`
3. Uncomment code in `src/lib/db/mongodb/client.ts`
4. Uncomment code in `src/lib/db/mongodb/schema.ts`
5. Uncomment code in `src/lib/db/mongodb/repository.ts`
6. Uncomment MongoDB import lines in `src/lib/db/storage.ts`

### Enable Firebase

1. Set `STORAGE_PROVIDER=firebase`
2. Fill in all `NEXT_PUBLIC_FIREBASE_*` and `FIREBASE_ADMIN_*` vars
3. Uncomment code in `src/lib/db/firebase/client.ts`
4. Uncomment code in `src/lib/db/firebase/admin.ts`
5. Uncomment code in `src/lib/db/firebase/repository.ts`
6. Uncomment Firebase import lines in `src/lib/db/storage.ts`

---

## API Reference

### `POST /api/validate`
```json
{ "command": "run -d -p 8080:80 nginx", "sessionId": "uuid" }
```

**Response:**
```json
{
  "valid": true,
  "command": "run -d -p 8080:80 nginx",
  "subcommand": "run",
  "confidence": 0.90,
  "flags": [
    { "flag": "-d", "description": "...", "category": "execution" },
    { "flag": "-p", "value": "8080:80", "description": "...", "category": "network" }
  ],
  "typos": [],
  "pro_tips": ["..."],
  "summary": "..."
}
```

### `GET /api/history?sessionId=uuid`
Returns session command history.

### `DELETE /api/history?sessionId=uuid`
Clears session history.

---

## Features

- ✅ Real-time Docker command validation
- ✅ 80+ flags with full descriptions and categories
- ✅ Typo detection with suggestions (edit-distance + fuzzy matching)
- ✅ Confidence scoring
- ✅ Per-subcommand pro tips
- ✅ Session history with sidebar panel
- ✅ GSAP animations (mount, card reveal, stagger)
- ✅ Arrow key command history navigation
- ✅ Quick-start suggestion chips
- ✅ Collapsible result cards
- ✅ MongoDB / Firebase ready (commented, easy to enable)
