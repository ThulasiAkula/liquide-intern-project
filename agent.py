import os
import pickle
import re
import faiss
from sentence_transformers import SentenceTransformer
from duckduckgo_search import DDGS

INDEX_PATH = "faiss.index"
CHUNKS_PATH = "chunks.pkl"

# Load index and glossary
if os.path.exists(INDEX_PATH) and os.path.exists(CHUNKS_PATH):
    index = faiss.read_index(INDEX_PATH)
    with open(CHUNKS_PATH, "rb") as f:
        entries = pickle.load(f)
else:
    raise RuntimeError("Run pipeline_stream.py first to build the FAISS index and chunks.pkl")

# Build glossary dictionary
entry_dict = {}
for e in entries:
    term_full, definition = e.split("\n", 1)
    term_full = term_full.strip()
    definition = definition.strip()
    entry_dict[term_full.lower()] = definition

    main = re.sub(r"\s*\(.*?\)", "", term_full).strip().lower()
    if main and main not in entry_dict:
        entry_dict[main] = definition

embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


#  Helper: Split multi-term queries
def split_query(query: str):
    query = query.lower().replace("what is", "").replace("explain", "").replace("definition of", "")
    return [q.strip().capitalize() for q in re.split(r'\s*(?:and|,|;)\s*', query) if q.strip()]


#  Helper: Summarize web result
def simple_summarize(text: str, num_sentences: int = 3):
    sents = re.split(r'(?<=[\.!?])\s+', text.strip())
    return " ".join(sents[:num_sentences])


#  Main retrieval function for single query
def retrieve(query: str) -> dict:
    original_query = query.strip()
    if len(original_query) < 3:
        return {
            "source": "None",
            "text": "Please enter a more specific question."
        }

    # Clean the query of filler phrases
    query_cleaned = original_query.lower()
    query_cleaned = re.sub(
        r"(what is|explain|tell me about|give me info about|info of|definition of|define|meaning of|describe)", 
        "", 
        query_cleaned
    ).strip()

    # Exact match
    if query_cleaned in entry_dict:
        return {
            "source": "PDF",
            "term": query_cleaned,
            "text": entry_dict[query_cleaned]
        }

    # Partial match
    for term in entry_dict.keys():
        if term in query_cleaned:
            return {
                "source": "PDF",
                "term": term,
                "text": entry_dict[term]
            }

    # Semantic search
    q_vec = embedder.encode([original_query])
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

    # Web fallback
    with DDGS() as ddgs:
        results = ddgs.text(keywords=original_query, max_results=3)

    if not results:
        return {
            "source": "None",
            "text": f"Sorry, I couldn’t find information for “{original_query}.”"
        }

    raw = results[0].get("body", "")
    summary = simple_summarize(raw)
    link = results[0].get("href")

    return {
        "source": "Web",
        "text": summary,
        "link": link
    }


#  Multi-term query handler
def retrieve_multiple(query: str):
    if " and " in query or "," in query or ";" in query:
        sub_queries = split_query(query)
        results = []
        for sub in sub_queries:
            ans = retrieve(sub)
            results.append((sub, ans))
        return results
    else:
        return [(query, retrieve(query))]
