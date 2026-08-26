"""
search_core.py

Stage 1 of the two-stage retrieval pipeline: TF-IDF pre-filtering.

Given a query and the full set of BLIP-generated captions, this cheaply narrows
the candidate pool down to the top-N most textually relevant photos, before
handing off to the (slower, costlier) LLM ranking/clarification stage.

Usage as a library:
    index = CaptionIndex(captions_dict)   # {filename: caption}
    top_matches = index.search("dog on a beach", top_k=20)
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class Match:
    filename: str
    caption: str
    score: float


class CaptionIndex:
    """
    Wraps a scikit-learn TF-IDF vectorizer over a fixed set of captions.

    Rebuild (call `fit`) whenever the photo library changes. For a growing
    library, re-fitting periodically is fine — TF-IDF fit is cheap even at
    tens of thousands of documents.
    """

    def __init__(self, captions: Dict[str, str]):
        self.filenames: List[str] = list(captions.keys())
        self.captions: List[str] = list(captions.values())
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(
                1,
                2,
            ),  # unigrams + bigrams: "red car" beats matching "red" and "car" separately
        )
        self._matrix = None
        self.fit()

    def fit(self):
        """Build the TF-IDF matrix over all current captions."""
        if not self.captions:
            self._matrix = None
            return
        self._matrix = self.vectorizer.fit_transform(self.captions)

    def search(self, query: str, top_k: int = 20) -> List[Match]:
        """
        Return the top_k captions most similar to the query, ranked by
        cosine similarity of TF-IDF vectors. Zero-score matches are dropped —
        no lexical overlap at all means TF-IDF has nothing useful to say.
        """
        if self._matrix is None:
            return []

        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._matrix)[0]

        ranked: List[Tuple[int, float]] = sorted(
            enumerate(scores), key=lambda x: x[1], reverse=True
        )

        results = []
        for idx, score in ranked[:top_k]:
            if score <= 0:
                continue
            results.append(
                Match(
                    filename=self.filenames[idx],
                    caption=self.captions[idx],
                    score=float(score),
                )
            )
        return results


if __name__ == "__main__":
    # Quick smoke test using YOUR real captions.json from Layer 1
    import json

    with open("captions.json") as f:
        real_captions = json.load(f)

    index = CaptionIndex(real_captions)

    query = "woman standing"
    matches = index.search(query, top_k=5)

    print(f"Query: {query!r}")
    for m in matches:
        print(f"  {m.filename}  (score={m.score:.3f})  -> {m.caption}")
