import React, { useState } from "react";
import QuizControls from "../components/QuizControls";
import QuizCard from "../components/QuizCard";
import { generateQuiz } from "../api";

export default function Dashboard() {
  const [sport, setSport] = useState("Cricket");
  const [difficulty, setDifficulty] = useState("Medium");
  const [quiz, setQuiz] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showSources, setShowSources] = useState(false);
  const [activeTab, setActiveTab] = useState("local");

  const handleGenerate = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await generateQuiz(sport, difficulty);
      data.generatedAt = Date.now();
      setQuiz(data);
      setShowSources(true); // Open sources panel by default
      setActiveTab("local");
    } catch (err) {
      const detail = err?.response?.data?.detail || "Something went wrong while generating the quiz.";
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard">
      <header className="app-header">
        <h1>SportIQ AI</h1>
        <p>AI Sports Quiz Generator</p>
      </header>

      <QuizControls
        sport={sport}
        setSport={setSport}
        difficulty={difficulty}
        setDifficulty={setDifficulty}
        onGenerate={handleGenerate}
        loading={loading}
        hasQuiz={!!quiz}
      />

      {error && <div className="error-box">{error}</div>}

      {quiz && quiz.sources && (
        <div className="sources-container">
          <div className="sources-header" onClick={() => setShowSources(!showSources)}>
            <h3>
              <span>🔍 Grounding Sources / RAG Context</span>
              <span className="toggle-icon">{showSources ? "▲" : "▼"}</span>
            </h3>
            <p>See the historical facts and live search results the AI used to build this quiz.</p>
          </div>
          
          {showSources && (
            <div className="sources-tabs-container">
              <div className="sources-tabs">
                <button
                  className={`tab-btn ${activeTab === "local" ? "active" : ""}`}
                  onClick={() => setActiveTab("local")}
                >
                  📖 Historical Facts ({quiz.sources.local ? quiz.sources.local.length : 0})
                </button>
                <button
                  className={`tab-btn ${activeTab === "web" ? "active" : ""}`}
                  onClick={() => setActiveTab("web")}
                >
                  🌐 Live Web Snippets ({quiz.sources.web ? quiz.sources.web.length : 0})
                </button>
              </div>
              
              <div className="tab-content">
                {activeTab === "local" ? (
                  <ul className="sources-list">
                    {quiz.sources.local && quiz.sources.local.length > 0 ? (
                      quiz.sources.local.map((src, idx) => (
                        <li key={idx} className="source-item">{src}</li>
                      ))
                    ) : (
                      <li className="no-sources">No local facts retrieved for this query.</li>
                    )}
                  </ul>
                ) : (
                  <ul className="sources-list">
                    {quiz.sources.web && quiz.sources.web.length > 0 ? (
                      quiz.sources.web.map((src, idx) => (
                        <li key={idx} className="source-item">{src}</li>
                      ))
                    ) : (
                      <li className="no-sources">No web results retrieved (requires TAVILY_API_KEY).</li>
                    )}
                  </ul>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {quiz && (
        <div className="quiz-list">
          {quiz.questions.map((q, i) => (
            <QuizCard key={`${quiz.generatedAt}-${i}`} index={i} question={q} />
          ))}
        </div>
      )}
    </div>
  );
}
