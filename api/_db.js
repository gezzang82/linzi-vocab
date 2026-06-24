// 공용 Turso(libSQL) 클라이언트 + 헬퍼
import { createClient } from "@libsql/client";

export const db = createClient({
  url: process.env.TURSO_DATABASE_URL,
  authToken: process.env.TURSO_AUTH_TOKEN,
});

// username 으로 user_id 조회(없으면 생성). 기본값 'linzi'.
export async function getUserId(username = "linzi") {
  const u = (username || "linzi").trim();
  await db.execute({
    sql: "INSERT OR IGNORE INTO users(username, display_name) VALUES (?, ?)",
    args: [u, u],
  });
  const r = await db.execute({
    sql: "SELECT id FROM users WHERE username = ?",
    args: [u],
  });
  const id = r.rows[0].id;
  await db.execute({
    sql: "INSERT OR IGNORE INTO user_progress(user_id) VALUES (?)",
    args: [id],
  });
  return id;
}

export function readBody(req) {
  // Vercel 은 보통 req.body 를 파싱해 주지만, 문자열로 올 때를 대비.
  if (req.body && typeof req.body === "object") return req.body;
  try {
    return JSON.parse(req.body || "{}");
  } catch {
    return {};
  }
}

export function cors(res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET,POST,PUT,OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
}
