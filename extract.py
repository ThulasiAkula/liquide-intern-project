# extract.py
import pdfplumber

def load_pdf(path: str) -> str:
    text = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text.append(page.extract_text() or "")

            
    return "\n\n".join(text)