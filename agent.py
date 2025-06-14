# agent.py

import os
import pickle
import re

import faiss
from sentence_transformers import SentenceTransformer
from duckduckgo_search import DDGS

# —————————————————————————————————————————
# 1) Load persisted FAISS index + entries
# —————————————————————————————————————————
INDEX_PATH = "faiss.index"
CHUNKS_PATH = "chunks.pkl"

if os.path.exists(INDEX_PATH) and os.path.exists(CHUNKS_PATH):
    index = faiss.read_index(INDEX_PATH)
    with open(CHUNKS_PATH, "rb") as f:
        entries = pickle.load(f)
else:
    raise RuntimeError("Run pipeline_stream.py first to build the FAISS index and chunks.pkl")

# —————————————————————————————————————————
# 2) Build an exact-match dictionary from your glossary
# —————————————————————————————————————————
# entries are of the form "Term[\\n]Definition"
entry_dict = {}
for e in entries:
    term_full, definition = e.split("\n", 1)
    term_full = term_full.strip()
    definition = definition.strip()

    # 1) map the full header (including parentheses)
    entry_dict[term_full.lower()] = definition

    # 2) also map the “main” term with any (…)-suffix stripped
    main = re.sub(r"\s*\(.*?\)", "", term_full).strip().lower()
    if main and main not in entry_dict:
        entry_dict[main] = definition

# —————————————————————————————————————————
# 3) Embedding model
# —————————————————————————————————————————
embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# —————————————————————————————————————————
# 4) Fallback summarizer for web results
# —————————————————————————————————————————
def simple_summarize(text: str, num_sentences: int = 3) -> str:
    # naive sentence split
    sents = re.split(r'(?<=[\.!?])\s+', text.strip())
    return " ".join(sents[:num_sentences]).strip()

# —————————————————————————————————————————
# 5) Main retrieve() function
# —————————————————————————————————————————
def retrieve(query: str) -> dict:
    query = query.strip()
    if len(query) < 3:
        return {
            "source": "None",
            "text": "Could you please clarify your question with a few more words?"
        }

    q_lower = query.lower()

    # — Exact-match lookup first —
    if q_lower in entry_dict:
        return {
            "source": "PDF",
            "term": query,
            "text": entry_dict[q_lower]
        }

    # — Semantic search fallback —
    q_vec = embedder.encode([query])
    faiss.normalize_L2(q_vec)
    D, I = index.search(q_vec, k=3)
    if D[0][0] >= 0.65:
        snippet = entries[I[0][0]]
        term, definition = snippet.split("\n", 1)
        return {
            "source": "PDF",
            "term": term.strip(),
            "text": definition.strip()
        }

    # — Last-resort: DuckDuckGo + light summarize (zero-cost) —
    with DDGS() as ddgs:
        results = ddgs.text(keywords=query, max_results=3)

    if not results:
        return {
            "source": "None",
            "text": f"Sorry, I couldn’t find information for “{query}.”"
        }

    raw = results[0].get("body", "")
    summary = simple_summarize(raw, num_sentences=3)
    link = results[0].get("href")
    return {
        "source": "Web",
        "text": summary or "No concise summary available.",
        "link": link
    }