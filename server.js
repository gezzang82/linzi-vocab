// Render(onrender.com)용 Node 웹 서버.
// 정적 파일(index.html 등) + /api 엔드포인트를 함께 제공한다.
// API 로직은 Vercel 서버리스 함수(api/*.js)를 그대로 재사용한다.
import express from "express";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import wordsHandler from "./api/words.js";
import trackerHandler from "./api/tracker.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const app = express();

app.use(express.json({ limit: "1mb" }));

// API 라우트 (Vercel 핸들러 시그니처 (req,res) 와 호환)
app.all("/api/words", (req, res) => wordsHandler(req, res));
app.all("/api/tracker", (req, res) => trackerHandler(req, res));

// 정적 파일 (루트의 index.html 을 / 로 서빙)
app.use(
  express.static(__dirname, {
    extensions: ["html"],
    index: "index.html",
  })
);

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`linzi-vocab 서버 실행 중 → http://localhost:${PORT}`);
});
