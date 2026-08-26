import { useState } from "react";
import SearchBar from "./components/SearchBar";
import ResultsList from "./components/ResultsList";
import ClarificationPrompt from "./components/ClarificationPrompt";
import { searchPhotos } from "./api/photoSearch";
import "./App.css";

export default function App() {
  const [results, setResults] = useState([]);
  const [clarifyingQuestion, setClarifyingQuestion] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  // Keep track of the original query so a clarification answer can be
  // combined with it into a richer follow-up query.
  const [originalQuery, setOriginalQuery] = useState(null);

  async function handleSearch(query) {
    setLoading(true);
    setError(null);

    // If we're currently in a clarification round, combine the user's
    // answer with the original query for a more specific re-search.
    const effectiveQuery = clarifyingQuestion
      ? `${originalQuery} — ${query}`
      : query;

    try {
      const data = await searchPhotos(effectiveQuery);

      if (data.needs_clarification) {
        setClarifyingQuestion(data.clarifying_question);
        setResults([]);
        // Only set originalQuery the first time we enter a clarification
        // round — don't overwrite it if the user gets asked twice.
        if (!clarifyingQuestion) {
          setOriginalQuery(query);
        }
      } else {
        setClarifyingQuestion(null);
        setOriginalQuery(null);
        setResults(data.results);
      }
    } catch (err) {
      setError("Something went wrong. Is the backend server running?");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <h1>Conversational Photo Search</h1>

      <SearchBar onSearch={handleSearch} disabled={loading} />

      {loading && <p className="status-message">Searching...</p>}
      {error && <p className="status-message error">{error}</p>}

      <ClarificationPrompt question={clarifyingQuestion} />

      <ResultsList results={results} />
    </div>
  );
}