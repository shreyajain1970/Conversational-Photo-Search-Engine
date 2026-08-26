/**
 * ResultsList.jsx
 *
 * Pure display component: renders a list of search results.
 * Receives the results array as a prop — does not fetch, does not know
 * about the API, does not manage state.
 */
export default function ResultsList({ results }) {
  if (!results || results.length === 0) {
    return null;
  }

  return (
    <ul className="results-list">
      {results.map((r) => (
        <li key={r.filename} className="result-item">
          <div className="result-filename">{r.filename}</div>
          <div className="result-caption">{r.caption}</div>
        </li>
      ))}
    </ul>
  );
}