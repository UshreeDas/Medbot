from flask import Flask, request, jsonify, session, Response
from numpy import full
from chatbot import chatbot_stream
from db import *
from flask_cors import CORS
##################33############################################
# from faster_whisper import WhisperModel
# import tempfile
# import os
# model = WhisperModel(
#     "small",
#     device="cpu",
#     compute_type="int8"
# )
#############3###############################################################
app = Flask(__name__)
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False
# ✅ REQUIRED FOR SESSIONS
app.secret_key = "super_secret_key"

# ✅ allow cookies
CORS(app,
    supports_credentials=True,
    resources={r"/*": {"origins": "http://127.0.0.1:5500"}})
@app.route("/")
def home():
    return "MedBot API Running 🚀"
# -------------------------
# REGISTER
# -------------------------
@app.route("/register", methods=["POST"])
def register():
    print("🔥 REGISTER CALLED")
    data = request.json
    print("DATA:", data)
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"status": "error", "message": "Missing fields"})

    register_user(username, password)
    print("✅ USER INSERTED")
    return jsonify({"status": "registered"})


# -------------------------
# LOGIN
# -------------------------
@app.route("/login", methods=["POST"])
def login():
    print("🔥 LOGIN CALLED")
    data = request.json
    print("DATA:", data)
    username = data.get("username")
    password = data.get("password")

    if login_user(username, password):
        session["user"] = username   # ✅ FIX
        print("SESSION AFTER LOGIN:", dict(session))
        print(f"✅ Logged in: {username}")
        return jsonify({"status": "success"})
    else:
        print("❌ LOGIN FAILED")
        return jsonify({"status": "fail"})


# -------------------------
# NEW CHAT
# -------------------------
@app.route("/new_chat", methods=["POST"])
def new_chat():
    user = session.get("user")

    if not user:
        return jsonify({"status": "error", "message": "Not logged in"})

    chat_id = request.json.get("chat_id")

    create_chat(chat_id, user)

    print(f"🆕 Chat created: {chat_id} | User: {user}")

    return jsonify({"status": "created"})


# -------------------------
# GET USER CHATS
# -------------------------
@app.route("/get_chats", methods=["GET"])
def get_chats():
    user = session.get("user")

    if not user:
        return jsonify([])

    chats = get_user_chats(user)

    return jsonify(chats)
# -------------------------
# RENAME CHAT
# -------------------------
@app.route("/rename_chat", methods=["POST"])
def rename_chat_route():

    user = session.get("user")

    if not user:
        return jsonify({"status": "error"})

    data = request.json

    old_id = data.get("old_id")
    new_id = data.get("new_id")

    rename_chat(old_id, new_id)

    return jsonify({"status": "renamed"})
# -------------------------
# DELETE CHAT
# -------------------------
@app.route("/delete_chat", methods=["POST"])
def delete_chat_route():

    user = session.get("user")

    if not user:
        return jsonify({"status": "error"})

    data = request.json

    chat_id = data.get("chat_id")

    delete_chat(chat_id)

    return jsonify({"status": "deleted"})
# -------------------------
# STREAM CHAT
# -------------------------
@app.route("/chat", methods=["POST"])
def chat():
    user = session.get("user")
    if not user:
        return jsonify({"answer": "User not logged in"})

    data = request.json
    query = data["message"]
    chat_id = data["chat_id"]

    def generate():
        full = ""

        try:
            for chunk, done in chatbot_stream(query, chat_id):
                full += chunk
                yield chunk
        except Exception as e:
            yield f"\n[Error: {e}]"

        if full.strip():
            save_message(chat_id, "user", query)
            save_message(chat_id, "bot", full)
    # def generate():  ##BAD
    #     full = ""
    #     try:
    #         for chunk, done in chatbot_stream(query, chat_id):
    #             full += chunk
    #             yield chunk
    #     except GeneratorExit:
    #         print("⚠️ Browser disconnected")
    #         return
    #     except Exception as e:
    #         print("SERVER STREAM ERROR:", e)
    #         return
    #     try:
    #         if full.strip():
    #             save_message(chat_id, "user", query)
    #             save_message(chat_id, "bot", full)
    #     except Exception as e:
    #         print("DB SAVE ERROR:", e)



    return Response(generate(), mimetype='text/plain')


# # -------------------------
# # LOAD CHAT HISTORY
# # -------------------------
@app.route("/history/<chat_id>", methods=["GET"])
def history(chat_id):
    messages = load_chat(chat_id)
    return jsonify(messages)
# kk
@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"status": "logged_out"})
######################################################################
# @app.route("/speech", methods=["POST"])
# def speech():

#     audio = request.files["audio"]

#     temp = tempfile.NamedTemporaryFile(delete=False, suffix=".webm")
#     temp.close()

#     audio.save(temp.name)

#     try:
#         segments, info = model.transcribe(
#             temp.name,
#             beam_size=5
#         )

#         text = ""

#         for seg in segments:
#             text += seg.text

#         return jsonify({
#             "text": text,
#             "language": info.language
#         })

#     finally:
#         try:
#             os.remove(temp.name)
#         except:
#             pass
###################################################
# # -------------------------
# # RUN
# # -------------------------
# -------------------------
if __name__ == "__main__":
    app.run(debug=True, threaded=True)