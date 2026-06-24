// GET  /api/words            -> 단어 마스터 전체 { words:[...], total }
// GET  /api/words?date=YYYY-MM-DD&user=linzi -> 해당 날짜에 발송된 단어
// POST /api/words { words:[{word,...}] }     -> 단어 추가(INSERT OR IGNORE)
import { db, getUserId, readBody, cors } from "./_db.js";

export default async function handler(req, res) {
  cors(res);
  if (req.method === "OPTIONS") return res.status(204).end();

  if (req.method === "POST") {
    try {
      const body = readBody(req);
      const list = Array.isArray(body) ? body : body.words || [];
      let added = 0;
      for (const w of list) {
        if (!w || !w.word) continue;
        const r = await db.execute({
          sql: `INSERT OR IGNORE INTO words(word,pronunciation,pos,meaning,example,example_ko,tip)
                VALUES (?,?,?,?,?,?,?)`,
          args: [w.word, w.pronunciation ?? null, w.pos ?? null, w.meaning ?? null,
                 w.example ?? null, w.example_ko ?? null, w.tip ?? null],
        });
        added += r.rowsAffected || 0;
      }
      const total = (await db.execute("SELECT COUNT(*) c FROM words")).rows[0].c;
      return res.status(200).json({ added, total });
    } catch (e) {
      return res.status(500).json({ error: String(e) });
    }
  }

  if (req.method !== "GET") return res.status(405).json({ error: "GET/POST only" });

  try {
    const { date, user } = req.query || {};

    if (date) {
      const uid = await getUserId(user);
      const r = await db.execute({
        sql: `SELECT s.word, s.meaning, w.pronunciation, w.pos, w.example, w.example_ko, w.tip
              FROM sent_words s LEFT JOIN words w ON w.word = s.word
              WHERE s.user_id = ? AND s.sent_date = ?`,
        args: [uid, date],
      });
      return res.status(200).json({ date, words: r.rows });
    }

    const r = await db.execute(
      "SELECT word, pronunciation, pos, meaning, example, example_ko, tip FROM words ORDER BY id"
    );
    return res.status(200).json({ words: r.rows, total: r.rows.length });
  } catch (e) {
    return res.status(500).json({ error: String(e) });
  }
}
