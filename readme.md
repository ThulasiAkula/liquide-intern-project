# Liquide Glossary Search

An offline-first, Streamlit-based glossary lookup tool for financial terms. It uses a local PDF glossary (`Data.pdf`), semantic search (via FAISS and SentenceTransformers), and a DuckDuckGo fallback for undefined terms. Definitions are displayed neatly, with bullet-point formatting and footer page markers removed.

---

## Features

* **Exact Glossary Lookup**: Directly retrieves term definitions from the PDF glossary.
* **Semantic Search**: Falls back to approximate matching when exact terms aren’t found (using the `all-MiniLM-L6-v2` embedding model via FAISS).
* **DuckDuckGo Fallback**: For terms not in the PDF, fetches and lightly summarizes top web results—only if they mention the query term.
* **Clean Output**: Splits long definitions into bullet points and filters out page-number footers.
* **Edge-Case Handling**:

  * Vague queries prompt clarification.

---

## Repository Structure

```
├── Data.pdf                # Source glossary PDF file
├── app.py                  # Streamlit application
├── agent.py                # Retrieval logic (PDF/semantic/web)
├── pipeline_stream.py      # Index-building script (PDF → FAISS index)
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

---

## Installation

### macOS / Linux

1. **Clone the repository**:

   ```bash
   git clone https://github.com/ThulasiAkula/liquide-intern-project.git
   cd liquide-intern-project
   ```

2. **Create & activate** a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

### Windows (PowerShell)

1. **Clone the repository**:

   ```powershell
   git clone https://github.com/ThulasiAkula/liquide-intern-project.git
   cd liquide-intern-project
   ```

2. **Create & activate** a virtual environment:

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**:

   ```powershell
   pip install -r requirements.txt
   ```

---

## Setup & Index Building

Before running the app, build the FAISS index from `Data.pdf`:

```bash
python pipeline_stream.py
```

You should see:

```
→ Extracted <N> glossary entries.
→ FAISS index built: <N> vectors
✅ Saved faiss.index and chunks.pkl
```

This generates:

* `faiss.index` — the persisted vector index.
* `chunks.pkl` — pickled list of "Term\nDefinition" entries.

---

## Running the App

Launch the Streamlit UI:

```bash
streamlit run app.py
```

1. Enter a financial term in the input box.
2. If found in the glossary (exact or semantic), the PDF definition is displayed.
3. If not found, a DuckDuckGo-sourced summary appears only if it includes the query.
4. Vague or invalid queries prompt clarifications or polite suggestions.

---

## Configuration & Customization

* **Embedding Model**: Modify `MODEL_NAME` in `pipeline_stream.py` and `agent.py` to switch embedding models.
* **Similarity Threshold**: In `agent.py`, adjust the `0.65` cosine-similarity threshold for semantic matches.
* **Bullet Formatting**: In `app.py`, tweak the length or sentence-count thresholds for bullet-point rendering.

---

## Troubleshooting

* **`RuntimeError: No glossary entries found`**: Check `Data.pdf` presence and formatting.
* **Empty search results**: Verify `faiss.index` and `chunks.pkl` exist—re-run `pipeline_stream.py` if necessary.
* **UI issues**: Ensure Python ≥3.7 and Streamlit are installed correctly.
