# Zero-Shot Cognitive Cross-Pollination

A structure-mapping approach to serendipity in recommender systems without model training. This application uses **Conceptual Blending Theory** (Fauconnier & Turner) and Gentner's **Structure-Mapping Theory (SMT)** to auto-translate obscure, distant domains into the vocabulary of something the user already understands, challenge the user to apply the concept, and dynamically update user progress.

---

## Why This Exists

Traditional recommender algorithms trap users in echo chambers of familiar content, while completely random discovery often leads down disjointed rabbit holes that are either too obscure to understand or too trivial to care about. 

**Zero-Shot Cognitive Cross-Pollination** was built to provide **serendipity with purpose**—a structured springboard to discover unfamiliar domains across science, technology, and humanities by anchoring them to mental models you already possess.

---

## Architecture Overview

```
User Known Topic/Hobby (e.g., "Baking Bread")
                │
                ▼
┌──────────────────────────────────────────────────────────┐
│  Layer 1: Semantic Disrupter (Near / Mid / Far Bands)    │
│  Computes vector distances using sentence-transformers   │
└───────────────────────┬──────────────────────────────────┘
                        │ Target Concept (e.g., "Tectonic Subduction")
                        ▼
┌──────────────────────────────────────────────────────────┐
│  Layer 2: Zero-Key Information Retrieval Layer           │
│  Live ingestion from Wikipedia, arXiv & DuckDuckGo       │
└───────────────────────┬──────────────────────────────────┘
                        │ Raw Domain Knowledge
                        ▼
┌──────────────────────────────────────────────────────────┐
│  Layer 3: Structure-Mapping & Blending Engine (SMT)      │
│  • Agent A: Relational Schema Distiller (Entities/Rules) │
│  • Agent B: Analogical Translator (Vocabulary Mapping)   │
└───────────────────────┬──────────────────────────────────┘
                        │ Blended Narrative
                        ▼
┌──────────────────────────────────────────────────────────┐
│  Layer 4: Serendipity Evaluator                          │
│  Mathematical scoring: Unexpectedness × Utility          │
└───────────────────────┬──────────────────────────────────┘
                        │ Verified Analogy
                        ▼
┌──────────────────────────────────────────────────────────┐
│  Layer 5: Micro-Challenge Generator                      │
│  Reverse-prompt scenario in user's hobby context         │
└───────────────────────┬──────────────────────────────────┘
                        │ User Free-Text Answer
                        ▼
┌──────────────────────────────────────────────────────────┐
│  Layer 6: Rubric-Based Scoring & Active Learning Loop    │
│  Multi-criteria grading, XP, Streaks & EMA Mastery       │
└──────────────────────────────────────────────────────────┘
```

---

## Key Features

### 1. Unknown-from-Known Topic Discovery
- Analyzes user interests and projects them into semantic embedding space using `all-MiniLM-L6-v2`.
- Generates a 3-tier disruption spectrum:
  - **Near Band:** Intuitive adjacent mechanics and concepts.
  - **Mid Band:** Related applied fields and interdisciplinary crossovers.
  - **Far Band:** Highly distant target concepts with high analogical potential.

### 2. Zero-Key Multi-Source Information Retrieval Layer
- Automatically retrieves factual and academic context for obscure targets on the fly.
- Queries **Wikipedia**, **arXiv**, and **DuckDuckGo** without requiring paid external API subscriptions.
- Employs SQLite caching to ensure fast, idempotent subsequent lookups.

### 3. Dual-Agent Structure-Mapping & Blending Engine
- **Agent A (Relational Systems Abstractor):** Deconstructs complex target topics into system rules, entities, and causal relationships.
- **Agent B (Analogical Translator):** Projects target relations onto the learner’s known hobby, generating:
  - An intuitive **blended narrative**.
  - A 1-to-1 **vocabulary translation table** (e.g., *Subducting Plate $\rightarrow$ Dense Dough*, *Magma Chamber $\rightarrow$ Oven Heat Distribution*).

### 4. Mathematical Serendipity Evaluator
- Computes a quantitative serendipity score:
  $$\text{Serendipity} = \text{Unexpectedness} \times \text{Utility}$$
- Assesses structural validity, semantic distance, and explanatory quality before surfacing analogies.
- Automatically retries candidate selection if structural validity falls below thresholds.

### 5. Reverse-Prompt Micro-Challenge Generator
- Synthesizes realistic, interactive problem scenarios within the user's hobby realm.
- Prompts the learner to solve the challenge by applying the core structural rule borrowed from the target scientific or technical concept.

### 6. Rubric-Based Scoring & Active Learning Loop
- Evaluates free-text submissions against a strict 3-dimensional rubric ($0$ to $3$ points each):
  1. **Rule Application:** Did the user accurately implement the required relational mechanism?
  2. **Contextual Coherence:** Is the proposed solution logical within the hobby context?
  3. **Analogical Understanding:** Did the user grasp the underlying "why" of the mapping?
- Updates user mastery score dynamically using **Exponential Moving Average (EMA)**, tracks streaks, and awards XP.

### 7. Human-in-the-Loop Evaluation Dashboard (`/eval-ui`)
- Built-in web dashboard at `http://localhost:8000/eval-ui`.
- Allows researchers and educators to inspect generated analogies, review raw schemas, and submit manual benchmark ratings (soundness, utility, novelty, overall quality).

### 8. Dynamic Model Discovery & Fallback Resiliency
- Seamlessly queries the Groq API for active chat models (such as `qwen/qwen3.8-27b`, `openai/gpt-oss-20b`, `llama-3.3-70b-versatile`).
- Bypasses decommissioned or unavailable model endpoints with immediate failover.
- Offline/mock support for keyless exploration and development.

---

## Setup Instructions

### Prerequisites
- **Python 3.10+** (or Python Launcher `py`)
- **Node.js 18+** and `npm`
- A **Groq API Key** (from [console.groq.com](https://console.groq.com))

### Backend Setup
1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Create a virtual environment and activate it:
   ```powershell
   # Windows (PowerShell)
   py -m venv venv
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure your `.env` in the project root:
   ```bash
   # Copy example if not present
   cp ../.env.example ../.env
   ```
   Ensure your `GROQ_API_KEY` is added to `.env`.
5. Run the backend server:
   ```bash
   python run.py
   ```
   *The backend will be live at `http://127.0.0.1:8000` (API Docs at `/docs`, Evaluation UI at `/eval-ui`).*

### Frontend Setup
1. Open a new terminal and navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the Next.js development server:
   ```bash
   npm run dev
   ```
   *The application will be accessible at `http://localhost:3000`.*

---

## Testing & Benchmarks

Run unit tests across all layers:
```bash
cd backend
python -m pytest
```

---

## License
MIT License
