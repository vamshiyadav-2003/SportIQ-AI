import axios from "axios";

// Change this if the backend is deployed somewhere other than localhost
const BASE_URL = process.env.REACT_APP_API_URL || (window.location.origin.includes("localhost:3000") ? "http://localhost:8000" : "");

export async function generateQuiz(sport, difficulty) {
  const response = await axios.post(`${BASE_URL}/generate-quiz`, {
    sport,
    difficulty,
  });
  return response.data;
}

export async function getQuizHistory(limit = 10) {
  const response = await axios.get(`${BASE_URL}/quiz-history`, {
    params: { limit },
  });
  return response.data;
}
