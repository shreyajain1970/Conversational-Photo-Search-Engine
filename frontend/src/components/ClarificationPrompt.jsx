/**
 * ClarificationPrompt.jsx
 *
 * Pure display component: shows the LLM's clarifying question when the
 * user's query was too ambiguous to rank confidently.
 */
export default function ClarificationPrompt({ question }) {
  if (!question) {
    return null;
  }

  return (
    <div className="clarification-prompt">
      <p>{question}</p>
    </div>
  );
}