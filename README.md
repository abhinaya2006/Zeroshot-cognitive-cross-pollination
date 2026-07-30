# Zero-Shot Cognitive Cross-Pollination

A structure-mapping approach to serendipity in recommender systems without model training. This application uses Conceptual Blending Theory (Fauconnier & Turner) and Gentner's Structure-Mapping Theory (SMT) to auto-translate obscure, distant domains into the vocabulary of something the user already understands, challenge the user to apply the concept, and dynamically update user progress.

## Features
1. **Unknown-from-Known Topic Discovery**: Computes semantic distance map (near/mid/far) to select target disruption topics.
2. **Information Retrieval Layer**: Uses keyless APIs (Wikipedia, arXiv, DuckDuckGo) with SQLite caching.
3. **Structure-Mapping & Blending Engine**: Distills target topic into a relational schema (rules, entities, causes) and translates it to user hobby vocabulary.
4. **Serendipity Evaluator**: Evaluates analogical utility and unexpectedness ($Unexpectedness \times Utility$).
5. **Micro-Challenge Generator**: Creates game-like reverse-prompt challenges testing the target concept in the user's hobby context.
6. **Rubric-Based Scoring & Active-Learning Loop**: Grades free-text submissions using a structured rubric and updates user mastery via EMA.

---

## Setup Instructions

### Backend
1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   # On Windows (Powershell)
   & "..\.venv\Scripts\Activate.ps1"
   # On Linux/macOS
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` in the backend root and set your Groq API key:
   ```bash
   cp ../.env.example .env
   ```
5. Run the development server:
   ```bash
   python run.py
   ```

### Frontend
1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Copy `.env.example` configuration or set the API URL environment variable.
4. Run the Next.js development server:
   ```bash
   npm run dev
   ```

---

## Testing
Run backend unit tests:
```bash
cd backend
pytest
```

