-- linzi-vocab Turso (libSQL) schema
-- 단어 목록 + 학습 진행/스트릭 + 사용자별 데이터

-- 사용자 ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  username     TEXT NOT NULL UNIQUE,          -- 로그인/식별용 (예: 'linzi')
  display_name TEXT,
  created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 단어 마스터 DB (words.json) ------------------------------------------
CREATE TABLE IF NOT EXISTS words (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  word          TEXT NOT NULL UNIQUE,
  pronunciation TEXT,
  pos           TEXT,
  meaning       TEXT NOT NULL,
  example       TEXT,
  example_ko    TEXT,
  tip           TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 발송된 단어 (vocab_tracker.weekly_words) -----------------------------
-- 매일 전송된 단어 기록. 사용자별로 구분.
CREATE TABLE IF NOT EXISTS sent_words (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  word      TEXT NOT NULL,
  meaning   TEXT,
  sent_date TEXT NOT NULL,                    -- YYYY-MM-DD
  UNIQUE(user_id, word, sent_date)
);
CREATE INDEX IF NOT EXISTS idx_sent_words_user_date ON sent_words(user_id, sent_date);

-- 학습 완료 단어 (vocab_tracker.studied_words) -------------------------
CREATE TABLE IF NOT EXISTS studied_words (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  word       TEXT NOT NULL,
  studied_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(user_id, word)
);

-- 오답 / 5일 복습 (vocab_tracker.wrong_answers, 프론트 wrong5) ---------
CREATE TABLE IF NOT EXISTS wrong_answers (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  word       TEXT NOT NULL,
  expires_on TEXT,                            -- 복습 만료일 YYYY-MM-DD
  count      INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(user_id, word)
);

-- 퀴즈 기록 (vocab_tracker.quiz_history) -------------------------------
CREATE TABLE IF NOT EXISTS quiz_history (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  quiz_date  TEXT NOT NULL,
  score      INTEGER,
  total      INTEGER,
  detail     TEXT,                            -- JSON 문자열 (문항별 상세)
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_quiz_history_user ON quiz_history(user_id, quiz_date);

-- 학습 진행 / 스트릭 (사용자당 1행) ------------------------------------
CREATE TABLE IF NOT EXISTS user_progress (
  user_id           INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  current_streak    INTEGER NOT NULL DEFAULT 0,
  longest_streak    INTEGER NOT NULL DEFAULT 0,
  last_studied_date TEXT,
  total_studied     INTEGER NOT NULL DEFAULT 0,
  updated_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 메타데이터 (week_start, last_generated, last_sent 등) ----------------
CREATE TABLE IF NOT EXISTS meta (
  key   TEXT PRIMARY KEY,
  value TEXT
);
