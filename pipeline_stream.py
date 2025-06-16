import pdfplumber
import faiss
import pickle
from sentence_transformers import SentenceTransformer

# Paths & model
PDF_PATH = "Data.pdf"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Load PDF into lines
def load_lines(path: str):
    lines = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                for ln in text.splitlines():
                    ln = ln.strip()
                    if ln:
                        lines.append(ln)
    return lines

# Identify glossary term lines
def is_term_line(line: str) -> bool:
    
    if len(line) == 1 and line.isupper():
        return False
   
    if line[-1] in ".?!;:,":
        return False
  
    words = line.split()
    if len(words) > 6:
        return False

    if not line[0].isalpha() or not line[0].isupper():
        return False
    return True

# Read and split into lines
lines = load_lines(PDF_PATH)

# Parse term-definition pairs
entries = []
i = 0
while i < len(lines):
    line = lines[i]
    if is_term_line(line):
        term = line
        def_lines = []
        j = i + 1
        while j < len(lines) and not is_term_line(lines[j]):
            def_lines.append(lines[j])
            j += 1
        definition = " ".join(def_lines).strip()
        if definition:
            entries.append(f"{term}\n{definition}")
        i = j
    else:
        i += 1

if not entries:
    raise RuntimeError("No glossary entries found; check PDF format.")

print(f"→ Extracted {len(entries)} glossary entries.")

# Embed & normalize
embedder = SentenceTransformer(MODEL_NAME)
embs = embedder.encode(entries, show_progress_bar=True, convert_to_numpy=True)
faiss.normalize_L2(embs)

# Build FAISS index
index = faiss.IndexFlatIP(embs.shape[1])
index.add(embs)
print(f"→ FAISS index built: {index.ntotal} vectors")

# Persist to disk
faiss.write_index(index, "faiss.index")
with open("chunks.pkl", "wb") as f:
    pickle.dump(entries, f)
print("Saved faiss.index and chunks.pkl")