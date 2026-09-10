# =========================
# OFFLINE MODE
# =========================
import os
os.environ["HF_HUB_OFFLINE"] = "1"

# =========================
# IMPORTS
# =========================
import faiss
import pickle
import numpy as np
import requests
from sentence_transformers import SentenceTransformer
from langdetect import detect

# =========================
# LOAD DATA
# =========================
index = faiss.read_index("index.faiss")

with open("metadata.pkl", "rb") as f:
    documents = pickle.load(f)

print("Loaded documents:", len(documents))
from collections import Counter

langs = [d.get("language") for d in documents]
print(Counter(langs))
# =========================
# LOAD MULTILINGUAL MODEL
# =========================
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# =========================
# SEARCH FUNCTION
# =========================
def search(query, lang, k=5):
    query_embedding = model.encode([query])
    query_embedding = np.array(query_embedding)

    distances, indices = index.search(query_embedding, k * 5)

    same_lang = []
    other_lang = []

    for idx in indices[0]:
        if idx >= len(documents):
            continue

        doc = documents[idx]

        if doc.get("language") == lang:
            same_lang.append(doc)
        else:
            other_lang.append(doc)

        if len(same_lang) >= k:
            break

    # ✅ If enough same language → use them
    if len(same_lang) >= 2:
        return same_lang[:k]

    # ⚠️ fallback → mix
    return (same_lang + other_lang)[:k]
# =========================
# LLM FUNCTION
# =========================
def ask_llm(context, question, lang):
    prompt = f"""
Instruction:
You are an expert Indian Medical Assistant. Use the provided context to answer the question in {lang}. 
If the answer is not in the context, strictly say "Not found."

Constraints:
-'hi' means hindi language, 'en' means english,  'bn' means bengali. Answer in this language {lang}.
- Use bullet points for dosages if mentioned.
- Do NOT provide information outside of the context.
- NO introductory text like "Sure, I can help."

Context:
{context}

Question:
{question}

Answer ({lang})
"""

    try:
        response = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={
                "model": "  phi3:3.8b",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": .9,
                    "seed": 42,
                    "num_ctx": 4096
                    # "num_predict": 200   # prevent cutoff
                }
            }
        )

        data = response.json()

        if "response" in data:
            return data["response"]
        else:
            return f"LLM Error: {data}"

    except Exception as e:
        return f"Ollama error: {e}"

# =========================
# CHATBOT FUNCTION
# =========================
def chatbot(query):
    try:
        lang = detect(query)
    except:
        lang = "en"

    results = search(query, lang, k=3)

    context = "\n\n".join([r["text"] for r in results])

    answer = ask_llm(context, query,lang)
    print("Language detected:", lang)
    print("\n[DEBUG ANSWER]:\n", answer)

    return answer, results

# =========================
# DISPLAY SOURCES
# =========================
def show_sources(results):
    print("\nSOURCE REFERENCES:\n")

    for r in results:
        # PDF case (if you stored page info)
        if "page" in r:
            print(f"📄 PDF: {r.get('source', 'Unknown')} | Page: {r['page']}")
        else:
            print(f"🖼 Image: {r.get('source', 'Unknown')}")

        if "language" in r:
            print(f"🌐 Language: {r['language']}")

        print("-" * 40)

# =========================
# MAIN LOOP
# =========================
if __name__ == "__main__":
    while True:
        query = input("\nAsk something (or type 'exit'): ")

        if query.lower() == "exit":
            break

        answer, results = chatbot(query)

        print("\nANSWER:\n", answer)

        show_sources(results)