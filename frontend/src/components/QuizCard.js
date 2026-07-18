import React, { useState } from "react";

export default function QuizCard({ index, question }) {
  const [selected, setSelected] = useState(null);
  const [revealed, setRevealed] = useState(false);

  const handleSelect = (key) => {
    if (revealed) return;
    setSelected(key);
    setRevealed(true);
  };

  const getOptionClass = (key) => {
    if (!revealed) return "option";
    if (key === question.answer) return "option correct";
    if (key === selected) return "option incorrect";
    return "option";
  };

  return (
    <div className="quiz-card">
      <h3>
        Question {index + 1}
      </h3>
      <p className="question-text">{question.question}</p>

      <div className="options-grid">
        {Object.entries(question.options).map(([key, text]) => (
          <button
            key={key}
            className={getOptionClass(key)}
            onClick={() => handleSelect(key)}
          >
            <span className="option-key">{key}.</span> {text}
          </button>
        ))}
      </div>

      {revealed && (
        <div className="explanation-box">
          <strong>Correct Answer: {question.answer}</strong>
          <p>{question.explanation}</p>
        </div>
      )}
    </div>
  );
}
