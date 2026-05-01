# Wumpus Logic Agent — AI 2002 Assignment 6

A Python Flask web application implementing a Knowledge-Based Agent that navigates the Wumpus World using Propositional Logic and Resolution Refutation.

## Features
- **Real CNF Resolution Refutation Engine** (pure Python, no libraries)
- **TELL/ASK KB Architecture** — biconditional rules per visited cell
- **Dynamic Grid** (3×3 up to 7×7), random pits/wumpus/gold
- **Auto-Run, Step-by-Step, Pause** controls
- **Metrics Dashboard** — inference count, KB clause count, percepts
- **KB Inference Log** — every TELL/ASK operation logged
- **World Reveal** on game over

## Project Structure
```
wumpus/
├── app.py              # Flask server + REST API
├── wumpus_world.py     # WumpusWorld + Agent classes
├── logic_engine.py     # CNF Resolution Engine + KnowledgeBase
├── requirements.txt
└── templates/
    └── index.html      # Full frontend (HTML/CSS/JS)
```

## How to Run Locally

```bash
pip install -r requirements.txt
python app.py
```
Open `http://localhost:5000` in your browser.

## How to Deploy on Vercel / Render

### Render (Recommended for Flask)
1. Push to GitHub
2. Create new Web Service on Render
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `gunicorn app:app`

Add `gunicorn` to requirements.txt for production.

### Vercel (using serverless)
Add a `vercel.json`:
```json
{
  "builds": [{"src": "app.py", "use": "@vercel/python"}],
  "routes": [{"src": "/(.*)", "dest": "app.py"}]
}
```

## How It Works

### Logic Pipeline
1. Agent visits cell [r,c]
2. **TELL**: percept facts added as unit clauses to KB (CNF)
3. **TELL**: biconditional rules `B_{r}_{c} ⟺ (P_adj1 ∨ P_adj2 ∨ ...)` added
4. **ASK**: For each unvisited adjacent cell — assume hazard, run Resolution Refutation
5. If contradiction (⊥) derived → cell proved safe → agent moves there

### Resolution Refutation (Proof by Contradiction)
To prove `¬P_r_c` (no pit at [r,c]):
- Add `{P_r_c}` (negation of goal) to KB
- Resolve clauses pairwise until empty clause derived
- Empty clause = contradiction = goal proven
