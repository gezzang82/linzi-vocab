# Turso(libSQL) DB 연결 가이드

linzi-vocab 의 데이터(단어 목록 / 학습 진행·스트릭 / 사용자별 데이터)를 Turso 에 저장합니다.

## 구성

- `db/schema.sql` — 테이블 정의
- `db/migrate.py` — 기존 `words.json` / `vocab_tracker.json` → Turso 1회성 이전
- `api/words.js`, `api/tracker.js` — Vercel 서버리스 API (프론트엔드가 호출)
- 프론트엔드(`index.html`)는 `/api/tracker` 를 통해 읽고/씁니다.

## 1) DB 생성 (최초 1회, 직접 실행)

```bash
brew install turso          # CLI 설치
turso auth login            # 브라우저 로그인 (GitHub 계정)
turso db create linzi-vocab
turso db show linzi-vocab --url        # → TURSO_DATABASE_URL
turso db tokens create linzi-vocab     # → TURSO_AUTH_TOKEN
```

## 2) 로컬 환경변수

`.env.example` 을 복사해 `.env` 생성 후 위 값 입력.

## 3) 데이터 이전

```bash
pip install libsql-experimental
export TURSO_DATABASE_URL="libsql://..."
export TURSO_AUTH_TOKEN="..."
python db/migrate.py        # 기본 사용자 'linzi'
```

## 4) Vercel 환경변수 + 배포

```bash
vercel env add TURSO_DATABASE_URL production
vercel env add TURSO_AUTH_TOKEN production
vercel deploy --prod
```

## 스키마 요약

| 테이블 | 용도 |
|--------|------|
| `users` | 사용자 |
| `words` | 단어 마스터 DB |
| `sent_words` | 날짜별 발송 단어 |
| `studied_words` | 학습 완료 단어 |
| `wrong_answers` | 오답/5일 복습 |
| `quiz_history` | 퀴즈 기록 |
| `user_progress` | 스트릭/누적 진행 |
| `meta` | week_start 등 메타값 |
