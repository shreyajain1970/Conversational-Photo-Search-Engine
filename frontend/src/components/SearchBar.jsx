/**
 * SearchBar.jsx
 *
 * Pure display component: a text input + submit button.
 * Holds no state of its own beyond the current input text — the actual
 * search query submission and API calls are handled by whoever uses this
 * component (App.jsx), not here.
 */
import { useState } from "react";

export default function SearchBar({ onSearch, disabled }) {
  const [inputValue, setInputValue] = useState("");

  function handleSubmit(e) {
    e.preventDefault();
    const trimmed = inputValue.trim();
    if (!trimmed) return;
    onSearch(trimmed);
  }

  return (
    <form onSubmit={handleSubmit} className="search-bar">
      <input
        type="text"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        placeholder="Describe the photo you're looking for..."
        disabled={disabled}
      />
      <button type="submit" disabled={disabled}>
        Search
      </button>
    </form>
  );
}