import React, { useState, useEffect } from "react";
import QuizControls from "../components/QuizControls";
import QuizCard from "../components/QuizCard";
import { generateQuiz, getQuizHistory, checkHealth } from "../api";

export default function Dashboard() {
  const [sport, setSport] = useState("Cricket");
  const [difficulty, setDifficulty] = useState("Medium");
  const [quiz, setQuiz] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showSources, setShowSources] = useState(false);
  const [activeTab, setActiveTab] = useState("local");

  // Score state
  const [score, setScore] = useState(0);
  const [userAnswers, setUserAnswers] = useState({});

  // History modal state
  const [showHistory, setShowHistory] = useState(false);
  const [historyList, setHistoryList] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // System status
  const [systemStatus, setSystemStatus] = useState(null);

  useEffect(() => {
    checkHealth().then((res) => setSystemStatus(res));
  }, []);

  const handleGenerate = async () => {
    setLoading(true);
    setError("");
    setScore(0);
    setUserAnswers({});

    try {
      const data = await generateQuiz(sport, difficulty);
      data.generatedAt = Date.now();
      setQuiz(data);
      setShowSources(true);
      setActiveTab("local");
    } catch (err) {
      const detail = err?.message || "Something went wrong while generating the quiz.";
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerSelected = (questionIdx, isCorrect) => {
    if (userAnswers[questionIdx] !== undefined) return;

    setUserAnswers((prev) => ({
      ...prev,
      [questionIdx]: isCorrect,
    }));

    if (isCorrect) {
      setScore((prev) => prev + 1);
    }
  };

  const handleFetchHistory = async () => {
    setLoadingHistory(true);
    setShowHistory(true);
    const data = await getQuizHistory(20);
    setHistoryList(data);
    setLoadingHistory(false);
  };

  const handleSelectHistoryItem = (item) => {
    setQuiz({
      sport: item.sport,
      difficulty: item.difficulty,
      questions: item.questions,
      sources: { local: ["Retrieved from history archive"], web: [] },
      generatedAt: item.id,
    });
    setSport(item.sport);
    setDifficulty(item.difficulty.charAt(0).toUpperCase() + item.difficulty.slice(1));
    setScore(0);
    setUserAnswers({});
    setShowHistory(false);
  };

  const totalQuestions = quiz?.questions?.length || 0;
  const answeredCount = Object.keys(userAnswers).length;

  return (
    <div className="dashboard">
      <header className="app-header">
        <div className="header-badge">
          <span>AI POWERED RAG</span>
        </div>
        <h1>SportIQ AI</h1>
        <p>Interactive Sports Quiz Engine with Real-Time Grounding</p>

        {systemStatus && (
          <div className="system-pill">
            <span className={`status-dot ${systemStatus.status === "ok" ? "online" : "offline"}`}></span>
            Backend: {systemStatus.status === "ok" ? "Connected" : "Offline"}
            {systemStatus.vector_store && (
              <span className="vector-count">
                | Knowledge Base: {systemStatus.vector_store.indexed_documents} chunks
              </span>
            )}
          </div>
        )}
      </header>

      <QuizControls
        sport={sport}
        setSport={setSport}
        difficulty={difficulty}
        setDifficulty={setDifficulty}
        onGenerate={handleGenerate}
        onOpenHistory={handleFetchHistory}
        loading={loading}
        hasQuiz={!!quiz}
      />

      {error && (
        <div className="error-box">
          <span className="error-icon">⚠️</span> {error}
        </div>
      )}

      {quiz && totalQuestions > 0 && (
        <div className="score-tracker-card">
          <div className="score-info">
            <span className="score-label">Current Quiz Score</span>
            <span className="score-value">
              {score} / {totalQuestions}
            </span>
          </div>
          <div className="score-bar-bg">
            <div
              className="score-bar-fill"
              style={{ width: `${(score / totalQuestions) * 100}%` }}
            ></div>
          </div>
          <span className="score-subtext">
            {answeredCount === 0
              ? "Select an answer for each question below"
              : answeredCount < totalQuestions
              ? `${totalQuestions - answeredCount} question(s) remaining`
              : `Completed! Final Accuracy: ${Math.round((score / totalQuestions) * 100)}%`}
          </span>
        </div>
      )}

      {quiz && quiz.sources && (
        <div className="sources-container">
          <div className="sources-header" onClick={() => setShowSources(!showSources)}>
            <h3>
              <span>🔍 Grounding Sources / RAG Context</span>
              <span className="toggle-icon">{showSources ? "▲" : "▼"}</span>
            </h3>
            <p>See the vector store facts and web search snippets used for this quiz.</p>
          </div>

          {showSources && (
            <div className="sources-tabs-container">
              <div className="sources-tabs">
                <button
                  className={`tab-btn ${activeTab === "local" ? "active" : ""}`}
                  onClick={() => setActiveTab("local")}
                >
                  📖 ChromaDB Vector Base ({quiz.sources.local ? quiz.sources.local.length : 0})
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
                        <li key={idx} className="source-item">
                          {src}
                        </li>
                      ))
                    ) : (
                      <li className="no-sources">No local facts retrieved for this query.</li>
                    )}
                  </ul>
                ) : (
                  <ul className="sources-list">
                    {quiz.sources.web && quiz.sources.web.length > 0 ? (
                      quiz.sources.web.map((src, idx) => (
                        <li key={idx} className="source-item">
                          {src}
                        </li>
                      ))
                    ) : (
                      <li className="no-sources">No web snippets retrieved.</li>
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
            <QuizCard
              key={`${quiz.generatedAt}-${i}`}
              index={i}
              question={q}
              onAnswerSelected={handleAnswerSelected}
            />
          ))}
        </div>
      )}

      {showHistory && (
        <div className="modal-backdrop" onClick={() => setShowHistory(false)}>
          <div className="history-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>📜 Quiz History Archive</h2>
              <button className="close-btn" onClick={() => setShowHistory(false)}>
                ✕
              </button>
            </div>

            {loadingHistory ? (
              <div className="modal-loading">Loading past quizzes...</div>
            ) : historyList.length === 0 ? (
              <div className="modal-empty">No quiz history recorded yet.</div>
            ) : (
              <div className="history-list">
                {historyList.map((item) => (
                  <div
                    key={item.id}
                    className="history-item"
                    onClick={() => handleSelectHistoryItem(item)}
                  >
                    <div className="history-item-top">
                      <span className="history-sport">{item.sport}</span>
                      <span className={`history-diff diff-${item.difficulty}`}>
                        {item.difficulty}
                      </span>
                    </div>
                    <div className="history-item-bottom">
                      <span>{item.questions.length} Questions</span>
                      <span className="history-date">
                        {new Date(item.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
