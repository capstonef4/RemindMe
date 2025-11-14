from flask import Flask, request, jsonify, session, render_template, redirect, send_from_directory

from werkzeug.utils import secure_filename
import mysql.connector
import bcrypt
import random

from datetime import date, datetime

import os

app = Flask(__name__,
            static_folder='static',
            static_url_path='/static')
app.config['SECRET_KEY'] = 'your_secret_key'
# 사진 업로드 설정
UPLOAD_FOLDER = 'static/uploads/photos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER




def get_db_connection():
    try:
        if os.getenv("DB_HOST"):  # Production - PostgreSQL
            import psycopg2
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST"),
                port=int(os.getenv("DB_PORT", "5432")),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASS"),
                database=os.getenv("DB_NAME"),
                sslmode='prefer'  # require 대신 prefer
            )
            print("✅ PostgreSQL 연결 성공")
        else:  # Local - MySQL
            import mysql.connector
            conn = mysql.connector.connect(
                host=os.getenv("DB_HOST"),
                port=int(os.getenv("DB_PORT")),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASS"),
                database=os.getenv("DB_NAME")
            )
            print("✅ MySQL 연결 성공")
        return conn
    except Exception as e:
        print(f"❌ DB 연결 실패: {e}")
        return None




def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# --- HTML 페이지 라우트들 ---
@app.route('/')
def index(): return render_template('index.html')


@app.route('/signup')
def signup_page(): return render_template('signup.html')


@app.route('/login')
def login_page(): return render_template('login.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)


@app.route('/guardian')
def guardian_page(): return render_template('guardian.html')


@app.route('/patient')
def patient_page(): return render_template('patient.html')


@app.route('/map')
def map_page():
    # 로그인 세션이 없으면 로그인 페이지로 리디렉션
    if "user_id" not in session:
        print("❌ 로그인되지 않은 접근 감지 — /map으로 진입 차단")
        return redirect("/login")

    print("🟢 로그인된 사용자:", session.get("user_id"), session.get("role"))
    return render_template('map.html')


@app.route('/call')
def call_page(): return render_template('call.html')


@app.route('/friend_request')
def friend_request_page(): return render_template('friend_request.html')


@app.route('/game')
def game_page(): return render_template('game.html')


@app.route('/math')
def math_page(): return render_template('math.html')


@app.route('/rock')
def rock_page(): return render_template('rock.html')





@app.route('/word')
def word_page(): return render_template('word.html')


@app.route('/color')
def color_page(): return render_template('color.html')


@app.route('/exercise')
def exercise_page(): return render_template('exercise.html')


# ====== 🆕 추억 대화 관련 ======
@app.route('/memory_upload')
def memory_upload_page(): return render_template('memory_upload.html')


@app.route('/memory_conversation')
def memory_conversation_page(): return render_template('memory_conversation.html')


# ------------------------------------
# ------------------------------------
# 회원가입
@app.route("/add_user", methods=["POST"])
def add_user():
    try:
        data = request.json
        user_name = data.get("user_name")
        user_phone = data.get("user_phone")
        user_id_login = data.get("user_id_login")
        user_password = data.get("user_password")
        role = data.get("role")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # ✅ 1️⃣ 중복 아이디 확인 추가
        cursor.execute("SELECT * FROM users WHERE user_id_login = %s", (user_id_login,))
        existing = cursor.fetchone()
        if existing:
            conn.close()
            return jsonify({"error": "이미 사용 중인 아이디입니다."}), 400

        # ✅ 2️⃣ 비밀번호 해싱
        password_hash = bcrypt.hashpw(user_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        # ✅ 3️⃣ DB 저장
        cursor.execute("""
            INSERT INTO users (user_name, user_phone, user_id_login, user_password, role)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_name, user_phone, user_id_login, password_hash, role))

        conn.commit()
        conn.close()
        return jsonify({"message": "회원가입 성공!"})

    except Exception as e:
        print("회원가입 오류:", e)
        return jsonify({"error": str(e)}), 500



# ------------------------------------
# 로그인
@app.route('/do_login', methods=['POST'])
def do_login():
    data = request.get_json()
    user_id_login = data.get("id")
    password = data.get("password")

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE user_id_login = %s", (user_id_login,))
        user = cursor.fetchone()
        conn.close()

        if not user:
            return jsonify({"error": "존재하지 않는 아이디입니다."}), 401

        if not bcrypt.checkpw(password.encode('utf-8'), user['user_pw'].encode('utf-8')):
            return jsonify({"error": "비밀번호가 올바르지 않습니다."}), 401

        # 로그인 성공 시 세션 저장
        session["user_id"] = user["user_id"]
        session["role"] = user["user_type"]

        return jsonify({
            "message": "로그인 성공",
            "user_id": user["user_id"],
            "role": user["user_type"]
        })

    except Exception as e:
        print("❌ 로그인 실패:", e)
        return jsonify({"error": str(e)}), 500





# ------------------------------------
# 친구 연결 요청
@app.route('/request_connection', methods=['POST'])
def request_connection():
    if "user_id" not in session:
        return jsonify({"error": "로그인이 필요합니다."}), 401

    guardian_id = session.get("user_id")
    data = request.get_json()
    patient_id = data.get("patient_id")

    if not patient_id:
        return jsonify({"error": "환자 ID가 없습니다."}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO connection_request (guardian_id, patient_id, status)
            VALUES (%s, %s, 'pending')
        """, (guardian_id, patient_id))
        conn.commit()
        conn.close()
        return jsonify({"message": "요청이 전송되었습니다."})
    except Exception as e:
        print("❌ 요청 실패:", e)
        return jsonify({"error": str(e)}), 500



@app.route("/requests", methods=["POST"])
def get_requests():
    try:
        data = request.json
        patient_id = data.get("patient_id")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT r.request_id, g.user_name AS guardian_name, r.status
            FROM connection_request r
            JOIN users g ON r.guardian_id = g.user_id
            WHERE r.patient_id = %s AND r.status = 'pending'
            ORDER BY r.request_id DESC
        """, (patient_id,))
        requests = cursor.fetchall()
        conn.close()

        return jsonify(requests)

    except Exception as e:
        print("❌ 요청 목록 불러오기 오류:", e)
        return jsonify({"error": "서버 내부 오류 발생"}), 500


@app.route("/accept_connection", methods=["POST"])
def accept_connection():
    try:
        data = request.json
        request_id = data.get("request_id")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 1️⃣ 요청 정보 가져오기
        cursor.execute("SELECT guardian_id, patient_id FROM connection_request WHERE request_id = %s", (request_id,))
        request_data = cursor.fetchone()
        if not request_data:
            conn.close()
            return jsonify({"error": "요청을 찾을 수 없습니다."}), 404

        guardian_id = request_data["guardian_id"]
        patient_id = request_data["patient_id"]

        # 2️⃣ 요청 상태를 accepted로 변경
        cursor.execute("""
            UPDATE connection_request
            SET status = 'accepted'
            WHERE request_id = %s
        """, (request_id,))

        # 3️⃣ connection 테이블에 실제 연결 정보 추가 (중복 방지)
        cursor.execute("""
            INSERT INTO connection (guardian_id, patient_id)
            SELECT %s, %s
            WHERE NOT EXISTS (
                SELECT 1 FROM connection WHERE guardian_id = %s AND patient_id = %s
            )
        """, (guardian_id, patient_id, guardian_id, patient_id))

        conn.commit()
        conn.close()
        return jsonify({"message": "요청이 성공적으로 수락되었습니다."})

    except Exception as e:
        print("❌ 연결 수락 처리 중 오류:", e)
        return jsonify({"error": str(e)}), 500


# ------------------------------------
# 연결된 환자 목록 조회
@app.route("/api/connected_patients", methods=["GET"])
def get_connected_patients():
    guardian_id = request.args.get("guardian_id")
    if not guardian_id:
        return jsonify({"error": "guardian_id가 필요합니다"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT u.user_id, u.user_name, u.user_phone
        FROM connection c
        JOIN users u ON c.patient_id = u.user_id
        WHERE c.guardian_id = %s
    """, (guardian_id,))
    patients = cursor.fetchall()
    conn.close()
    return jsonify({"patients": patients})


# ------------------------------------
# 사진 업로드
@app.route("/api/upload_photo", methods=["POST"])
def upload_photo():
    guardian_id = request.form.get('guardian_id')
    if not guardian_id:
        return jsonify({"error": "guardian_id가 없습니다"}), 400

    if 'photo' not in request.files:
        return jsonify({"error": "사진이 없습니다"}), 400

    file = request.files['photo']
    patient_id = request.form.get('patient_id')
    photo_date = request.form.get('photo_date', str(date.today()))
    location = request.form.get('location', '')
    description = request.form.get('description', '')

    if not patient_id:
        return jsonify({"error": "환자를 선택해주세요"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM connection WHERE guardian_id=%s AND patient_id=%s
    """, (guardian_id, patient_id))
    connection = cursor.fetchone()
    if not connection:
        conn.close()
        return jsonify({"error": "연결된 환자가 아닙니다"}), 403

    if file and allowed_file(file.filename):
        filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        cursor.execute("""
            INSERT INTO memory_photos (patient_id, guardian_id, filename, photo_date, location, description)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (patient_id, guardian_id, filename, photo_date, location, description))
        conn.commit()
        conn.close()
        return jsonify({"message": "사진이 업로드되었습니다!", "success": True})
    else:
        conn.close()
        return jsonify({"error": "허용되지 않은 파일 형식입니다"}), 400


# ------------------------------------
# 사진 목록 조회
@app.route("/api/photos/<int:patient_id>", methods=["GET"])
def get_photos(patient_id):
    user_id = request.args.get("guardian_id") or session.get("user_id")

    if not user_id:
        return jsonify({"error": "guardian_id가 필요합니다"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT mp.*, u.user_name AS guardian_name
        FROM memory_photos mp
        JOIN users u ON mp.guardian_id = u.user_id
        WHERE mp.patient_id = %s
        ORDER BY mp.photo_date DESC
    """, (patient_id,))
    photos = cursor.fetchall()
    conn.close()
    return jsonify({"photos": photos})


# ------------------------------------
# 환자 화면용: 보호자가 올린 최신 사진 1장 불러오기
@app.route("/api/daily_photos", methods=["POST"])
def get_daily_photos():
    try:
        data = request.get_json()
        patient_id = data.get("patient_id")

        if not patient_id:
            return jsonify({"error": "patient_id가 필요합니다"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 연결된 보호자의 최신 업로드 사진 1장만 가져오기
        cursor.execute("""
            SELECT mp.*, u.user_name AS guardian_name
            FROM memory_photos mp
            JOIN users u ON mp.guardian_id = u.user_id
            JOIN connection c ON mp.guardian_id = c.guardian_id AND mp.patient_id = c.patient_id
            WHERE mp.patient_id = %s
            ORDER BY mp.photo_id DESC
            LIMIT 1
        """, (patient_id,))
        latest_photo = cursor.fetchone()

        conn.close()

        if latest_photo:
            return jsonify({"memory_photo": [latest_photo]})
        else:
            return jsonify({"memory_photo": []})

    except Exception as e:
        print("❌ daily_photos 오류:", e)
        return jsonify({"error": str(e)}), 500


# ------------------------------------
# 환자 전화번호로 사용자 정보 조회
@app.route("/get_user_by_phone", methods=["POST"])
def get_user_by_phone():
    try:
        data = request.get_json()
        phone = data.get("phone")

        if not phone:
            return jsonify({"error": "전화번호가 필요합니다."}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT user_id, user_name, user_phone, role FROM users WHERE user_phone = %s", (phone,))
        user = cursor.fetchone()
        conn.close()

        if user:
            return jsonify(user)
        else:
            return jsonify({"error": "해당 전화번호의 사용자를 찾을 수 없습니다."}), 404

    except Exception as e:
        print("전화번호 조회 오류:", e)
        return jsonify({"error": "서버 오류"}), 500

# ------------------------------------
# 환자 위치 업데이트 (환자端)
@app.route("/update_location", methods=["POST"])
def update_location():
    try:
        data = request.json
        patient_id = data.get("patient_id")
        latitude = data.get("latitude")
        longitude = data.get("longitude")

        if not all([patient_id, latitude, longitude]):
            return jsonify({"error": "필수 데이터 누락"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # 없으면 새로, 있으면 갱신
        cursor.execute("""
            INSERT INTO patient_location (patient_id, latitude, longitude, updated_at)
            VALUES (%s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE latitude=%s, longitude=%s, updated_at=NOW()
        """, (patient_id, latitude, longitude, latitude, longitude))
        conn.commit()
        conn.close()

        return jsonify({"message": "위치 업데이트 성공"})
    except Exception as e:
        print("위치 업데이트 오류:", e)
        return jsonify({"error": str(e)}), 500

# ------------------------------------
# 보호자端: 연결된 환자들의 최신 위치 조회
@app.route("/get_patient_locations", methods=["GET"])
def get_patient_locations():
    guardian_id = request.args.get("guardian_id")
    if not guardian_id:
        return jsonify({"error": "guardian_id가 필요합니다"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT u.user_id, u.user_name, p.latitude, p.longitude, p.updated_at
        FROM connection c
        JOIN users u ON c.patient_id = u.user_id
        JOIN patient_location p ON u.user_id = p.patient_id
        WHERE c.guardian_id = %s
    """, (guardian_id,))
    locations = cursor.fetchall()
    conn.close()
    return jsonify({"locations": locations})



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)