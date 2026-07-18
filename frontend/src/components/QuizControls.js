import React from "react";

const SPORTS = ["Cricket", "Football", "Tennis", "Basketball", "Badminton", "Volleyball"];
const DIFFICULTIES = ["Easy", "Medium", "Hard"];

export default function QuizControls({
  sport,
  setSport,
  difficulty,
  setDifficulty,
  onGenerate,
  loading,
  hasQuiz,
}) {
  return (
    <div className="controls-card">
      <div className="control-row">
        <label htmlFor="sport-select">Select Sport</label>
        <select
          id="sport-select"
          value={sport}
          onChange={(e) => setSport(e.target.value)}
        >
          {SPORTS.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>

      <div className="control-row">
        <label htmlFor="difficulty-select">Difficulty</label>
        <select
          id="difficulty-select"
          value={difficulty}
          onChange={(e) => setDifficulty(e.target.value)}
        >
          {DIFFICULTIES.map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>
      </div>

      <button className="primary-btn" onClick={onGenerate} disabled={loading}>
        {loading ? "Generating..." : hasQuiz ? "Regenerate Quiz" : "Generate Quiz"}
      </button>
    </div>
  );
}
