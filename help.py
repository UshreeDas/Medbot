import sqlite3

conn = sqlite3.connect("chat.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM users")
print(cursor.fetchall())
# import requests

# res = requests.post("http://127.0.0.1:11434/api/generate", json={
#     "model": "llama3.2",
#     "prompt": "how many days it takes to cure asthma?",
#     "stream": False
# })

# print(res.json())