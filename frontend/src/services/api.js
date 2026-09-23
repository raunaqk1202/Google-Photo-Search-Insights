/**
 * API service layer — Axios wrapper for backend communication.
 *
 * Base URL is configured via VITE_API_BASE_URL environment variable.
 */

import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8080";

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000,
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error(
        `API Error: ${error.response.status} — ${error.response.data?.message || error.message}`
      );
    } else if (error.request) {
      console.error("API Error: No response received from server");
    } else {
      console.error(`API Error: ${error.message}`);
    }
    return Promise.reject(error);
  }
);

/** Health check */
export const checkHealth = () => api.get("/health");

/** Chat — send a conversational query */
export const sendChatMessage = (query, filters = null, sessionId = null) =>
  api.post("/chat", { query, filters, session_id: sessionId });

/** Citations — get full citation detail */
export const getCitation = (id) => api.get(`/citations/${id}`);

/** Analytics — opportunity matrix */
export const getOpportunities = () => api.get("/analytics/opportunities");

/** Analytics — memory cue frequencies */
export const getMemoryCues = () => api.get("/analytics/memory-cues");

/** Analytics — failure mode distribution */
export const getFailureModes = () => api.get("/analytics/failure-modes");

/** Analytics — retrieval archetypes */
export const getArchetypes = () => api.get("/analytics/archetypes");

/** Scraping — trigger a scrape job */
export const triggerScrape = (source = null) =>
  api.post("/scrape/trigger", { source });

/** Scraping — check job status */
export const getScrapeStatus = () => api.get("/scrape/status");

/** Data — browse structured reviews */
export const getReviews = (page = 1, perPage = 20) =>
  api.get("/data/reviews", { params: { page, per_page: perPage } });

export default api;
