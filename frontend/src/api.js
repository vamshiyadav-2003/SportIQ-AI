import axios from "axios";

// Helper to determine the backend API base URL
function getBaseUrl() {
  const envUrl = process.env.REACT_APP_API_URL;
  if (envUrl && envUrl.trim()) {
    return envUrl.trim().replace(/\/+$/, "");
  }

  if (typeof window !== "undefined") {
    const hostname = window.location.hostname;
    if (hostname === "localhost" || hostname === "127.0.0.1") {
      return "http://localhost:8000";
    }
  }

  return "";
}

const BASE_URL = getBaseUrl();

export async function generateQuiz(sport, difficulty) {
  try {
    const response = await axios.post(
      `${BASE_URL}/generate-quiz`,
      { sport, difficulty },
      { timeout: 35000 }
    );
    return response.data;
  } catch (err) {
    if (!err.response) {
      if (typeof window !== "undefined") {
        const hostname = window.location.hostname;
        if (hostname !== "localhost" && hostname !== "127.0.0.1") {
          throw new Error(
            "Backend server unreachable. Make sure REACT_APP_API_URL is configured in your deployment settings."
          );
        }
      }
      throw new Error(
        "Cannot connect to backend server at http://localhost:8000. Please make sure the FastAPI server is running."
      );
    }
    const detail = err.response?.data?.detail || err.message || "Failed to generate quiz.";
    throw new Error(detail);
  }
}

export async function getQuizHistory(limit = 20) {
  try {
    const response = await axios.get(`${BASE_URL}/quiz-history`, {
      params: { limit },
      timeout: 15000,
    });
    return response.data || [];
  } catch (err) {
    console.error("[api] Failed to fetch quiz history:", err);
    return [];
  }
}

export async function checkHealth() {
  try {
    const response = await axios.get(`${BASE_URL}/health`, { timeout: 5000 });
    return response.data;
  } catch (err) {
    return { status: "offline", error: err.message };
  }
}
