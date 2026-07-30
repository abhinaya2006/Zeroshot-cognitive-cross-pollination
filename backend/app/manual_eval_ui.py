import sqlite3
import time
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.config import settings

manual_eval_router = APIRouter()
DB_PATH = settings.database_url.replace("sqlite:///", "") if settings.database_url.startswith("sqlite:///") else settings.database_url

class ManualEvalSubmit(BaseModel):
    metric_id: int
    correctness: int
    clarity: int
    structural_consistency: int
    notes: Optional[str] = ""

@manual_eval_router.get("/api/manual-evaluation/history")
def get_evaluation_history():
    """Retrieves generated analogies and checks if they have manual grades."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        # Fetch runs, joining with manual evaluations and matching history log records
        query = """
            SELECT 
                m.id, m.hobby, m.discovered_topic, m.cosine_similarity, m.cosine_distance,
                m.serendipity_score, m.unexpectedness_score, m.analogy_utility_score,
                m.total_pipeline_time, m.timestamp,
                e.correctness, e.clarity, e.structural_consistency, e.overall_quality, e.notes,
                h.explanation, h.challenge
            FROM benchmark_metrics m
            LEFT JOIN manual_evaluations e ON m.id = e.metric_id
            LEFT JOIN history h ON h.known_topic = m.hobby AND h.target_topic = m.discovered_topic
            GROUP BY m.id
            ORDER BY m.timestamp DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        conn.close()

@manual_eval_router.post("/api/manual-evaluation/submit")
def submit_manual_evaluation(req: ManualEvalSubmit):
    """Saves or updates manual grading for a specific analogy run."""
    if not (1 <= req.correctness <= 5 and 1 <= req.clarity <= 5 and 1 <= req.structural_consistency <= 5):
        raise HTTPException(status_code=400, detail="Scores must be between 1 and 5.")

    overall_quality = round((req.correctness + req.clarity + req.structural_consistency) / 3.0, 2)
    timestamp = time.time()

    conn = sqlite3.connect(DB_PATH)
    try:
        with conn:
            conn.execute("""
                INSERT OR REPLACE INTO manual_evaluations 
                (metric_id, correctness, clarity, structural_consistency, overall_quality, notes, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (req.metric_id, req.correctness, req.clarity, req.structural_consistency, overall_quality, req.notes, timestamp))
        return {
            "status": "success",
            "metric_id": req.metric_id,
            "overall_quality": overall_quality
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        conn.close()

@manual_eval_router.get("/eval-ui", response_class=HTMLResponse)
def serve_evaluation_ui():
    """Serves the web dashboard for human-in-the-loop analogy scoring."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Analogy Benchmarking Evaluation UI</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap" rel="stylesheet">
        <style>
            body { font-family: 'Inter', sans-serif; background-color: #0b0f19; }
            .glow-border:focus { border-color: #a855f7; box-shadow: 0 0 10px rgba(168, 85, 247, 0.5); }
        </style>
    </head>
    <body class="text-slate-100 min-h-screen p-6 md:p-12">
        <div class="max-w-6xl mx-auto flex flex-col gap-8">
            <!-- Header -->
            <header class="flex justify-between items-center border-b border-slate-800 pb-6">
                <div>
                    <h1 class="text-3xl font-black bg-gradient-to-r from-purple-400 via-pink-400 to-indigo-400 bg-clip-text text-transparent">
                        ANALOGY EVALUATION PORTAL
                    </h1>
                    <p class="text-xs text-slate-400 tracking-wider uppercase mt-1">Human-in-the-Loop Quality Benchmarking</p>
                </div>
                <div class="bg-slate-900 border border-slate-800 px-4 py-2 rounded-xl text-center">
                    <span class="text-xs text-slate-500 font-bold uppercase">Evaluated Runs</span>
                    <div id="stats-evaluated" class="text-lg font-black text-purple-400">0 / 0</div>
                </div>
            </header>

            <!-- Main Workspace -->
            <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
                <!-- Left Sidebar: Attempt List -->
                <div class="lg:col-span-4 bg-slate-900/50 border border-slate-800 rounded-2xl p-4 flex flex-col gap-4 max-h-[70vh] overflow-y-auto">
                    <h2 class="text-sm font-bold text-slate-400 uppercase tracking-widest px-2">History Logs</h2>
                    <div id="runs-list" class="flex flex-col gap-2">
                        <!-- Run items will load here -->
                        <p class="text-xs text-slate-500 p-4 text-center">Loading run logs...</p>
                    </div>
                </div>

                <!-- Right Workspace: Grading Form -->
                <div class="lg:col-span-8 bg-slate-900/80 border border-slate-800 rounded-2xl p-6 md:p-8 flex flex-col gap-6" id="grading-workspace">
                    <div class="text-center py-12 text-slate-500">
                        <p class="text-lg">Select a log from the history panel to start scoring.</p>
                    </div>
                </div>
            </div>
        </div>

        <script>
            let currentRunId = null;
            let runsData = [];

            async function fetchHistory() {
                try {
                    const res = await fetch('/api/manual-evaluation/history');
                    runsData = await res.json();
                    renderRunsList();
                    updateStats();
                    if (currentRunId !== null) {
                        const updatedRun = runsData.find(r => r.id === currentRunId);
                        if (updatedRun) renderGradingWorkspace(updatedRun);
                    }
                } catch (e) {
                    console.error("Error loading evaluation history:", e);
                }
            }

            function updateStats() {
                const total = runsData.length;
                const graded = runsData.filter(r => r.overall_quality !== null).length;
                document.getElementById('stats-evaluated').innerText = `${graded} / ${total}`;
            }

            function renderRunsList() {
                const container = document.getElementById('runs-list');
                if (runsData.length === 0) {
                    container.innerHTML = '<p class="text-xs text-slate-500 text-center p-4">No benchmark runs recorded yet.</p>';
                    return;
                }

                container.innerHTML = runsData.map(run => {
                    const isGraded = run.overall_quality !== null;
                    const isSelected = run.id === currentRunId;
                    const date = new Date(run.timestamp * 1000).toLocaleDateString();
                    
                    return `
                        <div onclick="selectRun(${run.id})" class="cursor-pointer p-3.5 rounded-xl border transition-all ${
                            isSelected 
                                ? 'bg-purple-950/20 border-purple-500 text-white' 
                                : 'bg-slate-950/40 border-slate-800/60 hover:bg-slate-900 hover:border-slate-700 text-slate-300'
                        }">
                            <div class="flex justify-between items-start">
                                <span class="text-xs text-slate-400 font-bold">${date}</span>
                                <span class="px-2 py-0.5 rounded text-[10px] font-bold ${
                                    isGraded ? 'bg-green-950/60 text-green-400' : 'bg-yellow-950/60 text-yellow-400'
                                }">
                                    ${isGraded ? 'GRADED' : 'UNGRADED'}
                                </span>
                            </div>
                            <h3 class="font-bold text-sm mt-1 truncate">${run.hobby}</h3>
                            <p class="text-xs text-slate-500 truncate">🔬 ${run.discovered_topic}</p>
                            ${isGraded ? `<div class="text-xs text-purple-400 font-semibold mt-1">Manual Score: ${Number(run.overall_quality).toFixed(1)}/5.0</div>` : ''}
                        </div>
                    `;
                }).join('');
            }

            function selectRun(id) {
                currentRunId = id;
                renderRunsList();
                const run = runsData.find(r => r.id === id);
                if (run) renderGradingWorkspace(run);
            }

            function renderGradingWorkspace(run) {
                const container = document.getElementById('grading-workspace');
                const isGraded = run.overall_quality !== null;
                const correctness = run.correctness || 3;
                const clarity = run.clarity || 3;
                const consistency = run.structural_consistency || 3;
                const notes = run.notes || '';

                container.innerHTML = `
                    <div class="flex flex-col gap-6">
                        <!-- Top Metadata -->
                        <div class="flex justify-between items-start flex-wrap gap-4 border-b border-slate-800 pb-4">
                            <div>
                                <span class="text-xs text-slate-500 font-bold uppercase">Selected Log #${run.id}</span>
                                <h2 class="text-xl font-bold text-white mt-1">${run.hobby} &rarr; <span class="text-purple-400">${run.discovered_topic}</span></h2>
                                <p class="text-xs text-slate-400 mt-1">Pipeline time: ${run.total_pipeline_time != null ? Number(run.total_pipeline_time).toFixed(2) : '0.00'}s | Cosine Similarity: ${run.cosine_similarity != null ? Number(run.cosine_similarity).toFixed(4) : '0.0000'}</p>
                            </div>
                        </div>

                        <!-- Explanation & Challenge View Card -->
                        <div class="bg-slate-950/80 p-5 rounded-xl border border-slate-800 flex flex-col gap-4">
                            <div>
                                <span class="text-xs text-purple-400 font-bold uppercase text-[11px] tracking-wider">Generated Analogy Explanation</span>
                                <div class="text-xs text-slate-300 mt-2 bg-slate-900/60 p-3.5 rounded-lg border border-slate-800/40 max-h-48 overflow-y-auto whitespace-pre-line leading-relaxed">
                                    ${run.explanation || 'No explanation details logged in history for this mock run. (Live API generations populate this fully.)'}
                                </div>
                            </div>
                            <div>
                                <span class="text-xs text-pink-400 font-bold uppercase text-[11px] tracking-wider">Associated Micro-Challenge</span>
                                <div class="text-xs text-slate-300 mt-2 bg-slate-900/60 p-3.5 rounded-lg border border-slate-800/40 whitespace-pre-line leading-relaxed">
                                    ${run.challenge || 'No challenge details logged.'}
                                </div>
                            </div>
                        </div>

                        <!-- Grading Section -->
                        <form onsubmit="submitForm(event)" class="flex flex-col gap-6">
                            <input type="hidden" id="metric-id" value="${run.id}" />
                            
                            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                                <!-- Correctness -->
                                <div class="bg-slate-950 p-4 rounded-xl border border-slate-800">
                                    <label class="block text-sm font-bold text-slate-300 mb-1">Correctness</label>
                                    <span class="text-[10px] text-slate-500 block mb-3">Does the scientific concept map without errors?</span>
                                    <input type="range" id="correctness" min="1" max="5" value="${correctness}" class="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-purple-500" oninput="document.getElementById('correctness-val').innerText = this.value" />
                                    <div class="text-center font-bold text-lg text-purple-400 mt-2"><span id="correctness-val">${correctness}</span> / 5</div>
                                </div>
                                
                                <!-- Clarity -->
                                <div class="bg-slate-950 p-4 rounded-xl border border-slate-800">
                                    <label class="block text-sm font-bold text-slate-300 mb-1">Clarity</label>
                                    <span class="text-[10px] text-slate-500 block mb-3">Is the explanation easy to read and understand?</span>
                                    <input type="range" id="clarity" min="1" max="5" value="${clarity}" class="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-purple-500" oninput="document.getElementById('clarity-val').innerText = this.value" />
                                    <div class="text-center font-bold text-lg text-purple-400 mt-2"><span id="clarity-val">${clarity}</span> / 5</div>
                                </div>

                                <!-- Consistency -->
                                <div class="bg-slate-950 p-4 rounded-xl border border-slate-800">
                                    <label class="block text-sm font-bold text-slate-300 mb-1">Consistency</label>
                                    <span class="text-[10px] text-slate-500 block mb-3">Are rules and causal chains mapped 1:1?</span>
                                    <input type="range" id="consistency" min="1" max="5" value="${consistency}" class="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-purple-500" oninput="document.getElementById('consistency-val').innerText = this.value" />
                                    <div class="text-center font-bold text-lg text-purple-400 mt-2"><span id="consistency-val">${consistency}</span> / 5</div>
                                </div>
                            </div>

                            <!-- Notes -->
                            <div class="flex flex-col gap-2">
                                <label class="text-sm font-bold text-slate-300">Qualitative Evaluator Notes</label>
                                <textarea id="notes" rows="3" placeholder="Add observations on analogical strength, gaps, or logic errors..." class="bg-slate-950 border border-slate-800 rounded-xl p-3 text-sm focus:outline-none glow-border transition-all text-slate-300">${notes}</textarea>
                            </div>

                            <button type="submit" class="w-full bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-bold py-3 px-4 rounded-xl transition-all shadow-md active:scale-[0.98]">
                                ${isGraded ? 'Update Evaluation Scores' : 'Submit Evaluation Scores'}
                            </button>
                        </form>
                    </div>
                `;
            }

            async function submitForm(e) {
                e.preventDefault();
                const metricId = parseInt(document.getElementById('metric-id').value);
                const correctness = parseInt(document.getElementById('correctness').value);
                const clarity = parseInt(document.getElementById('clarity').value);
                const consistency = parseInt(document.getElementById('consistency').value);
                const notes = document.getElementById('notes').value;

                try {
                    const res = await fetch('/api/manual-evaluation/submit', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            metric_id: metricId,
                            correctness: correctness,
                            clarity: clarity,
                            structural_consistency: consistency,
                            notes: notes
                        })
                    });

                    if (res.ok) {
                        fetchHistory();
                    } else {
                        alert("Error saving manual score.");
                    }
                } catch (err) {
                    console.error("Submit error:", err);
                }
            }

            // Initial Load
            fetchHistory();
        </script>
    </body>
    </html>
    """
    return html_content
