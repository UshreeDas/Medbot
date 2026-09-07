from numpy import full
from chatbot import chatbot_stream
from db import *
from flask_cors import CORS
import os
from flask import Flask, request, jsonify, session, Response, send_from_directory, send_file
from PIL import Image
from io import BytesIO
import json
app = Flask(__name__)
#
SOURCE_FOLDER = os.path.join(
    os.path.dirname(__file__),
    "content",
    "drive",
    "MyDrive",
    "WTIND"
)
@app.route("/source/<filename>")
def source_image(filename):

    file_path = os.path.join(SOURCE_FOLDER, filename)

    print("SOURCE FOLDER:", SOURCE_FOLDER)
    print("REQUESTED:", filename)
    print("LOOKING FOR:", file_path)
    print("EXISTS:", os.path.exists(file_path))

    
    if os.path.exists(file_path):

        return send_from_directory(
            SOURCE_FOLDER,
            filename
        )

    
    if filename.lower().endswith(".png"):

        tif_filename = os.path.splitext(filename)[0] + ".tif"

        tif_path = os.path.join(
            SOURCE_FOLDER,
            tif_filename
        )

        print("TRYING TIF:", tif_path)
        print("TIF EXISTS:", os.path.exists(tif_path))

        if os.path.exists(tif_path):

            try:

                
                image = Image.open(tif_path)

                
                if image.mode not in ("RGB", "RGBA"):
                    image = image.convert("RGB")

                
                img_io = BytesIO()

                image.save(
                    img_io,
                    format="PNG"
                )

                img_io.seek(0)

                print("TIFF converted to PNG successfully")

                
                return send_file(
                    img_io,
                    mimetype="image/png",
                    download_name=filename
                )

            except Exception as e:

                print("TIFF CONVERSION ERROR:", e)

                return "Could not convert source image", 500

    return "Source image not found", 404
#
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False

app.secret_key = "super_secret_key"


CORS(app,
    supports_credentials=True,
    resources={r"/*": {"origins": "http://127.0.0.1:5500"}})
@app.route("/")
def home():
    return "MedBot API Running "
# REGISTER
@app.route("/register", methods=["POST"])
def register():
    print("REGISTER CALLED")
    data = request.json
    print("DATA:", data)
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"status": "error", "message": "Missing fields"})

    register_user(username, password)
    print("USER INSERTED")
    return jsonify({"status": "registered"})


# LOGIN
@app.route("/login", methods=["POST"])
def login():
    print("LOGIN CALLED")
    data = request.json
    print("DATA:", data)
    username = data.get("username")
    password = data.get("password")

    if login_user(username, password):
        session["user"] = username   
        print("SESSION AFTER LOGIN:", dict(session))
        print(f"Logged in: {username}")
        return jsonify({"status": "success"})
    else:
        print("LOGIN FAILED")
        return jsonify({"status": "fail"})


# NEW CHAT
@app.route("/new_chat", methods=["POST"])
def new_chat():
    user = session.get("user")

    if not user:
        return jsonify({"status": "error", "message": "Not logged in"})

    chat_id = request.json.get("chat_id")

    create_chat(chat_id, user)

    print(f"🆕 Chat created: {chat_id} | User: {user}")

    return jsonify({"status": "created"})


# GET USER CHATS
@app.route("/get_chats", methods=["GET"])
def get_chats():
    user = session.get("user")

    if not user:
        return jsonify([])

    chats = get_user_chats(user)

    return jsonify(chats)

# RENAME CHAT

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
# 
# DELETE CHAT
@app.route("/delete_chat", methods=["POST"])
def delete_chat_route():

    user = session.get("user")

    if not user:
        return jsonify({"status": "error"})

    data = request.json

    chat_id = data.get("chat_id")

    delete_chat(chat_id)

    return jsonify({"status": "deleted"})
# STREAM CHAT
import json


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

            sources = []

            for chunk, done, source_data in chatbot_stream(
                query,
                chat_id
            ):

                if chunk:
                    full += chunk

                    payload = {
                        'type': 'token',
                        'text': chunk
                    }
                    yield f"data: {json.dumps(payload)}\n\n"

                if source_data:
                    sources = source_data

            if sources:

                payload = {
                    'type': 'sources',
                    'sources': sources
                }
                yield f"data: {json.dumps(payload)}\n\n"

            payload = {
                'type': 'done'
            }
            yield f"data: {json.dumps(payload)}\n\n"

            if full.strip():

                save_message(
                    chat_id,
                    "user",
                    query
                )

                save_message(
                    chat_id,
                    "bot",
                    full
                )

        except Exception as e:

            payload = {
                'type': 'error',
                'message': str(e)
            }
            yield f"data: {json.dumps(payload)}\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )

# # LOAD CHAT HISTORY

@app.route("/history/<chat_id>", methods=["GET"])
def history(chat_id):
    messages = load_chat(chat_id)
    return jsonify(messages)
# kk
@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"status": "logged_out"})


# # RUN

if __name__ == "__main__":
    app.run(debug=True, threaded=True)