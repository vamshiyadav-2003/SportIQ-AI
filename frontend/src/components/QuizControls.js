import React from "react";

const SPORTS = ["Cricket", "Football", "Tennis", "Basketball", "Badminton", "Volleyball"];
const DIFFICULTIES = ["Easy", "Medium", "Hard"];

export default function QuizControls({
  sport,
  setSport,
  difficulty,
  setDifficulty,
  onGenerate,
  onOpenHistory,
  loading,
  hasQuiz,
}) {
  return (
    <div className="controls-card">
      <div className="control-row">
        <label htmlFor="sport-select">⚽ Select Sport</label>
        <select
          id="sport-select"
          value={sport}
          onChange={(e) => setSport(e.target.value)}
          disabled={loading}
        >
          {SPORTS.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>

      <div className="control-row">
        <label htmlFor="difficulty-select">⚡ Difficulty</label>
        <select
          id="difficulty-select"
          value={difficulty}
          onChange={(e) => setDifficulty(e.target.value)}
          disabled={loading}
        >
          {DIFFICULTIES.map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>
      </div>

      <div className="control-actions">
        <button className="primary-btn" onClick={onGenerate} disabled={loading}>
          {loading ? (
            <span className="spinner-text">
              <span className="spinner"></span> Generating AI Quiz...
            </span>
          ) : hasQuiz ? (
            "✨ Regenerate Quiz"
          ) : (
            "🚀 Generate Quiz"
          )}
        </button>

        <button className="secondary-btn" onClick={onOpenHistory} title="View Past Quizzes">
          📜 History
        </button>
      </div>
    </div>
  );
}
