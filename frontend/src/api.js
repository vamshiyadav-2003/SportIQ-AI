import axios from "axios";

// Normalize API URL
let rawUrl = process.env.REACT_APP_API_URL || "";
if (!rawUrl && (window.location.origin.includes("localhost:3000") || window.location.origin.includes("127.0.0.1:3000"))) {
  rawUrl = "http://localhost:8000";
}
const BASE_URL = rawUrl ? rawUrl.replace(/\/+$/, "") : "";

export async function generateQuiz(sport, difficulty) {
  try {
    const response = await axios.post(
      `${BASE_URL}/generate-quiz`,
      { sport, difficulty },
      { timeout: 30000 }
    );
    return response.data;
  } catch (err) {
    if (!err.response) {
      if (!rawUrl && !window.location.origin.includes("localhost") && !window.location.origin.includes("127.0.0.1")) {
        throw new Error(
          "REACT_APP_API_URL is missing on Vercel! In Vercel Project Settings > Environment Variables, set REACT_APP_API_URL to your Render backend URL (e.g. https://your-app.onrender.com)."
        );
      }
      throw new Error(
        "Cannot reach backend server. If using Render free tier, the backend server may be waking up from sleep. Please wait 15 seconds and try again."
      );
    }
    const detail = err.response?.data?.detail || err.message || "Failed to generate quiz.";
    throw new Error(detail);
  }
}

export async function getQuizHistory(limit = 10) {
  try {
    const response = await axios.get(`${BASE_URL}/quiz-history`, {
      params: { limit },
      timeout: 15000,
    });
    return response.data;
  } catch (err) {
    console.error("Failed to fetch history:", err);
    return [];
  }
}
