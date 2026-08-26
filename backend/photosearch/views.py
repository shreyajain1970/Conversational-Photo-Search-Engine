import json
import os

from rest_framework.decorators import api_view
from rest_framework.response import Response

from search_core import CaptionIndex
from ranking import rank_candidates

# Load captions once when the server starts, not on every request —
# rebuilding the TF-IDF index per-request would be wasteful.
CAPTIONS_PATH = os.path.join(os.path.dirname(__file__), "..", "captions.json")

with open(CAPTIONS_PATH) as f:
    _captions = json.load(f)

_index = CaptionIndex(_captions)


@api_view(["POST"])
def search(request):
    """
    POST /api/search/
    Body: {"query": "dog on a beach"}

    Runs the full two-stage pipeline: TF-IDF pre-filter -> LLM rerank/clarify.
    Returns either a ranked list of matches, or a clarifying question.
    """
    query = request.data.get("query", "").strip()

    if not query:
        return Response({"error": "Query is required"}, status=400)

    tfidf_matches = _index.search(query, top_k=20)
    result = rank_candidates(query, tfidf_matches)

    if result.needs_clarification:
        return Response({
            "needs_clarification": True,
            "clarifying_question": result.clarifying_question,
            "results": [],
        })

    return Response({
        "needs_clarification": False,
        "clarifying_question": None,
        "results": [
            {"filename": m.filename, "caption": m.caption}
            for m in result.ranked_matches
        ],
    })