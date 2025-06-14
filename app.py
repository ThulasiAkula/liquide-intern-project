import streamlit as st
import re
from agent import retrieve

st.set_page_config(page_title="Liquide Glossary Search", layout="wide")
st.title("🔎 Liquide Glossary Search")


def is_page_marker(s: str) -> bool:
    """
    Returns True if the string is a standalone page number or page marker like '49' or '49 N'.
    """
    return bool(re.fullmatch(r"\d+\s*[A-Z]?", s.strip()))

query = st.text_input("Ask your question:")
if query:
    with st.spinner("Searching…"):
        ans = retrieve(query)

    source = ans.get("source")
    # Exact PDF lookup
    if source == "PDF":
        term = ans.get("term", "").strip() or query
        definition = ans.get("text", "").strip()
        st.subheader(term)

        # Split into sentences
        sentences = re.split(r'(?<=[\.\!?])\s+', definition)
        # Filter out page markers
        filtered = [sent.strip() for sent in sentences if sent.strip() and not is_page_marker(sent)]

        # If multiple sentences or long text, bullet-point
        if len(filtered) > 1 or len(" ".join(filtered)) > 100:
            for sent in filtered:
                st.markdown(f"- {sent}")
        else:
            # Single short definition
            if filtered:
                st.write(filtered[0])
            else:
                st.write("")

    # DuckDuckGo web summary (only if summary mentions query)
    elif source == "Web":
        st.subheader("🌐 Web Summary")
        summary = ans.get("text", "").strip()
        # If the summary does not mention the query term, treat as no match
        #if query.lower() not in summary.lower():
            #st.warning("I'm sorry, I wasn't able to find that term. Please verify the spelling and try again with the specific financial term.")
        #else:
        sentences = re.split(r'(?<=[\.\!?])\s+', summary)
        for sent in sentences:
            sent = sent.strip()
            if sent:
                st.markdown(f"- {sent}")


    # Edge-case: no result or vague query
    elif source == "None":
        message = ans.get("text", "")
        if "clarify" in message.lower():
            st.info(message)
        else:
            st.warning("I'm sorry, I wasn't able to find that term. Please verify the spelling and try again with the specific financial term.")

    # Fallback for unexpected sources
    else:
        st.error("Unexpected response. Please try again.")