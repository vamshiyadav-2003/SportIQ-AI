import React, { useState, useEffect } from "react";
import QuizControls from "../components/QuizControls";
import QuizCard from "../components/QuizCard";
import { generateQuiz, getQuizHistory } from "../api";

export default function Dashboard() {
  const [sport, setSport] = useState("Cricket");
  const [difficulty, setDifficulty] = useState("Medium");
  const [quiz, setQuiz] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Score state
  const [score, setScore] = useState(0);
  const [userAnswers, setUserAnswers] = useState({});

  // History modal state
  const [showHistory, setShowHistory] = useState(false);
  const [historyList, setHistoryList] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Gamification states
  const [timeLeft, setTimeLeft] = useState(60);
  const [timerActive, setTimerActive] = useState(false);
  const [showConfetti, setShowConfetti] = useState(false);
  const [copied, setCopied] = useState(false);

  // Timer countdown hook
  useEffect(() => {
    let interval = null;
    if (timerActive && timeLeft > 0) {
      interval = setInterval(() => {
        setTimeLeft((prev) => prev - 1);
      }, 1000);
    } else if (timeLeft === 0 && timerActive) {
      setTimerActive(false);
      // Auto-submit unanswered questions
      const newAnswers = { ...userAnswers };
      quiz?.questions.forEach((_, idx) => {
        if (newAnswers[idx] === undefined) {
          newAnswers[idx] = false;
        }
      });
      setUserAnswers(newAnswers);
    }
    return () => clearInterval(interval);
  }, [timerActive, timeLeft, quiz, userAnswers]);

  const handleGenerate = async () => {
    setLoading(true);
    setError("");
    setScore(0);
    setUserAnswers({});
    setShowConfetti(false);

    try {
      const data = await generateQuiz(sport, difficulty);
      data.generatedAt = Date.now();
      setQuiz(data);
      setTimeLeft(60);
      setTimerActive(true);
    } catch (err) {
      const detail = err?.message || "Something went wrong while generating the quiz.";
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerSelected = (questionIdx, isCorrect) => {
    if (userAnswers[questionIdx] !== undefined) return;

    setUserAnswers((prev) => {
      const newAnswers = {
        ...prev,
        [questionIdx]: isCorrect,
      };

      // Stop timer if all questions are answered
      const totalQ = quiz?.questions?.length || 0;
      if (Object.keys(newAnswers).length === totalQ) {
        setTimerActive(false);
        const finalScore = score + (isCorrect ? 1 : 0);
        if (finalScore >= 4) {
          setShowConfetti(true);
          setTimeout(() => setShowConfetti(false), 6000);
        }
      }

      return newAnswers;
    });

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
    setShowConfetti(false);
    setTimeLeft(60);
    setTimerActive(true);
  };

  const handleShareScore = () => {
    const text = `I scored ${score}/${totalQuestions} on the ${difficulty} ${sport} quiz in SportIQ AI! 🏆 Can you beat me? Try it here: ${window.location.origin}`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const totalQuestions = quiz?.questions?.length || 0;
  const answeredCount = Object.keys(userAnswers).length;

  const renderConfetti = () => {
    if (!showConfetti) return null;
    const colors = ["#fb923c", "#facc15", "#38bdf8", "#ec4899", "#34d399"];
    return (
      <div className="confetti-container">
        {Array.from({ length: 50 }).map((_, i) => {
          const style = {
            left: `${Math.random() * 100}vw`,
            animationDelay: `${Math.random() * 2}s`,
            animationDuration: `${2 + Math.random() * 3}s`,
            backgroundColor: colors[Math.floor(Math.random() * colors.length)],
            transform: `rotate(${Math.random() * 360}deg)`,
          };
          return <div key={i} className="confetti-piece" style={style}></div>;
        })}
      </div>
    );
  };

  return (
    <div className="dashboard">
      {renderConfetti()}

      <header className="app-header">
        <div className="header-badge">
          <span>AI POWERED RAG</span>
        </div>
        <h1>SportIQ AI</h1>
        <p>Interactive Sports Quiz Engine with Real-Time Grounding</p>
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
        <div className="quiz-info-grid">
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

          <div className="timer-card">
            <div className="timer-info">
              <span className="timer-label">⏱️ Countdown Timer</span>
              <span className={`timer-value ${timeLeft <= 15 ? "timer-warning" : ""}`}>
                {timeLeft}s
              </span>
            </div>
            <div className="timer-bar-bg">
              <div
                className={`timer-bar-fill ${timeLeft <= 15 ? "timer-bar-warning" : ""}`}
                style={{ width: `${(timeLeft / 60) * 100}%` }}
              ></div>
            </div>
            <span className="timer-subtext">
              {timeLeft === 0 
                ? "⌛ Time's up! Remaining questions locked."
                : timeLeft <= 15 
                ? "🚨 Fast pace! Clock is running out!" 
                : "Complete the quiz before the timer runs out."}
            </span>
          </div>
        </div>
      )}

      {quiz && answeredCount === totalQuestions && (
        <div className="completion-card animate-fadeIn">
          <div className="badge-display">
            {score === 5 && <span className="rank-badge gold">🏅 Perfect Genius (Gold)</span>}
            {score === 4 && <span className="rank-badge silver">🥈 Sports Pro (Silver)</span>}
            {score === 3 && <span className="rank-badge bronze">🥉 Sports Fan (Bronze)</span>}
            {score < 3 && <span className="rank-badge rookie">🌱 Rookie (Practice more!)</span>}
          </div>
          <button className="share-btn" onClick={handleShareScore}>
            {copied ? "✓ Copied to Clipboard!" : "🔗 Share Your Score"}
          </button>
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

      <footer className="app-footer">
        <p>© 2026 SportIQ AI. All rights reserved.</p>
        <div className="footer-links">
          <span>Real-Life Interactive Game</span>
          <span className="footer-dot">•</span>
          <span>Fast RAG Pipeline v1.2</span>
        </div>
      </footer>
    </div>
  );
}
