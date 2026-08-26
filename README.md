Conversational Photo Search Engine

A full-stack image search system where users describe photos in natural language and retrieve results through a conversational interface — no manual tagging or folder browsing required.

How it works

The core idea is a two-stage retrieval pipeline:

BLIP captioning (offline, one-time indexing step) — every photo is run through BLIP (Salesforce's image-captioning model) to generate a natural-language caption, stored in captions.json.
TF-IDF pre-filtering — when a user searches, their query is compared against all captions using TF-IDF + cosine similarity (scikit-learn). This is a cheap, fast lexical match that narrows a potentially large photo library down to a small set of plausible candidates.
LLM ranking / clarification — the TF-IDF candidates are handed to Gemini (gemini-3.6-flash), which either (a) reranks them by actual semantic relevance — catching synonyms, plurals, and implied meaning that pure keyword matching misses — or (b) decides the query is too ambiguous and generates a clarifying question instead.
Why two stages instead of just the LLM?

Sending every photo caption to an LLM on every query doesn't scale — it's slow and expensive as the library grows. TF-IDF acts as a cheap recall filter first (milliseconds, no API call), and the LLM is only asked to reason carefully over a small, already-relevant shortlist. This is a standard retrieve-then-rerank pattern.

Why not just TF-IDF alone?

TF-IDF is purely lexical — it only catches literal word overlap. It doesn't know that "dogs" and "dog," or "shore" and "beach," mean roughly the same thing, and it can rank a lexically-similar-but-irrelevant caption above a genuinely relevant one. The LLM stage fixes exactly this class of error, and it's also what makes the clarification round-trip (the "conversational" part of the search) possible.

Architecture
photo-search-engine/
├── backend/                    Python / Django
│   ├── captioning.py           Stage 0: BLIP image → caption generation
│   ├── search_core.py          Stage 1: TF-IDF pre-filter (CaptionIndex class)
│   ├── ranking.py              Stage 2: Gemini reranking / clarification
│   ├── photosearch/            Django app — REST API
│   │   ├── views.py            POST /api/search/ — wires the pipeline to HTTP
│   │   └── urls.py
│   ├── config/                 Django project settings
│   └── requirements.txt
└── frontend/                   React (Vite)
    └── src/
        ├── api/
        │   └── photoSearch.js  API service layer — talks to Django, nothing else
        ├── components/
        │   ├── SearchBar.jsx           Pure display: text input + submit
        │   ├── ResultsList.jsx         Pure display: photo grid
        │   └── ClarificationPrompt.jsx Pure display: clarifying question banner
        └── App.jsx              Wiring: state, search flow, clarification round-trip

Each Python module in backend/ (captioning, search_core, ranking) is a standalone, independently testable unit with no HTTP dependency — Django only wires them together. Each React component is prop-driven and display-only — App.jsx is the only place that calls the API or holds state.

Conversational flow
User types a query (e.g. "woman standing").
If the query is unambiguous, ranked results are returned and rendered immediately.
If the query is too vague (e.g. matches nothing, or could mean several different things), the API returns a clarifying question instead of results.
The user's next input is treated as an answer to that question, combined with the original query, and re-searched — allowing multi-turn refinement rather than a single-shot query.
Setup
Backend
bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

Create a .env file in backend/ with your Gemini API key:

GEMINI_API_KEY=your_key_here

(Get a free key at aistudio.google.com/apikey.)

Add photos to backend/photos/, then generate captions:

bash
python captioning.py --image_dir ./photos --out captions.json

Run migrations and start the server:

bash
python manage.py migrate
python manage.py runserver
Frontend
bash
cd frontend
npm install
npm run dev

Open http://localhost:5173. Make sure the backend is running on http://127.0.0.1:8000 — the frontend's API service layer points there by default.

Known limitations
BLIP caption quality varies by image type. It performs well on typical photos (people, scenes, objects) but struggles with text-heavy images like certificates or documents (it doesn't do OCR), and can occasionally produce repetitive output on visually cluttered images.
Clarification threshold isn't finely tuned. The LLM doesn't always ask for clarification even when a query genuinely matches several very different candidates (e.g. "the woman" matching four unrelated photos) — this could be improved with more explicit prompt instructions or few-shot examples.
No persistent photo/caption database yet. Captions are loaded from a flat captions.json file on server startup rather than a proper database model — fine for a small personal library, but wouldn't scale to a large or frequently-changing photo collection without moving to Django models.
Single-user, local-only. No authentication, no per-user photo libraries — designed as a personal search tool, not a multi-tenant service.
Tech stack

Django, Django REST Framework, React (Vite), BLIP (HuggingFace Transformers), scikit-learn (TF-IDF), Google Gemini API (gemini-3.6-flash)

Project content
resume
Created by you
Add PDFs, documents, or other text to reference in this project.