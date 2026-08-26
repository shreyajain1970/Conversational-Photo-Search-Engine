"""
ranking.py

Stage 2 of the two-stage retrieval pipeline: LLM-based reranking and
clarification.

Takes the TF-IDF candidates from search_core.py plus the user's raw query,
and asks Gemini to do two things at once:
  1. Rerank the candidates by actual semantic relevance (fixing TF-IDF's
     blind spots — synonyms, plurals, implied meaning)
  2. Decide if the query is too ambiguous to answer confidently, and if so,
     generate a clarifying question instead of a ranked list

Usage as a library:
    result = rank_candidates("dog on beach", tfidf_matches)
    if result.needs_clarification:
        print(result.clarifying_question)
    else:
        for m in result.ranked_matches:
            print(m.filename, m.caption)
"""

import json
import os
from dataclasses import dataclass
from typing import List, Optional

from dotenv import load_dotenv
from google import genai

from search_core import Match

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL_NAME = "gemini-3.6-flash"


@dataclass
class RankingResult:
    needs_clarification: bool
    clarifying_question: Optional[str]
    ranked_matches: List[Match]  # empty if needs_clarification is True


def build_prompt(query: str, candidates: List[Match]) -> str:
    """
    Construct the prompt sent to Gemini. We ask for strict JSON output so
    the response is machine-parseable — no free text to accidentally break
    downstream parsing.
    """
    candidate_lines = "\n".join(
        f'{i}. filename="{m.filename}" caption="{m.caption}"'
        for i, m in enumerate(candidates)
    )

    return f"""You are ranking candidate photos for a conversational photo search app.

User query: "{query}"

Candidate photos (pre-filtered by keyword overlap, may contain false positives or miss synonyms):
{candidate_lines}

Task:
1. If the query is clear enough to rank candidates by relevance, return the candidate
   indices ranked from most to least relevant to the query's actual meaning
   (not just keyword overlap — use synonyms, plurals, and implied meaning).
2. If the query is too vague or ambiguous to rank meaningfully (e.g. "that one photo",
   "the good one", or something that could mean multiple very different things),
   set needs_clarification to true and write ONE short, specific clarifying question.

Respond with ONLY valid JSON, no other text, in exactly this shape:
{{
  "needs_clarification": false,
  "clarifying_question": null,
  "ranked_indices": [2, 0, 1]
}}
"""


def rank_candidates(query: str, candidates: List[Match]) -> RankingResult:
    """
    Send the query + TF-IDF candidates to Gemini for semantic reranking
    or ambiguity detection.
    """
    if not candidates:
        # Nothing to rerank — TF-IDF found zero lexical matches at all
        return RankingResult(
            needs_clarification=True,
            clarifying_question="I couldn't find any photos matching that. Could you describe it differently?",
            ranked_matches=[],
        )

    prompt = build_prompt(query, candidates)
    response = client.models.generate_content(model=MODEL_NAME, contents=prompt)

    raw_text = response.text.strip()
    # Gemini sometimes wraps JSON in markdown code fences despite instructions — strip if present
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    parsed = json.loads(raw_text)

    if parsed["needs_clarification"]:
        return RankingResult(
            needs_clarification=True,
            clarifying_question=parsed["clarifying_question"],
            ranked_matches=[],
        )

    ranked = [candidates[i] for i in parsed["ranked_indices"]]
    return RankingResult(
        needs_clarification=False,
        clarifying_question=None,
        ranked_matches=ranked,
    )


if __name__ == "__main__":
    import json as json_module
    from search_core import CaptionIndex

    with open("captions.json") as f:
        real_captions = json_module.load(f)

    index = CaptionIndex(real_captions)

    query = "woman standing"
    tfidf_matches = index.search(query, top_k=5)

    print(f"TF-IDF candidates for {query!r}:")
    for m in tfidf_matches:
        print(f"  {m.filename} (score={m.score:.3f}) -> {m.caption}")

    result = rank_candidates(query, tfidf_matches)

    print()
    if result.needs_clarification:
        print(f"Needs clarification: {result.clarifying_question}")
    else:
        print("Reranked by Gemini:")
        for m in result.ranked_matches:
            print(f"  {m.filename} -> {m.caption}")
