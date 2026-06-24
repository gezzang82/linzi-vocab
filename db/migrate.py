#!/usr/bin/env python3
"""
words.json + vocab_tracker.json -> Turso(libSQL) 1회성 마이그레이션.

사용법:
    pip install libsql-experimental
    export TURSO_DATABASE_URL="libsql://linzi-vocab-xxx.turso.io"
    export TURSO_AUTH_TOKEN="..."
    python db/migrate.py            # 기본 사용자 'linzi'로 적재
    python db/migrate.py --user mina

같은 명령을 다시 실행해도 UNIQUE 제약 + INSERT OR IGNORE 로 중복 없이 동작합니다.
"""
import argparse
import json
import os
import sys

try:
    import libsql_experimental as libsql
except ImportError:
    sys.exit("libsql-experimental 가 필요합니다:  pip install libsql-experimental")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")
WORDS_FILE = os.path.join(BASE, "words.json")
TRACKER_FILE = os.path.join(BASE, "vocab_tracker.json")


def connect():
    url = os.environ.get("TURSO_DATABASE_URL")
    token = os.environ.get("TURSO_AUTH_TOKEN")
    if not url or not token:
        sys.exit("환경변수 TURSO_DATABASE_URL / TURSO_AUTH_TOKEN 를 설정하세요.")
    return libsql.connect(database=url, auth_token=token)


def apply_schema(conn):
    with open(SCHEMA_FILE, encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    print("✅ 스키마 적용 완료")


def ensure_user(conn, username):
    conn.execute(
        "INSERT OR IGNORE INTO users(username, display_name) VALUES (?, ?)",
        (username, username),
    )
    conn.commit()
    row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    uid = row[0]
    conn.execute(
        "INSERT OR IGNORE INTO user_progress(user_id) VALUES (?)", (uid,)
    )
    conn.commit()
    return uid


def migrate_words(conn):
    if not os.path.exists(WORDS_FILE):
        print("⚠️ words.json 없음 - 단어 적재 건너뜀")
        return
    data = json.load(open(WORDS_FILE, encoding="utf-8"))
    words = data.get("words", [])
    for w in words:
        conn.execute(
            """INSERT OR IGNORE INTO words
               (word, pronunciation, pos, meaning, example, example_ko, tip)
               VALUES (?,?,?,?,?,?,?)""",
            (
                w.get("word"),
                w.get("pronunciation"),
                w.get("pos"),
                w.get("meaning"),
                w.get("example"),
                w.get("example_ko"),
                w.get("tip"),
            ),
        )
    conn.commit()
    conn.execute(
        "INSERT OR REPLACE INTO meta(key, value) VALUES ('last_generated', ?)",
        (str(data.get("last_generated", "")),),
    )
    conn.commit()
    print(f"✅ 단어 {len(words)}개 적재")


def migrate_tracker(conn, uid):
    if not os.path.exists(TRACKER_FILE):
        print("⚠️ vocab_tracker.json 없음 - 진행 데이터 건너뜀")
        return
    t = json.load(open(TRACKER_FILE, encoding="utf-8"))

    for w in t.get("weekly_words", []):
        conn.execute(
            "INSERT OR IGNORE INTO sent_words(user_id, word, meaning, sent_date) VALUES (?,?,?,?)",
            (uid, w.get("word"), w.get("meaning"), w.get("date")),
        )

    for word in t.get("studied_words", []):
        conn.execute(
            "INSERT OR IGNORE INTO studied_words(user_id, word) VALUES (?, ?)",
            (uid, word),
        )

    for wa in t.get("wrong_answers", []):
        if isinstance(wa, str):
            word, exp, cnt = wa, None, 1
        else:
            word, exp, cnt = wa.get("word"), wa.get("exp") or wa.get("expires_on"), wa.get("count", 1)
        conn.execute(
            "INSERT OR IGNORE INTO wrong_answers(user_id, word, expires_on, count) VALUES (?,?,?,?)",
            (uid, word, exp, cnt),
        )

    for q in t.get("quiz_history", []):
        conn.execute(
            "INSERT INTO quiz_history(user_id, quiz_date, score, total, detail) VALUES (?,?,?,?,?)",
            (
                uid,
                q.get("date"),
                q.get("score"),
                q.get("total"),
                json.dumps(q, ensure_ascii=False),
            ),
        )

    studied_total = len(t.get("studied_words", []))
    conn.execute(
        "UPDATE user_progress SET total_studied = ?, updated_at = datetime('now') WHERE user_id = ?",
        (studied_total, uid),
    )

    if t.get("week_start"):
        conn.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES ('week_start', ?)",
            (t["week_start"],),
        )
    conn.commit()
    print("✅ 진행/스트릭/오답/퀴즈 데이터 적재")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default="linzi", help="기본 사용자 username")
    args = ap.parse_args()

    conn = connect()
    apply_schema(conn)
    uid = ensure_user(conn, args.user)
    migrate_words(conn)
    migrate_tracker(conn, uid)
    print(f"\n🎉 마이그레이션 완료 (user='{args.user}', id={uid})")


if __name__ == "__main__":
    main()
