from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector

app = Flask(__name__)
CORS(app)

# MySQL 연결 설정
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1127",  
    database="myapp"
)
cursor = conn.cursor(dictionary=True)

@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    if cursor.fetchone():
        return jsonify({"success": False, "message": "이미 존재하는 사용자입니다"})

    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
    conn.commit()
    return jsonify({"success": True})

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
    user = cursor.fetchone()
    if user:
        return jsonify({"success": True, "token": f"{username}-token"})  # 실제 토큰은 JWT 등 추천
    else:
        return jsonify({"success": False})

@app.route("/auto_login", methods=["POST"])
def auto_login():
    data = request.get_json()
    token = data.get("token")

    if token.endswith("-token"):
        username = token.replace("-token", "")
        return jsonify({"success": True, "username": username})
    else:
        return jsonify({"success": False})

@app.route("/add_friend", methods=["POST"])
def add_friend():
    data = request.get_json()
    my_username = data.get("my_username")
    friend_username = data.get("friend_username")

    cursor.execute("SELECT * FROM users WHERE username=%s", (friend_username,))
    if not cursor.fetchone():
        return jsonify({"success": False, "message": "친구가 존재하지 않음"})

    cursor.execute("INSERT INTO friends (user, friend) VALUES (%s, %s)", (my_username, friend_username))
    conn.commit()
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(port=5000)

