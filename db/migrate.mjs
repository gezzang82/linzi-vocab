// words.json + vocab_tracker.json -> Turso 마이그레이션 (Node 버전)
// 사용법: node db/migrate.mjs [username]   (기본 'linzi')
import { createClient } from "@libsql/client";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, "..");
const USER = process.argv[2] || "linzi";

// .env 로드 (간단 파서)
for (const line of readFileSync(join(ROOT, ".env"), "utf-8").split("\n")) {
  const m = line.match(/^\s*([A-Z_]+)\s*=\s*"?([^"]*)"?\s*$/);
  if (m) process.env[m[1]] = m[2];
}

const db = createClient({
  url: process.env.TURSO_DATABASE_URL,
  authToken: process.env.TURSO_AUTH_TOKEN,
});

// 1) 스키마 적용
const schema = readFileSync(join(__dirname, "schema.sql"), "utf-8");
const stmts = schema
  .split(";")
  .map((s) => s.replace(/--.*$/gm, "").trim())
  .filter(Boolean);
for (const s of stmts) await db.execute(s);
console.log(`✅ 스키마 적용 (${stmts.length} statements)`);

// 2) 사용자
await db.execute({ sql: "INSERT OR IGNORE INTO users(username, display_name) VALUES (?, ?)", args: [USER, USER] });
const uid = (await db.execute({ sql: "SELECT id FROM users WHERE username = ?", args: [USER] })).rows[0].id;
await db.execute({ sql: "INSERT OR IGNORE INTO user_progress(user_id) VALUES (?)", args: [uid] });
console.log(`✅ 사용자 '${USER}' (id=${uid})`);

// 3) 단어 마스터
const wj = JSON.parse(readFileSync(join(ROOT, "words.json"), "utf-8"));
for (const w of wj.words || []) {
  await db.execute({
    sql: `INSERT OR IGNORE INTO words(word,pronunciation,pos,meaning,example,example_ko,tip) VALUES (?,?,?,?,?,?,?)`,
    args: [w.word, w.pronunciation ?? null, w.pos ?? null, w.meaning ?? null, w.example ?? null, w.example_ko ?? null, w.tip ?? null],
  });
}
await db.execute({ sql: "INSERT OR REPLACE INTO meta(key,value) VALUES ('last_generated', ?)", args: [String(wj.last_generated ?? "")] });
console.log(`✅ 단어 ${(wj.words || []).length}개`);

// 4) tracker
const t = JSON.parse(readFileSync(join(ROOT, "vocab_tracker.json"), "utf-8"));
for (const w of t.weekly_words || [])
  await db.execute({ sql: "INSERT OR IGNORE INTO sent_words(user_id,word,meaning,sent_date) VALUES (?,?,?,?)", args: [uid, w.word, w.meaning ?? null, w.date ?? null] });
for (const word of t.studied_words || [])
  await db.execute({ sql: "INSERT OR IGNORE INTO studied_words(user_id,word) VALUES (?,?)", args: [uid, word] });
for (const wa of t.wrong_answers || []) {
  const word = typeof wa === "string" ? wa : wa.word;
  const exp = typeof wa === "string" ? null : wa.exp ?? wa.expires_on ?? null;
  const cnt = typeof wa === "string" ? 1 : wa.count ?? 1;
  await db.execute({ sql: "INSERT OR IGNORE INTO wrong_answers(user_id,word,expires_on,count) VALUES (?,?,?,?)", args: [uid, word, exp, cnt] });
}
for (const q of t.quiz_history || [])
  await db.execute({ sql: "INSERT INTO quiz_history(user_id,quiz_date,score,total,detail) VALUES (?,?,?,?,?)", args: [uid, q.date ?? null, q.score ?? null, q.total ?? null, JSON.stringify(q)] });
await db.execute({ sql: "UPDATE user_progress SET total_studied=?, updated_at=datetime('now') WHERE user_id=?", args: [(t.studied_words || []).length, uid] });
if (t.week_start) await db.execute({ sql: "INSERT OR REPLACE INTO meta(key,value) VALUES ('week_start', ?)", args: [t.week_start] });
console.log(`✅ tracker: sent=${(t.weekly_words||[]).length}, studied=${(t.studied_words||[]).length}, wrong=${(t.wrong_answers||[]).length}, quiz=${(t.quiz_history||[]).length}`);

console.log("\n🎉 마이그레이션 완료");
