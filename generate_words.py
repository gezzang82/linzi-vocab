#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
매주 월요일 - OpenAI로 새 단어 50개 생성해서 words.json에 추가
GitHub Actions에서 실행됨
"""

import json, os, requests
from datetime import date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORDS_FILE = os.path.join(BASE_DIR, "words.json")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")

# Turso 백엔드 (웹앱/일일발송과 동일한 단일 소스)
API_BASE = os.environ.get("VOCAB_API_BASE", "https://linzi-vocab.vercel.app").rstrip("/")


def push_words_to_turso(words):
    """생성된 새 단어를 Turso(API)에 추가."""
    try:
        r = requests.post(f"{API_BASE}/api/words", json={"words": words}, timeout=30)
        r.raise_for_status()
        res = r.json()
        print(f"✅ Turso 반영: {res.get('added')}개 추가, 총 {res.get('total')}개")
        return True
    except Exception as e:
        print(f"⚠️ Turso 반영 실패: {e}")
        return False


def load_words():
    if os.path.exists(WORDS_FILE):
        with open(WORDS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"words": [], "last_generated": "", "total": 0}


def save_words(data):
    with open(WORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def generate_new_words(existing_words, count=50):
    # 최근 200개 단어만 제외 목록으로 전달 (프롬프트 길이 제한)
    existing_list = [w["word"] for w in existing_words[-200:]]
    existing_str = ", ".join(existing_list)

    prompt = f"""You are an English vocabulary expert for Korean learners.
Generate {count} NEW B1-B2 level practical English vocabulary words for daily life.

EXCLUDE these words (already in DB): {existing_str}

Cover varied topics: emotions, daily routines, work, communication, travel, health, relationships, etc.
Focus on words/phrases Koreans actually need in real daily conversations.

Respond with a JSON object in this exact format:
{{
  "words": [
    {{
      "word": "example",
      "pronunciation": "/ɪɡˈzɑːmpl/",
      "pos": "n/v",
      "meaning": "예시 / 예를 들다",
      "example": "Can you give me an example?",
      "example_ko": "예시를 들어줄 수 있어?",
      "tip": "exam(시험)+ple → 시험처럼 보여주는 것"
    }}
  ]
}}"""

    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"},
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 6000,
            "response_format": {"type": "json_object"}
        },
        timeout=60
    )

    if not resp.ok:
        raise Exception(f"OpenAI API 오류: {resp.status_code} {resp.text}")

    parsed = json.loads(resp.json()["choices"][0]["message"]["content"])
    return parsed.get("words", [])


def main():
    print(f"📚 단어 자동 생성 시작: {date.today()}")

    if not OPENAI_KEY:
        print("❌ OPENAI_API_KEY 없음")
        return

    data = load_words()
    # 중복 판단 기준은 Turso(단일 소스). 실패 시 로컬 words.json.
    try:
        existing = requests.get(f"{API_BASE}/api/words", timeout=15).json().get("words", [])
        print(f"현재 단어 수(Turso): {len(existing)}개")
    except Exception as e:
        existing = data.get("words", [])
        print(f"⚠️ Turso 조회 실패, 로컬 기준 {len(existing)}개: {e}")

    new_words = generate_new_words(existing, count=50)

    # 중복 제거
    existing_set = {w["word"].lower() for w in existing}
    filtered = [w for w in new_words if w.get("word", "").lower() not in existing_set]

    data["words"].extend(filtered)
    data["last_generated"] = date.today().isoformat()
    data["total"] = len(data["words"])

    save_words(data)
    print(f"✅ words.json {len(filtered)}개 추가 완료. 총 {data['total']}개")

    # Turso(단일 소스)에도 반영
    if filtered:
        push_words_to_turso(filtered)


if __name__ == "__main__":
    main()
