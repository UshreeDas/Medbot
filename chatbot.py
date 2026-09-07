import os
os.environ["HF_HUB_OFFLINE"] = "1"
import json
import faiss
import pickle
import numpy as np
import requests

from sentence_transformers import SentenceTransformer
from langdetect import detect
from deep_translator import GoogleTranslator

from db import load_chat  

# =========================
# LOAD DATA
# =========================
index = faiss.read_index("indexeng.faiss")

with open("metadataeng.pkl", "rb") as f:
    documents = pickle.load(f)

print("Loaded docs:", len(documents))

model =SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2",
    local_files_only=True
)
# =========================
# TRANSLATION
# =========================
def translate_to_english(text):
    try:
        lang = detect(text)
        if lang != "en":
            return GoogleTranslator(source='auto', target='en').translate(text), lang
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
#  SEARCH 
# =========================
def search(query, k=5):
    emb = model.encode([query])
    emb = np.array(emb)

    distances, indices = index.search(emb, k * 3)

    results = []
    seen = set()

    for i, idx in enumerate(indices[0]):
        if idx >= len(documents):
            continue

        score = distances[0][i]

        
        if score > 1.0:
            continue

        text = documents[idx]["text"]

        if text not in seen:
            results.append(documents[idx])
            seen.add(text)

        if len(results) >= k:
            break

    return results

# =========================
# STREAMING GENERATOR
# =========================
def stream_llm(prompt):
    response = requests.post(
        "http://127.0.0.1:11434/api/generate",
        json={
            "model": "phi3:3.8b",
            "prompt": prompt,
            "stream": True,
            "options": {"temperature": 0.1, "num_predict": 300}
        },
        stream=True
    )

    for line in response.iter_lines():
        if line:
            try:
                data = json.loads(line.decode("utf-8"))
                token = data.get("response", "")
                yield token
            except:
                continue
# =========================
# BUILD PROMPT
# =========================
def build_prompt(query, chat_id):
    query_en, lang = translate_to_english(query)

    
    history = load_chat(chat_id)
    
    history_text = ""
    for r, m in history[-6:]:
        if r == "user":
            history_text += f"Patient: {m}\n"
        else:
            history_text += f"MedBot: {m}\n"

    results = search(query_en)
    context = "\n\n".join([r["text"] for r in results])
    sources = [] 

    
    for r in results:
        image = r.get("image")
        if image:
            filename = os.path.basename(image)
            if filename not in sources:
                sources.append(filename)

                
    prompt = f"""
You are MedBot, a medical assistant.

RULES:
- Use only the provided context as primary source
- Ignore unrelated past conversation
- You can tell dosages of medicines if it is there in the provided context for different ages.
- If follow-up → use history
- If partial info exists, answer partially
- Be medically helpful, Stay focused on symptoms and remedies only
- Give short clear bullet points


Context:
{context}

Previous Conversation:
{history_text}

User:
{query_en}
"""

    return prompt, lang,sources 

# =========================
# MAIN (STREAM)
# =========================


def chatbot_stream(query, chat_id):

    prompt, lang, sources = build_prompt(
        query,
        chat_id
    )

    full_answer = ""

    try:

        for token in stream_llm(prompt):

            if token is None:
                continue

            full_answer += token

            yield token, False, None

        if lang != "en":

            try:

                translated = translate_back(
                    full_answer,
                    lang
                )

                if translated:

                    

                    yield translated, False, None

            except Exception as e:

                print(
                    "TRANSLATION ERROR:",
                    e
                )

        if not full_answer.strip():

            yield "Not found", True, sources

        else:

            yield "", True, sources

    except GeneratorExit:

        print("Client disconnected")

    except Exception as e:

        print(
            "STREAM ERROR:",
            e
        )

        yield f"\nError: {e}", True, sources