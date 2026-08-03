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

# model = SentenceTransformer("all-MiniLM-L6-v2")
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
# BETTER SEARCH (FILTERED)
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

        # ✅ FILTER: ignore very far results
        if score > 1.0:
            continue

        text = documents[idx]["text"]

        if text not in seen:
            results.append(documents[idx])
            seen.add(text)

        if len(results) >= k:
            break

    return results
# def search(query, k=5):   ##BAD

#     emb = model.encode([query])
#     emb = np.array(emb).astype("float32")

#     distances, indices = index.search(emb, k)

#     results = []

#     for idx in indices[0]:

#         if idx < len(documents):
#             results.append(documents[idx])

#     return results

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
# def stream_llm(prompt): ##BAD

#     try:

#         response = requests.post(
#             "http://127.0.0.1:11434/api/generate",
#             json={
#                 "model": "phi3:3.8b",
#                 "prompt": prompt,
#                 "stream": True,
#                 "options": {
#                     "temperature": 0.3,
#                     "num_predict": 300
#                 }
#             },
#             stream=True
#         )

#         for line in response.iter_lines():

#             if not line:
#                 continue

#             try:
#                 data = json.loads(line.decode("utf-8"))

#                 token = data.get("response", "")

#                 if token:
#                     yield token

#             except:
#                 continue

#     except GeneratorExit:
#         return

#     except Exception as e:
#         yield f"\nError: {str(e)}"
# =========================
# BUILD PROMPT
# =========================
def build_prompt(query, chat_id):
    query_en, lang = translate_to_english(query)

    # ✅ LOAD HISTORY FROM DB
    history = load_chat(chat_id)
    # history_text = "\n".join([f"{r}: {m}" for r, m in history[-6:]])
    history_text = ""
    for r, m in history[-6:]:
        if r == "user":
            history_text += f"Patient: {m}\n"
        else:
            history_text += f"MedBot: {m}\n"

    results = search(query_en)
    context = "\n\n".join([r["text"] for r in results])

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

    return prompt, lang

# =========================
# MAIN (STREAM)
# =========================
def chatbot_stream(query, chat_id):
    prompt, lang = build_prompt(query, chat_id)
    full_answer = ""
    try:
        # STREAM ENGLISH TOKENS
        for token in stream_llm(prompt):
            if token is None:
                continue
            full_answer += token
            # STREAM ORIGINAL TOKEN
            yield token, False
        # FINAL TRANSLATION
        if lang != "en":
            try:
                translated = translate_back(full_answer, lang)
                if translated:
                    yield "\n\n" + translated, False
            except Exception as e:
                print("TRANSLATION ERROR:", e)
        if not full_answer.strip():
            yield "Not found", True
        else:
            yield "", True
    except GeneratorExit:
        print("Client disconnected")
    except Exception as e:
        print("STREAM ERROR:", e)
        yield f"\nError: {e}", True

# def chatbot_stream(query, chat_id):
#     prompt, lang = build_prompt(query, chat_id)

#     full_answer = ""

#     for token in stream_llm(prompt):
#         full_answer += token
#         yield translate_back(token, lang), False  # streaming

#     if not full_answer.strip():
#         yield "Not found", True
#     else:
#         yield "", True
# def chatbot_stream(query, chat_id):  ## BAD

#     prompt, lang = build_prompt(query, chat_id)

#     full_answer = ""

#     try:

#         for token in stream_llm(prompt):

#             translated = translate_back(token, lang)

#             full_answer += translated

#             yield translated, False

#     except GeneratorExit:
#         print("⚠️ Client disconnected during stream")
#         return

#     except Exception as e:
#         print("STREAM ERROR:", e)
#         yield f"\nError: {str(e)}", True
#         return

#     if not full_answer.strip():
#         yield "Not found", True
#     else:
#         yield "", True

# import os
# os.environ["HF_HUB_OFFLINE"] = "1"

# import faiss
# import pickle
# import numpy as np
# import requests

# from sentence_transformers import SentenceTransformer
# from langdetect import detect
# from deep_translator import GoogleTranslator

# # ✅ LANGCHAIN MEMORY
# # from langchain_classic.memory import ConversationSummaryMemory

# from langchain_core.language_models.llms import LLM

# # =========================
# # LOAD DATA
# # =========================
# index = faiss.read_index("indexeng.faiss")

# with open("metadataeng.pkl", "rb") as f:
#     documents = pickle.load(f)

# print("Loaded docs:", len(documents))


# # =========================
# # EMBEDDING MODEL
# # =========================
# model = SentenceTransformer("all-MiniLM-L6-v2")


# # =========================
# # CUSTOM LLM WRAPPER (OLLAMA)
# # =========================
# class OllamaLLM(LLM):
#     def _call(self, prompt, stop=None):
#         try:
#             response = requests.post(
#             "http://127.0.0.1:11434/api/generate",
#             json={
#                 "model": "llama3.2",
#                 "prompt": prompt,
#                 "stream": False,
#                 "options": {
#                     "temperature": 0.3,
#                     "num_predict": 300
#                 }
#             }
#         )
#             data = response.json()
#             output = data.get("response", "").strip()
#             print("RAW LLM RESPONSE:", data)
#             # ✅ FIX: fallback if empty
#             if not output:
#                 return "Not found"
#             return output
        
#         except Exception as e:
#             return f"LLM error: {e}"

#     @property
#     def _llm_type(self):
#         return "ollama"

    
# llm = OllamaLLM()


# # =========================
# # MEMORY STORE (PER CHAT)
# # =========================
# chat_histories = {}  # chat_id -> list of messages

# def get_history(chat_id):
#     if chat_id not in chat_histories:
#         chat_histories[chat_id] = []
#     return chat_histories[chat_id]


# # =========================
# # TRANSLATION
# # =========================
# def translate_to_english(text):
#     try:
#         lang = detect(text)
#         if lang != "en":
#             translated = GoogleTranslator(source='auto', target='en').translate(text)
#             return translated, lang
#         return text, "en"
#     except:
#         return text, "en"


# def translate_back(text, lang):
#     try:
#         if lang != "en":
#             return GoogleTranslator(source='en', target=lang).translate(text)
#     except:
#         pass
#     return text


# # =========================
# # SEARCH (IMPROVED)
# # =========================
# def search(query, k=5):
#     emb = model.encode([query])
#     emb = np.array(emb)

#     distances, indices = index.search(emb, k * 2)

#     results = []
#     seen = set()

#     for idx in indices[0]:
#         if idx < len(documents):
#             text = documents[idx]["text"]

#             if text not in seen:
#                 results.append(documents[idx])
#                 seen.add(text)

#         if len(results) >= k:
#             break

#     return results


# # =========================
# # MAIN CHATBOT
# # =========================
# def chatbot(query, chat_id):
#     # Detect language
#     query_en, lang = translate_to_english(query)

#     # Retrieve memory
#     history_list = get_history(chat_id)

# # convert history to text
#     history_text = "\n".join(history_list[-6:])  # last 6 messages only

#     # Search context
#     results = search(query_en)
#     context = "\n\n".join([r["text"] for r in results])

#     # Build prompt (CLEAN VERSION)
#     prompt = f"""
# You are a medical assistant.
# You can tell dosages if it is there in the provided context for different ages.
# Give bullet points.
# Complete your answer.
# Do not add any extra explanation.
# Prefer using the context
# If partial info available → answer partially
# If nothing relevant → say "Not found"
# Always give some helpful response

# Context:
# {context}

# User Question:
# {query_en}
# """

#     # Add memory
#     # history = memory.load_memory_variables({}).get("history", "")

#     full_prompt = f"""
# Previous Conversation:
# {history_text}

# {prompt}
# """

#     # Call LLM
#     answer_en = llm.invoke(full_prompt)

#     # Save memory
#     history_list.append(f"User: {query_en}")
#     history_list.append(f"Bot: {answer_en}")

#     # Translate back
#     final_answer = translate_back(answer_en, lang)

#     # Debug
#     print("\n=== USER ===\n", query)
#     # print("\n=== MEMORY SUMMARY ===\n", memory.buffer)
#     print("\n=== ANSWER ===\n", final_answer)

#     return final_answer, results