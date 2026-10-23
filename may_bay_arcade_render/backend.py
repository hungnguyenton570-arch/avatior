import os
import sqlite3
from flask import Flask, jsonify, request, send_from_directory
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = os.environ.get("DATABASE_PATH", str(BASE_DIR / "arcade.db"))

app = Flask(__name__, static_folder="static", static_url_path="")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nickname TEXT NOT NULL UNIQUE,
                score INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

init_db()

@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.get("/api/health")
def health():
    return jsonify({"ok": True, "game": "May Bay Arcade"})

@app.post("/api/players")
def create_player():
    data = request.get_json(silent=True) or {}
    nickname = str(data.get("nickname", "")).strip()[:20]
    if len(nickname) < 2:
        return jsonify({"error": "Tên cần từ 2 đến 20 ký tự."}), 400
    try:
        with get_db() as conn:
            conn.execute("INSERT INTO players (nickname) VALUES (?)", (nickname,))
            conn.commit()
            row = conn.execute("SELECT id, nickname, score FROM players WHERE nickname = ?", (nickname,)).fetchone()
        return jsonify(dict(row)), 201
    except sqlite3.IntegrityError:
        with get_db() as conn:
            row = conn.execute("SELECT id, nickname, score FROM players WHERE nickname = ?", (nickname,)).fetchone()
        return jsonify(dict(row))

@app.get("/api/players/<int:player_id>")
def get_player(player_id):
    with get_db() as conn:
        row = conn.execute("SELECT id, nickname, score FROM players WHERE id = ?", (player_id,)).fetchone()
    if not row:
        return jsonify({"error": "Không tìm thấy người chơi."}), 404
    return jsonify(dict(row))

@app.post("/api/players/<int:player_id>/score")
def add_score(player_id):
    data = request.get_json(silent=True) or {}
    try:
        points = int(data.get("points", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "Điểm không hợp lệ."}), 400
    # Arcade-only: positive achievement points, capped per request.
    if points < 1 or points > 100:
        return jsonify({"error": "Mỗi lần chỉ cộng từ 1 đến 100 điểm."}), 400
    with get_db() as conn:
        row = conn.execute("SELECT id, nickname, score FROM players WHERE id = ?", (player_id,)).fetchone()
        if not row:
            return jsonify({"error": "Không tìm thấy người chơi."}), 404
        conn.execute("UPDATE players SET score = score + ? WHERE id = ?", (points, player_id))
        conn.commit()
        updated = conn.execute("SELECT id, nickname, score FROM players WHERE id = ?", (player_id,)).fetchone()
    return jsonify(dict(updated))

@app.get("/api/leaderboard")
def leaderboard():
    with get_db() as conn:
        rows = conn.execute("SELECT nickname, score FROM players ORDER BY score DESC, nickname ASC LIMIT 10").fetchall()
    return jsonify([dict(row) for row in rows])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
