// 사용자별 학습 추적 데이터 (vocab_tracker.json 과 동일한 형태로 주고받음)
//
//   GET /api/tracker?user=linzi
//     -> { week_start, weekly_words, studied_words, wrong_answers, quiz_history, progress }
//
//   PUT /api/tracker?user=linzi   (body = 위 객체 전체)
//     -> tracker 전체를 저장(동기화). 프론트의 기존 ghSaveTracker 를 대체.
import { db, getUserId, readBody, cors } from "./_db.js";

async function loadTracker(uid) {
  const [meta, sent, studied, wrong, quiz, prog] = await Promise.all([
    db.execute("SELECT key, value FROM meta"),
    db.execute({ sql: "SELECT word, meaning, sent_date FROM sent_words WHERE user_id = ? ORDER BY id", args: [uid] }),
    db.execute({ sql: "SELECT word FROM studied_words WHERE user_id = ? ORDER BY id", args: [uid] }),
    db.execute({ sql: "SELECT word, expires_on, count FROM wrong_answers WHERE user_id = ?", args: [uid] }),
    db.execute({ sql: "SELECT quiz_date, score, total, detail FROM quiz_history WHERE user_id = ? ORDER BY id", args: [uid] }),
    db.execute({ sql: "SELECT current_streak, longest_streak, last_studied_date, total_studied FROM user_progress WHERE user_id = ?", args: [uid] }),
  ]);
  const metaMap = Object.fromEntries(meta.rows.map((r) => [r.key, r.value]));
  return {
    week_start: metaMap.week_start || "",
    weekly_words: sent.rows.map((r) => ({ word: r.word, meaning: r.meaning, date: r.sent_date })),
    studied_words: studied.rows.map((r) => r.word),
    wrong_answers: wrong.rows.map((r) => ({ word: r.word, exp: r.expires_on, count: r.count })),
    quiz_history: quiz.rows.map((r) => {
      try { return JSON.parse(r.detail); } catch { return { date: r.quiz_date, score: r.score, total: r.total }; }
    }),
    progress: prog.rows[0] || { current_streak: 0, longest_streak: 0, last_studied_date: null, total_studied: 0 },
  };
}

async function saveTracker(uid, t) {
  const tx = await db.transaction("write");
  try {
    if (t.week_start) {
      await tx.execute({ sql: "INSERT OR REPLACE INTO meta(key,value) VALUES ('week_start', ?)", args: [t.week_start] });
    }
    // 전체 교체 방식: 사용자 데이터 비우고 다시 적재 (동기화 단순화)
    await tx.execute({ sql: "DELETE FROM sent_words WHERE user_id = ?", args: [uid] });
    for (const w of t.weekly_words || []) {
      await tx.execute({
        sql: "INSERT OR IGNORE INTO sent_words(user_id, word, meaning, sent_date) VALUES (?,?,?,?)",
        args: [uid, w.word, w.meaning ?? null, w.date ?? null],
      });
    }
    await tx.execute({ sql: "DELETE FROM studied_words WHERE user_id = ?", args: [uid] });
    for (const word of t.studied_words || []) {
      await tx.execute({ sql: "INSERT OR IGNORE INTO studied_words(user_id, word) VALUES (?, ?)", args: [uid, word] });
    }
    await tx.execute({ sql: "DELETE FROM wrong_answers WHERE user_id = ?", args: [uid] });
    for (const wa of t.wrong_answers || []) {
      const word = typeof wa === "string" ? wa : wa.word;
      const exp = typeof wa === "string" ? null : wa.exp ?? wa.expires_on ?? null;
      const cnt = typeof wa === "string" ? 1 : wa.count ?? 1;
      await tx.execute({ sql: "INSERT OR IGNORE INTO wrong_answers(user_id, word, expires_on, count) VALUES (?,?,?,?)", args: [uid, word, exp, cnt] });
    }
    await tx.execute({ sql: "DELETE FROM quiz_history WHERE user_id = ?", args: [uid] });
    for (const q of t.quiz_history || []) {
      await tx.execute({
        sql: "INSERT INTO quiz_history(user_id, quiz_date, score, total, detail) VALUES (?,?,?,?,?)",
        args: [uid, q.date ?? null, q.score ?? null, q.total ?? null, JSON.stringify(q)],
      });
    }
    const totalStudied = (t.studied_words || []).length;
    await tx.execute({
      sql: "UPDATE user_progress SET total_studied = ?, updated_at = datetime('now') WHERE user_id = ?",
      args: [totalStudied, uid],
    });
    await tx.commit();
  } catch (e) {
    await tx.rollback();
    throw e;
  }
}

export default async function handler(req, res) {
  cors(res);
  if (req.method === "OPTIONS") return res.status(204).end();
  try {
    const uid = await getUserId((req.query && req.query.user) || "linzi");
    if (req.method === "GET") {
      return res.status(200).json(await loadTracker(uid));
    }
    if (req.method === "PUT" || req.method === "POST") {
      await saveTracker(uid, readBody(req));
      return res.status(200).json({ ok: true });
    }
    return res.status(405).json({ error: "GET/PUT only" });
  } catch (e) {
    return res.status(500).json({ error: String(e) });
  }
}
