/**
 * photoSearch.js
 *
 * API service layer for the photo search backend.
 * This module's only job is talking to Django over HTTP — no UI logic,
 * no state, no rendering. Components call these functions and get back
 * plain JS objects/promises.
 */

const API_BASE_URL = "http://127.0.0.1:8000/api";

/**
 * Search photos by natural-language query.
 *
 * @param {string} query - The user's search text
 * @returns {Promise<{needs_clarification: boolean, clarifying_question: string|null, results: Array<{filename: string, caption: string}>}>}
 */
export async function searchPhotos(query) {
  const response = await fetch(`${API_BASE_URL}/search/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query }),
  });

  if (!response.ok) {
    throw new Error(`Search request failed: ${response.status}`);
  }

  return response.json();
}