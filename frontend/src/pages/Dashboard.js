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

  const handleGenerate = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await generateQuiz(sport, difficulty);
      data.generatedAt = Date.now();
      setQuiz(data);
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
