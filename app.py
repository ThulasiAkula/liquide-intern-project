
import streamlit as st
import re
from agent import retrieve_multiple  

st.set_page_config(page_title="Liquide Glossary Search", layout="wide")
st.title("🔎 Liquide Glossary Search")

# Helper to ignore page numbers or section labels
def is_page_marker(s: str) -> bool:
    return bool(re.fullmatch(r"\d+\s*[A-Z]?", s.strip()))
   
query = st.text_input("Ask your question:")

# If query exists, search and display results
if query:
    with st.spinner("Searching…"):
        results = retrieve_multiple(query) 

    for subquery, ans in results:
        source = ans.get("source")

        if source == "PDF":
            term = ans.get("term", "").strip() or subquery
            definition = ans.get("text", "").strip()
            st.subheader(term)

            # Clean and format definition text
            sentences = re.split(r'(?<=[\.!?])\s+', definition)
            filtered = [s.strip() for s in sentences if s and not is_page_marker(s)]

            if len(filtered) > 1 or len(" ".join(filtered)) > 100:
                for sent in filtered:
                    st.markdown(f"- {sent}")
            else:
                st.write(filtered[0] if filtered else "")

        elif source == "Web":
            st.subheader(f"🌐 Web Summary for '{subquery}'")
            summary = ans.get("text", "").strip()
            for sent in re.split(r'(?<=[\.!?])\s+', summary):
                sent = sent.strip()
                if sent:
                    st.markdown(f"- {sent}")

        elif source == "None":
            st.warning(f"No answer found for \"{subquery}\". Please check your input.")
