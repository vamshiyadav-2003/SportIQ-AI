import React, { useState } from "react";

export default function QuizCard({ index, question, onAnswerSelected }) {
  const [selected, setSelected] = useState(null);
  const [revealed, setRevealed] = useState(false);

  const handleSelect = (key) => {
    if (revealed) return;
    setSelected(key);
    setRevealed(true);
    const isCorrect = key === question.answer;
    if (onAnswerSelected) {
      onAnswerSelected(index, isCorrect);
    }
  };

  const getOptionClass = (key) => {
    if (!revealed) return "option";
    if (key === question.answer) return "option correct";
    if (key === selected) return "option incorrect";
    return "option muted";
  };

  const isUserCorrect = selected === question.answer;

  return (
    <div className={`quiz-card ${revealed ? (isUserCorrect ? "card-correct" : "card-incorrect") : ""}`}>
      <div className="card-header">
        <span className="question-badge">Question {index + 1}</span>
        {revealed && (
          <span className={`result-badge ${isUserCorrect ? "badge-success" : "badge-error"}`}>
            {isUserCorrect ? "✓ Correct" : "✗ Incorrect"}
          </span>
        )}
      </div>

      <p className="question-text">{question.question}</p>

      <div className="options-grid">
        {Object.entries(question.options || {}).map(([key, text]) => (
          <button
            key={key}
            className={getOptionClass(key)}
            onClick={() => handleSelect(key)}
            disabled={revealed}
          >
            <span className="option-key">{key}.</span> {text}
          </button>
        ))}
      </div>

      {revealed && (
        <div className="explanation-box">
          <div className="explanation-header">
            <strong>Key Fact / Correct Answer: {question.answer}</strong>
          </div>
          <p>{question.explanation}</p>
        </div>
      )}
    </div>
  );
}
