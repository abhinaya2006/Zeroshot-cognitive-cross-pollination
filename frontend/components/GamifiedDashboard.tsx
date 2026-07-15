"use client";

import React, { useState, useEffect } from "react";
import { 
  Sparkles, 
  Flame, 
  Award, 
  HelpCircle, 
  ArrowRight, 
  BookOpen, 
  Share2, 
  TrendingUp, 
  Compass, 
  Shuffle, 
  CheckCircle2, 
  XCircle, 
  RotateCcw,
  Zap
} from "lucide-react";

export default function GamifiedDashboard() {
  const [userId, setUserId] = useState("learner_42");
  const [knownTopic, setKnownTopic] = useState("Baking bread");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  
  // Pipeline result
  const [apiResult, setApiResult] = useState<any>(null);
  
  // Active challenge state
  const [userAnswer, setUserAnswer] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [challengeResult, setChallengeResult] = useState<any>(null);
  const [showHint, setShowHint] = useState(false);
  const [copiedLink, setCopiedLink] = useState(false);

  // User stats
  const [userStats, setUserStats] = useState({
    mastery: 1.0,
    streak: 0,
    xp: 0
  });

  // Load profile stats on mount
  useEffect(() => {
    fetchStats();
  }, [userId]);

  const fetchStats = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/user/${userId}`);
      if (res.ok) {
        const data = await res.json();
        setUserStats({
          mastery: data.mastery,
          streak: data.streak,
          xp: data.xp
        });
      }
    } catch (e) {
      console.error("Could not fetch user stats:", e);
    }
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!knownTopic.trim()) return;
    
    setIsLoading(true);
    setError("");
    setApiResult(null);
    setChallengeResult(null);
    setUserAnswer("");
    setShowHint(false);

    try {
      const res = await fetch("http://localhost:8000/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          known_topic: knownTopic
        })
      });

      if (!res.ok) {
        const detail = await res.json();
        throw new Error(detail.detail || "API Generation failed");
      }

      const data = await res.json();
      setApiResult(data);
      if (data.user_state) {
        setUserStats(data.user_state);
      }
    } catch (err: any) {
      setError(err.message || "Failed to connect to the backend server. Make sure it is running on port 8000.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmitAnswer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!userAnswer.trim() || !apiResult) return;

    setIsSubmitting(true);
    setError("");

    try {
      const challengePayload = {
        hobby: knownTopic,
        target_topic: apiResult.target_topic,
        scenario: apiResult.challenge.scenario,
        question: apiResult.challenge.question,
        required_rule_to_apply: apiResult.challenge.required_rule_to_apply
      };

      const res = await fetch("http://localhost:8000/api/submit-challenge", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          challenge: challengePayload,
          user_answer: userAnswer
        })
      });

      if (!res.ok) {
        throw new Error("Failed to grade challenge response.");
      }

      const grading = await res.json();
      setChallengeResult(grading);
      
      // Update local stats from returned results
      setUserStats({
        mastery: grading.new_mastery,
        streak: grading.new_streak,
        xp: grading.new_xp
      });
    } catch (err: any) {
      setError(err.message || "Scoring API failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleShare = () => {
    if (!apiResult) return;
    const shareText = `Discovered how ${knownTopic} connects to ${apiResult.target_topic}! Suggested Title: ${apiResult.suggested_title}. Try Cognitive Cross-Pollination!`;
    navigator.clipboard.writeText(shareText);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center p-4 md:p-8">
      {/* Top Header & Gamified Stats */}
      <header className="w-full max-w-5xl flex flex-col md:flex-row justify-between items-center gap-4 mb-8 glass-panel rounded-2xl p-4 md:p-6 border-slate-800">
        <div className="flex items-center gap-3">
          <div className="bg-purple-600 p-2.5 rounded-xl text-white">
            <Zap className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h1 className="text-xl md:text-2xl font-black bg-gradient-to-r from-purple-400 via-pink-400 to-indigo-400 bg-clip-text text-transparent">
              COGNITIVE CROSS-POLLINATOR
            </h1>
            <p className="text-xs text-slate-400 font-medium tracking-wide">ZERO-SHOT SERENDIPITY ENGINE</p>
          </div>
        </div>

        {/* Gamified Stat Pills */}
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 px-4 py-2 rounded-xl">
            <Flame className={`w-5 h-5 ${userStats.streak > 0 ? "text-orange-500 fill-orange-500 animate-bounce" : "text-slate-500"}`} />
            <div>
              <div className="text-xs text-slate-500 font-bold">STREAK</div>
              <div className="text-sm font-black text-orange-400">{userStats.streak} Days</div>
            </div>
          </div>
          <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 px-4 py-2 rounded-xl">
            <Award className="w-5 h-5 text-purple-400" />
            <div>
              <div className="text-xs text-slate-500 font-bold">XP POINTS</div>
              <div className="text-sm font-black text-purple-400">{userStats.xp}</div>
            </div>
          </div>
          <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 px-4 py-2 rounded-xl">
            <TrendingUp className="w-5 h-5 text-green-400" />
            <div>
              <div className="text-xs text-slate-500 font-bold">MASTERY LEVEL</div>
              <div className="text-sm font-black text-green-400">{userStats.mastery.toFixed(2)}x</div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Grid Layout */}
      <div className="w-full max-w-5xl grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        {/* Left Control / Input Panel */}
        <div className="lg:col-span-4 flex flex-col gap-6">
          <div className="glass-panel rounded-2xl p-6 border-slate-800 flex flex-col gap-4">
            <h2 className="text-lg font-black text-purple-300 flex items-center gap-2">
              <Compass className="w-5 h-5" /> Your Base Hobby
            </h2>
            <p className="text-sm text-slate-400 leading-relaxed">
              Enter a hobby or topic you know extremely well. The engine will disrupt it and find distant concepts.
            </p>

            <form onSubmit={handleGenerate} className="flex flex-col gap-3">
              <div className="relative">
                <input
                  id="knownTopic"
                  name="knownTopic"
                  type="text"
                  value={knownTopic}
                  onChange={(e) => setKnownTopic(e.target.value)}
                  placeholder="e.g. Baking bread, Skating, Chess..."
                  disabled={isLoading}
                  className="w-full bg-slate-900/80 border border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-colors disabled:opacity-50"
                />
              </div>

              <div className="flex gap-2">
                <span className="text-xs text-slate-500 font-bold">Gamer Tag:</span>
                <input 
                  id="gamerTag"
                  name="gamerTag"
                  type="text" 
                  value={userId} 
                  onChange={(e) => setUserId(e.target.value)}
                  className="bg-transparent text-xs text-slate-300 outline-none border-b border-dashed border-slate-700 w-24"
                />
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-bold py-3 px-4 rounded-xl transition-all shadow-lg hover:shadow-purple-500/20 active:scale-95 flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {isLoading ? (
                  <>
                    <span className="animate-spin inline-block w-4 h-4 border-2 border-current border-t-transparent rounded-full" />
                    Calculating Distance...
                  </>
                ) : (
                  <>
                    <Shuffle className="w-4 h-4" />
                    Cross-Pollinate
                  </>
                )}
              </button>
            </form>

            {error && (
              <div className="bg-red-950/40 border border-red-800/80 text-red-300 text-xs p-3 rounded-xl leading-relaxed">
                {error}
              </div>
            )}
          </div>

          {/* Gamified Mastery/XP Card info */}
          <div className="bg-gradient-to-br from-purple-950/20 to-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col gap-3">
            <h3 className="text-sm font-bold text-slate-400 tracking-wide">HOW IT WORKS</h3>
            <div className="flex gap-3">
              <span className="text-purple-400 text-lg font-bold">1</span>
              <p className="text-xs text-slate-400">Creates a semantic distance map to locate far concepts.</p>
            </div>
            <div className="flex gap-3">
              <span className="text-purple-400 text-lg font-bold">2</span>
              <p className="text-xs text-slate-400">Extracts rules & maps structure onto your vocabulary.</p>
            </div>
            <div className="flex gap-3">
              <span className="text-purple-400 text-lg font-bold">3</span>
              <p className="text-xs text-slate-400">Presents a micro-challenge. Correctly applying the rule awards XP!</p>
            </div>
          </div>
        </div>

        {/* Right Output Panels */}
        <div className="lg:col-span-8 flex flex-col gap-6">
          {isLoading ? (
            /* Loading State Skeleton */
            <div className="glass-panel rounded-2xl p-8 border-slate-800 animate-pulse flex flex-col gap-4">
              <div className="h-6 bg-slate-800 rounded w-1/3"></div>
              <div className="h-4 bg-slate-800 rounded w-1/2"></div>
              <div className="h-20 bg-slate-800 rounded"></div>
              <div className="h-20 bg-slate-800 rounded"></div>
            </div>
          ) : apiResult ? (
            /* Result Panel */
            <div className="flex flex-col gap-8">
              
              {/* Blended Explanation Card */}
              <div className="glass-panel rounded-2xl p-6 md:p-8 border-slate-800 flex flex-col gap-6 shadow-xl relative overflow-hidden animate-glow-purple">
                {/* Decorative background glow */}
                <div className="absolute top-0 right-0 w-64 h-64 bg-purple-600/10 rounded-full filter blur-3xl pointer-events-none"></div>

                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                  <div>
                    <span className="inline-flex items-center gap-1.5 bg-purple-900/60 border border-purple-800 text-purple-300 text-xs px-2.5 py-1 rounded-full font-bold">
                      <Sparkles className="w-3.5 h-3.5" /> Discovery Found!
                    </span>
                    <h2 className="text-2xl font-black text-white mt-2">
                      {apiResult.suggested_title}
                    </h2>
                    <p className="text-xs text-slate-400 mt-1">
                      {knownTopic} × <span className="text-purple-300 font-bold">{apiResult.target_topic}</span>
                    </p>
                  </div>

                  <button
                    onClick={handleShare}
                    className="flex items-center gap-1.5 text-xs font-bold bg-slate-800 hover:bg-slate-700 text-slate-200 px-3.5 py-2 rounded-xl transition-all self-end md:self-auto"
                  >
                    <Share2 className="w-3.5 h-3.5" />
                    {copiedLink ? "Copied!" : "Share Card"}
                  </button>
                </div>

                <hr className="border-slate-800" />

                {/* Explanation Card Content */}
                <div className="prose prose-invert max-w-none">
                  <p className="text-slate-300 leading-relaxed text-sm md:text-base whitespace-pre-line">
                    {apiResult.explanation}
                  </p>
                </div>

                {/* Vocab Translator Block */}
                <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 md:p-6">
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3 flex items-center gap-2">
                    <BookOpen className="w-4 h-4 text-purple-400" /> Relational Mapping Codebook
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                    {Object.entries(apiResult.vocabulary_mapping).map(([base, mapVal]: any) => (
                      <div key={base} className="flex items-center justify-between bg-slate-950 p-2.5 rounded-lg border border-slate-800/40">
                        <span className="text-purple-300 font-bold">{base}</span>
                        <ArrowRight className="w-3 h-3 text-slate-600" />
                        <span className="text-slate-400">{mapVal}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Collapsible How We Got Here */}
                <details className="group border border-slate-800/60 rounded-xl bg-slate-900/30 overflow-hidden">
                  <summary className="cursor-pointer select-none p-4 text-xs font-black text-slate-400 group-open:text-purple-300 flex items-center justify-between hover:bg-slate-900/50 transition-colors">
                    <span>TRANSPARENCY REPORT: HOW THE SYSTEM CHOSE THIS</span>
                    <span className="transition-transform group-open:rotate-180">▼</span>
                  </summary>
                  <div className="p-4 border-t border-slate-800/60 text-xs text-slate-400 flex flex-col gap-4">
                    <div>
                      <span className="font-bold text-slate-300 block mb-1">Disruption Semantic Map bands:</span>
                      <div className="flex gap-2 flex-wrap mt-1.5">
                        <span className="bg-green-950/40 border border-green-800/50 text-green-300 px-2 py-0.5 rounded-md">
                          Near: {apiResult.reasoning_log.near_band.join(", ")}
                        </span>
                        <span className="bg-yellow-950/40 border border-yellow-800/50 text-yellow-300 px-2 py-0.5 rounded-md">
                          Mid: {apiResult.reasoning_log.mid_band.join(", ")}
                        </span>
                        <span className="bg-purple-950/40 border border-purple-800/50 text-purple-300 px-2 py-0.5 rounded-md font-bold">
                          Chosen Far: {apiResult.reasoning_log.selected_concept}
                        </span>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <span className="font-bold text-slate-300 block">Selection Branching Path:</span>
                        <p className="mt-1 leading-relaxed">{apiResult.reasoning_log.branched_from}</p>
                      </div>
                      <div>
                        <span className="font-bold text-slate-300 block">Distance Heuristic:</span>
                        <p className="mt-1 leading-relaxed">{apiResult.reasoning_log.distance_heuristic}</p>
                      </div>
                    </div>

                    <div>
                      <span className="font-bold text-slate-300 block">Analogy Potential & Relational Fit:</span>
                      <p className="mt-1 leading-relaxed">{apiResult.reasoning_log.analogy_potential}</p>
                    </div>

                    <div className="bg-slate-950 p-3 rounded-lg border border-slate-800/60 flex flex-wrap gap-4 justify-between items-center text-xs">
                      <div>
                        Measured Vector Similarity:{" "}
                        <span className="font-bold text-purple-400">
                          {apiResult.reasoning_log.measured_similarity.toFixed(4)}
                        </span>
                      </div>
                      <div>
                        Serendipity Score:{" "}
                        <span className="font-bold text-purple-400">
                          {apiResult.reasoning_log.serendipity_evaluation.serendipity_score}
                        </span>
                      </div>
                      <div>
                        Utility Rating:{" "}
                        <span className="font-bold text-purple-400">
                          {apiResult.reasoning_log.serendipity_evaluation.utility}
                        </span>
                      </div>
                    </div>
                  </div>
                </details>
              </div>

              {/* Game-like Micro-Challenge Section */}
              <div className="glass-panel rounded-2xl p-6 md:p-8 border-slate-800 flex flex-col gap-6 shadow-xl relative overflow-hidden animate-glow-green">
                <div className="absolute top-0 right-0 w-64 h-64 bg-green-600/5 rounded-full filter blur-3xl pointer-events-none"></div>

                <div>
                  <span className="inline-flex items-center gap-1.5 bg-green-950/60 border border-green-800 text-green-300 text-xs px-2.5 py-1 rounded-full font-bold">
                    <Zap className="w-3.5 h-3.5" /> MICRO-CHALLENGE ACTIVE
                  </span>
                  <h3 className="text-xl font-black text-white mt-2">
                    Put the Analogy to Work
                  </h3>
                  <p className="text-xs text-slate-400 mt-1">
                    Solve this challenge using the structural rules of the target domain to score XP!
                  </p>
                </div>

                <div className="bg-slate-900 border border-slate-800/80 rounded-xl p-4 md:p-6 text-sm text-slate-300 leading-relaxed">
                  <p className="font-bold text-white mb-2">Scenario Context:</p>
                  <p className="mb-4">{apiResult.challenge.scenario}</p>
                  
                  <p className="font-bold text-white mb-2">Challenge Question:</p>
                  <p className="text-green-300 font-bold">{apiResult.challenge.question}</p>
                </div>

                {/* Interactive Hints block */}
                <div>
                  <button
                    onClick={() => setShowHint(!showHint)}
                    className="text-xs font-bold text-purple-400 hover:text-purple-300 flex items-center gap-1 focus:outline-none"
                  >
                    <HelpCircle className="w-3.5 h-3.5" /> {showHint ? "Hide hint" : "Need a hint?"}
                  </button>
                  {showHint && (
                    <div className="mt-2 text-xs text-slate-400 bg-slate-900/50 p-3 rounded-lg border border-slate-800 border-l-4 border-l-purple-500 leading-relaxed">
                      💡 {apiResult.challenge.hint}
                    </div>
                  )}
                </div>

                {/* Form to submit response */}
                {!challengeResult ? (
                  <form onSubmit={handleSubmitAnswer} className="flex flex-col gap-4">
                    <textarea
                      id="challengeAnswer"
                      name="challengeAnswer"
                      value={userAnswer}
                      onChange={(e) => setUserAnswer(e.target.value)}
                      placeholder="Write your explanation here... Map your hobby elements to solve the limit."
                      rows={4}
                      disabled={isSubmitting}
                      className="w-full bg-slate-900 border border-slate-800 rounded-xl p-4 text-sm focus:outline-none focus:border-green-500 focus:ring-1 focus:ring-green-500 transition-colors disabled:opacity-50"
                    />

                    <button
                      type="submit"
                      disabled={isSubmitting || !userAnswer.trim()}
                      className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 text-white font-bold py-3 px-4 rounded-xl transition-all shadow-md active:scale-95 disabled:opacity-50"
                    >
                      {isSubmitting ? "Grader Reviewing..." : "Submit Answer"}
                    </button>
                  </form>
                ) : (
                  /* Duolingo style grading results */
                  <div className="border border-slate-800 rounded-xl p-6 bg-slate-900/80 flex flex-col gap-4">
                    <div className="flex justify-between items-center flex-wrap gap-3 border-b border-slate-800 pb-4">
                      <div className="flex items-center gap-2">
                        {challengeResult.success ? (
                          <CheckCircle2 className="w-7 h-7 text-green-500" />
                        ) : (
                          <HelpCircle className="w-7 h-7 text-yellow-500" />
                        )}
                        <div>
                          <div className="text-xs text-slate-400 font-bold uppercase tracking-wider">RESULT</div>
                          <div className={`text-lg font-black ${challengeResult.success ? "text-green-400" : "text-yellow-400"}`}>
                            {challengeResult.success ? "XP Earned!" : "Good Attempt!"}
                          </div>
                        </div>
                      </div>

                      <div className="text-right">
                        <span className="text-2xl font-black text-white">{challengeResult.total_score}</span>
                        <span className="text-xs text-slate-500">/100</span>
                      </div>
                    </div>

                    <div className="text-sm leading-relaxed text-slate-300">
                      <p className="font-bold text-slate-400 mb-1">Feedback:</p>
                      <p className="bg-slate-950/80 p-3 rounded-lg border border-slate-800/40">{challengeResult.feedback}</p>
                    </div>

                    {/* Rubric metrics breakdown */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                      {Object.entries(challengeResult.rubric_checks).map(([key, details]: any) => (
                        <div key={key} className="bg-slate-950 p-3 rounded-lg border border-slate-800/40 text-xs">
                          <span className="text-slate-400 capitalize block font-bold mb-1">
                            {key.replace("_", " ")}
                          </span>
                          <span className="text-sm font-black text-white">
                            {details.score} <span className="text-slate-600">/ {details.max_score}</span>
                          </span>
                          <p className="text-[10px] text-slate-500 mt-1">{details.justification}</p>
                        </div>
                      ))}
                    </div>

                    {/* Streak & XP Gained Banner */}
                    {challengeResult.success && (
                      <div className="bg-gradient-to-r from-purple-900/40 to-indigo-900/40 border border-purple-800/80 p-3.5 rounded-xl flex items-center justify-between text-xs font-bold text-purple-300">
                        <span className="flex items-center gap-1">
                          🔥 Streak Up! {challengeResult.old_streak} → {challengeResult.new_streak} Days
                        </span>
                        <span>
                          ✨ XP: +{challengeResult.new_xp - challengeResult.old_xp} Gained
                        </span>
                      </div>
                    )}

                    <button
                      onClick={() => {
                        setChallengeResult(null);
                        setUserAnswer("");
                      }}
                      className="mt-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold py-2.5 px-4 rounded-xl flex items-center justify-center gap-1.5 transition-all self-start"
                    >
                      <RotateCcw className="w-3.5 h-3.5" /> Try Another Concept
                    </button>
                  </div>
                )}
              </div>
            </div>
          ) : (
            /* Idle Screen */
            <div className="glass-panel rounded-2xl p-12 border-slate-800 text-center flex flex-col items-center gap-4">
              <div className="bg-purple-950/50 p-4 rounded-full border border-purple-800 text-purple-400 mb-2">
                <Compass className="w-8 h-8 animate-spin-slow" />
              </div>
              <h2 className="text-xl font-black text-white">Select a Hobby to Start</h2>
              <p className="text-slate-400 text-sm max-w-sm leading-relaxed">
                Enter your hobby in the sidebar, and let the system discover surprising analogical maps.
              </p>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
