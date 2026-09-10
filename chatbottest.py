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
from deep_translator import GoogleTranslator
from langdetect import detect

# =========================
# LOAD DATA
# =========================
index = faiss.read_index("indexeng.faiss")

with open("metadataeng.pkl", "rb") as f:
    documents = pickle.load(f)

print("Loaded documents:", len(documents))

# =========================
# LOAD MODEL
# =========================
model = SentenceTransformer('all-MiniLM-L6-v2')

# =========================
# TRANSLATION FUNCTIONS
# =========================
def translate_to_english(text):
    try:
        lang = detect(text)  # detect any language

        if lang != "en":
            translated = GoogleTranslator(source='auto', target='en').translate(text)
            return translated, lang

        return text, "en"

    except:
        return text, "en"


def translate_back(text, lang):
    try:
        if lang != "en":
            return GoogleTranslator(source='en', target=lang).translate(text)
    except:
        pass

    return text

# =========================
# SEARCH
# =========================
def search(query, k=3):
    query = query.lower().strip()

    query_embedding = model.encode([query])
    query_embedding = np.array(query_embedding)

    distances, indices = index.search(query_embedding, k)

    results = []
    for idx in indices[0]:
        results.append(documents[idx])

    return results

# =========================
# LLM
# =========================
def ask_llm(context, question):
    prompt = f"""
You are a medical assistant.
First try to understand what the user is asking about.
Answer ONLY from the context.
You can tell dosages if it is there in the provided context for different ages.
Give bullet points.
Complete your answer.
Do not add any extra explanation.
If not found, say: Not found.

Context:
{context}

Question:
{question}

Answer:
"""

    try:
        response = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={
                "model": "llama3.2",   # FAST model (recommended)
                "prompt": prompt,
                "stream": False,
                "options": {
                    # "num_predict": 300,
                    "temperature": 0.0,
                    
                    "top_p": 1,
                    "seed": 42
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
# CHATBOT
# =========================
def chatbot(query):
    # Step 1: Translate
    query_en, lang = translate_to_english(query)

    # Step 2: Search
    results = search(query_en, k=3)
    context = "\n\n".join([r["text"] for r in results])

    # Step 3: LLM
    answer_en = ask_llm(context, query_en)

    print("\n[DEBUG ENGLISH ANSWER]:\n", answer_en)

    # Step 4: Translate back (for ANY language)
    final_answer = translate_back(answer_en, lang)

    return final_answer, results

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    while True:
        query = input("\nAsk something (or type 'exit'): ")

        if query.lower() == "exit":
            break

        answer, results = chatbot(query)

        print("\nANSWER:\n", answer)

        print("\nSOURCE IMAGES:")
        for r in results:
            print(r["image"])