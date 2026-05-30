#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
매일 아침 영단어 10개 카카오톡 알림 + HTML 페이지 생성
- 카톡: 알림 1개만 발송 (링크 포함)
- HTML: 단어, 예문, 발음, 팁, 퀴즈 포함
- 월~목: 새 단어 10개 (오답 재시험 포함)
- 금요일: 이번 주 전체 복습
"""

import json, os, random, subprocess
import requests
from datetime import datetime, date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKENS_FILE  = os.path.join(BASE_DIR, "kakao_tokens.json")
TRACKER_FILE = os.path.join(BASE_DIR, "vocab_tracker.json")
HTML_FILE    = os.path.join(BASE_DIR, "today_vocab.html")

# ── 단어 목록 (B1-B2 일상 실용 영어) ─────────────────────────────────────────
VOCAB_LIST = [
    # 감정/관계
    {"word": "upset",        "pronunciation": "/ʌpˈset/",        "pos": "adj/v", "meaning": "속상한 / 화나게 하다",           "example": "She was really upset when she heard the news.",              "tip": "up(뒤집다)+set → 감정이 뒤집힌 상태"},
    {"word": "awkward",      "pronunciation": "/ˈɔːkwərd/",      "pos": "adj",   "meaning": "어색한, 불편한",                 "example": "It was awkward when they ran into each other at the party.", "tip": "자리가 안 맞는 느낌 → 어색함"},
    {"word": "grateful",     "pronunciation": "/ˈɡreɪtfl/",      "pos": "adj",   "meaning": "감사하는",                      "example": "I'm so grateful for your help with the project.",            "tip": "great(크다) → 크게 감사하는"},
    {"word": "annoyed",      "pronunciation": "/əˈnɔɪd/",        "pos": "adj",   "meaning": "짜증난, 성가신",                 "example": "He was annoyed by the constant noise from next door.",       "tip": "annoy → ed → 짜증이 쌓인 상태"},
    {"word": "confident",    "pronunciation": "/ˈkɒnfɪdənt/",    "pos": "adj",   "meaning": "자신감 있는",                   "example": "She felt confident about her presentation.",                 "tip": "con+fide(믿다) → 자신을 믿는"},
    {"word": "exhausted",    "pronunciation": "/ɪɡˈzɔːstɪd/",    "pos": "adj",   "meaning": "완전히 지친, 탈진한",            "example": "I was absolutely exhausted after the long trip.",            "tip": "exhaust(소진) → 에너지가 완전히 빠진"},
    {"word": "relieved",     "pronunciation": "/rɪˈliːvd/",      "pos": "adj",   "meaning": "안도한",                        "example": "I was so relieved when the test was over.",                  "tip": "re+lieve(가볍게) → 무거운 짐이 사라진"},
    {"word": "jealous",      "pronunciation": "/ˈdʒeləs/",       "pos": "adj",   "meaning": "질투하는, 시기하는",              "example": "He was jealous of his friend's success.",                   "tip": "질투심이 불처럼 타오르는 이미지"},
    {"word": "embarrassed",  "pronunciation": "/ɪmˈbærəst/",     "pos": "adj",   "meaning": "당황한, 창피한",                 "example": "She was embarrassed when she forgot his name.",              "tip": "em+barrass(방해) → 마음이 막혀 얼굴이 빨개짐"},
    {"word": "disappointed", "pronunciation": "/ˌdɪsəˈpɔɪntɪd/","pos": "adj",   "meaning": "실망한",                        "example": "He was disappointed with his exam results.",                 "tip": "dis(부정)+appoint(기대) → 기대가 빗나간"},

    # 행동/습관
    {"word": "avoid",        "pronunciation": "/əˈvɔɪd/",        "pos": "v",     "meaning": "피하다, 회피하다",               "example": "Try to avoid eating too much sugar.",                        "tip": "a+void(빈 공간) → 빈 공간으로 비켜가다"},
    {"word": "manage",       "pronunciation": "/ˈmænɪdʒ/",       "pos": "v",     "meaning": "해내다, 관리하다",               "example": "Did you manage to finish the report on time?",               "tip": "manage to = 간신히 해내다"},
    {"word": "tend to",      "pronunciation": "/tend tuː/",       "pos": "v",     "meaning": "~하는 경향이 있다",              "example": "Students tend to study harder before exams.",                "tip": "tend = 기울다 → 그쪽으로 기울어진 습관"},
    {"word": "hesitate",     "pronunciation": "/ˈhezɪteɪt/",     "pos": "v",     "meaning": "망설이다, 주저하다",              "example": "Don't hesitate to ask me if you need help.",                 "tip": "hesi(걸리다) → 발걸음이 걸려 멈추는"},
    {"word": "handle",       "pronunciation": "/ˈhændl/",         "pos": "v",     "meaning": "다루다, 처리하다",               "example": "She knows how to handle difficult students.",                "tip": "손잡이(handle)를 잡고 능숙하게 다루다"},
    {"word": "figure out",   "pronunciation": "/ˈfɪɡər aʊt/",   "pos": "v",     "meaning": "알아내다, 이해하다",              "example": "I couldn't figure out how to use the new software.",         "tip": "figure(형태) → 형태를 파악해내다"},
    {"word": "give up",      "pronunciation": "/ɡɪv ʌp/",        "pos": "v",     "meaning": "포기하다",                      "example": "Never give up on your dreams.",                              "tip": "give(주다)+up → 위로 넘겨버리다 = 포기"},
    {"word": "keep in touch","pronunciation": "/kiːp ɪn tʌtʃ/", "pos": "v",     "meaning": "연락을 유지하다",                "example": "Let's keep in touch after you move.",                        "tip": "touch(접촉) 상태를 keep → 연락 유지"},
    {"word": "run into",     "pronunciation": "/rʌn ˈɪntuː/",   "pos": "v",     "meaning": "우연히 마주치다",                "example": "I ran into my old teacher at the supermarket.",              "tip": "달리다가 부딪히다 → 우연한 만남"},
    {"word": "bring up",     "pronunciation": "/brɪŋ ʌp/",       "pos": "v",     "meaning": "화제를 꺼내다 / 키우다",         "example": "She brought up an interesting point in the meeting.",        "tip": "위로 꺼내다 → 말을 꺼내다"},

    # 일상 상황
    {"word": "deadline",     "pronunciation": "/ˈdedlaɪn/",      "pos": "n",     "meaning": "마감 기한",                     "example": "The deadline for the assignment is next Friday.",            "tip": "dead+line → 넘으면 '죽는' 선"},
    {"word": "commute",      "pronunciation": "/kəˈmjuːt/",      "pos": "v/n",   "meaning": "통근하다 / 통근",                "example": "My daily commute takes about an hour.",                      "tip": "com+mute(바꾸다) → 집과 직장을 왔다 갔다"},
    {"word": "schedule",     "pronunciation": "/ˈskedʒuːl/",     "pos": "n/v",   "meaning": "일정 / 일정을 잡다",             "example": "Let me check my schedule for next week.",                    "tip": "시간표처럼 칸을 채우는 이미지"},
    {"word": "routine",      "pronunciation": "/ruːˈtiːn/",       "pos": "n/adj", "meaning": "일상, 루틴 / 일상적인",          "example": "Morning exercise is part of my daily routine.",              "tip": "route(길) → 매일 걷는 정해진 길"},
    {"word": "overwhelmed",  "pronunciation": "/ˌoʊvərˈwelmd/",  "pos": "adj",   "meaning": "압도된, 벅찬",                  "example": "I feel overwhelmed with so much work to do.",               "tip": "over+whelm → 파도에 완전히 덮인 느낌"},
    {"word": "distracted",   "pronunciation": "/dɪˈstræktɪd/",   "pos": "adj",   "meaning": "집중이 안 되는, 산만한",         "example": "I keep getting distracted by my phone.",                    "tip": "dis+tract(끌다) → 딴 곳으로 끌려가는"},
    {"word": "cancel",       "pronunciation": "/ˈkænsəl/",        "pos": "v",     "meaning": "취소하다",                      "example": "They had to cancel the meeting due to bad weather.",         "tip": "cancel = 선을 그어 지우다"},
    {"word": "remind",       "pronunciation": "/rɪˈmaɪnd/",       "pos": "v",     "meaning": "상기시키다, 생각나게 하다",      "example": "Can you remind me about the meeting tomorrow?",              "tip": "re+mind → 마음에 다시 불러오다"},
    {"word": "recommend",    "pronunciation": "/ˌrekəˈmend/",     "pos": "v",     "meaning": "추천하다",                      "example": "I highly recommend this restaurant.",                        "tip": "re+commend(맡기다) → 강하게 맡겨 추천"},
    {"word": "apologize",    "pronunciation": "/əˈpɒlədʒaɪz/",  "pos": "v",     "meaning": "사과하다",                      "example": "He apologized for being late to the meeting.",               "tip": "apology+ize → 사과의 말을 하다"},

    # 소통/표현
    {"word": "mention",      "pronunciation": "/ˈmenʃn/",         "pos": "v/n",   "meaning": "언급하다 / 언급",                "example": "Did you mention the new project to your boss?",              "tip": "men(마음)+tion → 마음에서 꺼내 말하다"},
    {"word": "assume",       "pronunciation": "/əˈsjuːm/",        "pos": "v",     "meaning": "추정하다, 가정하다",              "example": "Don't assume you know what others are thinking.",            "tip": "as+sume(잡다) → 사실처럼 잡아서 생각하다"},
    {"word": "agree",        "pronunciation": "/əˈɡriː/",         "pos": "v",     "meaning": "동의하다",                      "example": "I totally agree with what you said.",                        "tip": "a+gree(기분 좋은) → 서로 기분 좋게 맞추다"},
    {"word": "disagree",     "pronunciation": "/ˌdɪsəˈɡriː/",    "pos": "v",     "meaning": "반대하다, 의견이 다르다",         "example": "I disagree with your opinion on this matter.",               "tip": "dis(반대)+agree → 동의와 반대 방향"},
    {"word": "prefer",       "pronunciation": "/prɪˈfɜːr/",       "pos": "v",     "meaning": "선호하다",                      "example": "I prefer tea to coffee in the morning.",                    "tip": "pre+fer(가져오다) → 앞으로 가져오다 = 선호"},
    {"word": "complain",     "pronunciation": "/kəmˈpleɪn/",      "pos": "v",     "meaning": "불평하다, 항의하다",              "example": "Several students complained about the homework.",             "tip": "com+plain(치다) → 가슴을 치며 불평하다"},
    {"word": "persuade",     "pronunciation": "/pəˈsweɪd/",       "pos": "v",     "meaning": "설득하다",                      "example": "She persuaded him to try a new approach.",                   "tip": "per+suade(달콤한) → 달콤하게 설득하다"},
    {"word": "argue",        "pronunciation": "/ˈɑːrɡjuː/",       "pos": "v",     "meaning": "주장하다, 논쟁하다",              "example": "They argued about who should pay the bill.",                 "tip": "argue = 날카롭게 부딪히며 주장하다"},
    {"word": "admit",        "pronunciation": "/ədˈmɪt/",         "pos": "v",     "meaning": "인정하다, 고백하다",              "example": "He admitted that he had made a mistake.",                   "tip": "ad+mit(보내다) → 안으로 들여보내다 = 인정"},
    {"word": "insist",       "pronunciation": "/ɪnˈsɪst/",        "pos": "v",     "meaning": "주장하다, 고집하다",              "example": "She insisted on paying for the meal herself.",               "tip": "in+sist(서다) → 뜻 위에 굳건히 서다"},

    # 학습/성장
    {"word": "improve",      "pronunciation": "/ɪmˈpruːv/",       "pos": "v",     "meaning": "향상되다, 발전하다",              "example": "Your English has improved a lot this year.",                 "tip": "im+prove(증명) → 발전을 증명해가다"},
    {"word": "review",       "pronunciation": "/rɪˈvjuː/",        "pos": "v/n",   "meaning": "복습하다, 검토하다 / 복습",      "example": "Let's review what we learned last week.",                    "tip": "re+view → 다시 보다"},
    {"word": "memorize",     "pronunciation": "/ˈmeməraɪz/",      "pos": "v",     "meaning": "암기하다, 외우다",               "example": "I need to memorize these vocabulary words.",                 "tip": "memory+ize → 기억 속에 집어넣다"},
    {"word": "concentrate",  "pronunciation": "/ˈkɒnsntreɪt/",   "pos": "v",     "meaning": "집중하다",                      "example": "It's hard to concentrate when there's so much noise.",       "tip": "con+center → 중심으로 모으다"},
    {"word": "practice",     "pronunciation": "/ˈpræktɪs/",       "pos": "v/n",   "meaning": "연습하다 / 연습",                "example": "You need to practice speaking English every day.",           "tip": "practical(실용적) → 실제로 해보는 것"},
    {"word": "struggle",     "pronunciation": "/ˈstrʌɡl/",        "pos": "v/n",   "meaning": "애쓰다, 힘들어하다",              "example": "Many students struggle with grammar rules.",                 "tip": "strug(저항) → 저항과 싸우며 나아가다"},
    {"word": "achieve",      "pronunciation": "/əˈtʃiːv/",        "pos": "v",     "meaning": "성취하다, 달성하다",              "example": "You can achieve anything if you work hard enough.",          "tip": "a+chieve(끝) → 끝에 도달하다"},
    {"word": "challenge",    "pronunciation": "/ˈtʃælɪndʒ/",      "pos": "n/v",   "meaning": "도전 / 도전하다",                "example": "Learning a language is a challenge, but it's rewarding.",    "tip": "call+enge → 불러내어 도전하다"},
    {"word": "depend on",    "pronunciation": "/dɪˈpend ɒn/",     "pos": "v",     "meaning": "~에 달려있다, ~을 의존하다",     "example": "Success depends on how much effort you put in.",             "tip": "de+pend(달리다) → 결과가 달려있다"},
    {"word": "look forward to","pronunciation":"/lʊk ˈfɔːwəd tə/","pos":"v",     "meaning": "기대하다",                      "example": "I'm really looking forward to the holidays.",               "tip": "앞을 바라보다 → 기대감"},

    # 직장/사회생활
    {"word": "promote",      "pronunciation": "/prəˈmoʊt/",       "pos": "v",     "meaning": "승진시키다, 홍보하다",            "example": "She was promoted to team leader last month.",                "tip": "pro(앞으로)+mote(움직이다) → 앞으로 나아가다"},
    {"word": "resign",       "pronunciation": "/rɪˈzaɪn/",        "pos": "v",     "meaning": "사직하다, 辞职하다",             "example": "He resigned from his position after 10 years.",             "tip": "re+sign(서명) → 서명을 다시 → 그만두다"},
    {"word": "salary",       "pronunciation": "/ˈsæləri/",         "pos": "n",     "meaning": "급여, 봉급",                    "example": "She negotiated a higher salary with her new company.",       "tip": "라틴어 salarium(소금값) → 월급"},
    {"word": "colleague",    "pronunciation": "/ˈkɒliːɡ/",        "pos": "n",     "meaning": "동료",                          "example": "I went out for lunch with my colleagues.",                  "tip": "col+league(함께) → 함께 일하는 사람"},
    {"word": "feedback",     "pronunciation": "/ˈfiːdbæk/",       "pos": "n",     "meaning": "피드백, 의견",                  "example": "Your feedback really helped me improve my work.",            "tip": "feed(먹이다)+back → 발전을 위한 정보"},
    {"word": "deadline",     "pronunciation": "/ˈdedlaɪn/",       "pos": "n",     "meaning": "마감 기한",                     "example": "We need to meet the deadline no matter what.",               "tip": "dead+line → 넘으면 안 되는 선"},
    {"word": "presentation", "pronunciation": "/ˌprezənˈteɪʃn/", "pos": "n",     "meaning": "발표, 프레젠테이션",              "example": "I have to give a presentation in front of 50 people.",       "tip": "present(보여주다)+ation → 앞에서 보여주기"},
    {"word": "negotiate",    "pronunciation": "/nɪˈɡoʊʃieɪt/",   "pos": "v",     "meaning": "협상하다",                      "example": "They negotiated the price for an hour.",                    "tip": "neg+otiate(일) → 조건을 두고 주고받다"},
    {"word": "efficient",    "pronunciation": "/ɪˈfɪʃnt/",        "pos": "adj",   "meaning": "효율적인",                      "example": "Working from home can be very efficient.",                   "tip": "effici(만들어내다) → 낭비 없이 결과를 냄"},
    {"word": "deadline",     "pronunciation": "/ˈdedlaɪn/",       "pos": "n",     "meaning": "마감 기한",                     "example": "The project deadline is end of this week.",                  "tip": "dead+line → 이 선을 넘으면 '끝'"},
]

# 중복 제거
_seen = set()
_deduped = []
for _w in VOCAB_LIST:
    if _w["word"] not in _seen:
        _seen.add(_w["word"])
        _deduped.append(_w)
VOCAB_LIST = _deduped


# ── 유틸 함수 ──────────────────────────────────────────────────────────────

def load_tokens():
    with open(TOKENS_FILE, "r") as f:
        return json.load(f)

def save_tokens(tokens):
    with open(TOKENS_FILE, "w") as f:
        json.dump(tokens, f, indent=2, ensure_ascii=False)

def refresh_access_token(tokens):
    resp = requests.post("https://kauth.kakao.com/oauth/token", data={
        "grant_type":    "refresh_token",
        "client_id":     tokens["client_id"],
        "client_secret": tokens["client_secret"],
        "refresh_token": tokens["refresh_token"],
    })
    data = resp.json()
    if "access_token" in data:
        tokens["access_token"] = data["access_token"]
        if "refresh_token" in data:
            tokens["refresh_token"] = data["refresh_token"]
        save_tokens(tokens)
    return tokens

def send_kakao_notification(access_token, text, link_url):
    import json as _j
    template = {
        "object_type": "feed",
        "content": {
            "title": "📚 린지단어장",
            "description": text,
            "image_url": "https://raw.githubusercontent.com/gezzang82/linzi-vocab/main/banner.png",
            "link": {"web_url": link_url, "mobile_web_url": link_url}
        },
        "buttons": [
            {
                "title": "단어 보러 가기",
                "link": {"web_url": link_url, "mobile_web_url": link_url}
            }
        ]
    }
    resp = requests.post(
        "https://kapi.kakao.com/v2/api/talk/memo/default/send",
        headers={"Authorization": f"Bearer {access_token}"},
        data={"template_object": _j.dumps(template, ensure_ascii=False)}
    )
    return resp.json()

def load_tracker():
    if not os.path.exists(TRACKER_FILE):
        return {"week_start": "", "weekly_words": [], "wrong_answers": [], "quiz_history": []}
    with open(TRACKER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_tracker(tracker):
    with open(TRACKER_FILE, "w", encoding="utf-8") as f:
        json.dump(tracker, f, indent=2, ensure_ascii=False)

def get_week_start():
    today = date.today()
    import datetime as dt
    return (today - dt.timedelta(days=today.weekday())).isoformat()

def get_todays_words(tracker):
    week_start = get_week_start()
    if tracker["week_start"] != week_start:
        tracker["week_start"] = week_start
        tracker["weekly_words"] = []
        tracker["wrong_answers"] = []

    used = {w["word"] for w in tracker["weekly_words"]}
    available = [w for w in VOCAB_LIST if w["word"] not in used]
    wrong_words = [w for w in VOCAB_LIST if w["word"] in tracker.get("wrong_answers", [])]
    new_count = max(0, 10 - len(wrong_words))
    new_words = random.sample(available, min(new_count, len(available)))
    todays = (wrong_words + new_words)[:10]

    today_str = date.today().isoformat()
    for w in new_words:
        tracker["weekly_words"].append({"word": w["word"], "meaning": w["meaning"], "date": today_str})
    tracker["wrong_answers"] = []
    save_tracker(tracker)
    return todays


# ── HTML 생성 ──────────────────────────────────────────────────────────────

def generate_html(words, is_friday=False):
    import json as _j
    today = date.today()
    date_str = today.strftime("%Y년 %m월 %d일")
    weekday_names = ["월요일","화요일","수요일","목요일","금요일","토요일","일요일"]
    weekday = weekday_names[today.weekday()]
    title = "🎓 금요일 총복습" if is_friday else f"📚 오늘의 영단어 {len(words)}개"

    tmpl_path = os.path.join(BASE_DIR, "vocab_template.html")
    with open(tmpl_path, "r", encoding="utf-8") as f:
        html = f.read()

    html = html.replace("TITLE_PLACEHOLDER", title)
    html = html.replace("DATE_PLACEHOLDER", f"{date_str} {weekday}")
    html = html.replace("NEW_WORDS_PLACEHOLDER", str(len(words)))
    html = html.replace("TODAY_PLACEHOLDER", today.isoformat())
    html = html.replace("WORDS_JSON_PLACEHOLDER", _j.dumps(words, ensure_ascii=False))
    html = html.replace("ALL_WORDS_JSON_PLACEHOLDER", _j.dumps(VOCAB_LIST, ensure_ascii=False))
    return html

def _generate_html_old(words, is_friday=False):  # noqa: C901 — kept for reference
    import json as _json
    today = date.today()
    title = "🎓 금요일 총복습" if is_friday else f"📚 오늘의 영단어 {len(words)}개"
    words_json = _json.dumps(words, ensure_ascii=False)
    all_words_json = _json.dumps(VOCAB_LIST, ensure_ascii=False)
    return ""  # stub

def _unused_old_html():
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<title>{title}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}}
body{{font-family:-apple-system,'Noto Sans KR',sans-serif;background:#f0f4ff;min-height:100vh}}
:root{{--indigo:#4f46e5;--purple:#7c3aed;--green:#10b981;--red:#ef4444;--yellow:#f59e0b;--gray:#6b7280}}

/* ── 화면 전환 ── */
.screen{{display:none;min-height:100vh;flex-direction:column}}
.screen.active{{display:flex}}

/* ── 공통 헤더 ── */
.top-bar{{background:linear-gradient(135deg,#4f46e5,#7c3aed);color:white;padding:16px 20px}}
.top-bar h1{{font-size:1.1rem;font-weight:700}}
.top-bar .sub{{font-size:0.8rem;opacity:.8;margin-top:2px}}
.progress-wrap{{background:rgba(255,255,255,.2);border-radius:99px;height:6px;margin-top:10px}}
.progress-bar{{background:white;border-radius:99px;height:6px;transition:width .3s}}

/* ── 진입 화면 ── */
#screen-home{{background:linear-gradient(160deg,#4f46e5,#7c3aed);color:white;align-items:center;justify-content:center;text-align:center;padding:32px 24px;gap:24px}}
.streak-badge{{font-size:3rem}}
.streak-num{{font-size:2.5rem;font-weight:900}}
.streak-label{{font-size:0.9rem;opacity:.8;margin-top:-8px}}
.home-stats{{background:rgba(255,255,255,.15);border-radius:20px;padding:20px 32px;width:100%}}
.stat-row{{display:flex;justify-content:space-between;align-items:center;padding:8px 0}}
.stat-row+.stat-row{{border-top:1px solid rgba(255,255,255,.2)}}
.stat-label{{font-size:0.9rem;opacity:.85}}
.stat-val{{font-size:1rem;font-weight:700}}
.btn-start{{background:white;color:#4f46e5;border:none;border-radius:99px;padding:16px 48px;font-size:1.1rem;font-weight:800;cursor:pointer;width:100%;margin-top:8px}}

/* ── 플래시카드 화면 ── */
#screen-card{{background:#f0f4ff;padding:0}}
.card-area{{flex:1;display:flex;align-items:center;justify-content:center;padding:16px}}
.flashcard{{width:100%;max-width:420px;height:320px;perspective:1000px;cursor:pointer}}
.flashcard-inner{{width:100%;height:100%;position:relative;transform-style:preserve-3d;transition:transform .5s cubic-bezier(.4,0,.2,1)}}
.flashcard.flipped .flashcard-inner{{transform:rotateY(180deg)}}
.card-face{{position:absolute;width:100%;height:100%;backface-visibility:hidden;border-radius:24px;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:28px;box-shadow:0 8px 32px rgba(79,70,229,.15)}}
.card-front{{background:white}}
.card-back{{background:white;transform:rotateY(180deg)}}
.card-word{{font-size:2.2rem;font-weight:900;color:#1e1b4b;text-align:center}}
.card-pron{{font-size:0.9rem;color:#6b7280;margin-top:6px}}
.card-pos{{background:#e0e7ff;color:#4338ca;padding:3px 12px;border-radius:99px;font-size:0.8rem;font-weight:600;margin-top:10px}}
.card-hint{{font-size:0.85rem;color:#9ca3af;margin-top:20px}}
.card-meaning{{font-size:1.3rem;font-weight:700;color:#1e1b4b;text-align:center}}
.card-example{{font-size:0.85rem;color:#4b5563;background:#f9fafb;border-radius:12px;padding:10px 14px;margin-top:12px;line-height:1.6;text-align:center;width:100%}}
.card-tip{{font-size:0.8rem;color:#d97706;margin-top:8px;text-align:center}}
.tts-btn{{background:none;border:none;cursor:pointer;font-size:1.1rem;padding:2px 6px;border-radius:8px;transition:background .2s}}
.tts-btn:hover{{background:#e0e7ff}}
.card-actions{{display:flex;gap:12px;padding:0 16px 24px;width:100%;max-width:420px;margin:0 auto}}
.btn-knew{{flex:1;background:#10b981;color:white;border:none;border-radius:16px;padding:16px;font-size:1rem;font-weight:700;cursor:pointer}}
.btn-unknown{{flex:1;background:#f3f4f6;color:#374151;border:none;border-radius:16px;padding:16px;font-size:1rem;font-weight:700;cursor:pointer}}
.btn-back{{background:none;border:2px solid #d1d5db;color:#6b7280;border-radius:16px;padding:16px 14px;font-size:0.9rem;font-weight:600;cursor:pointer;white-space:nowrap}}
.card-counter{{text-align:center;font-size:0.85rem;color:#6b7280;padding:8px 0}}

/* ── 인터리빙 퀴즈 화면 ── */
#screen-quiz{{background:#f0f4ff;padding:0}}
.quiz-card{{background:white;border-radius:24px;margin:16px;padding:24px;box-shadow:0 4px 20px rgba(0,0,0,.08)}}
.quiz-word{{font-size:1.8rem;font-weight:900;color:#1e1b4b;text-align:center;margin-bottom:8px}}
.quiz-instruction{{font-size:0.85rem;color:#9ca3af;text-align:center;margin-bottom:20px}}
.quiz-options{{display:flex;flex-direction:column;gap:10px}}
.quiz-opt{{background:#f3f4f6;border:2px solid transparent;border-radius:14px;padding:14px 18px;font-size:0.95rem;cursor:pointer;text-align:left;color:#374151;transition:all .2s}}
.quiz-opt.correct{{background:#d1fae5;border-color:#10b981;color:#065f46}}
.quiz-opt.wrong{{background:#fee2e2;border-color:#ef4444;color:#991b1b}}
.quiz-opt:disabled{{cursor:default}}
.quiz-feedback{{text-align:center;font-size:1rem;font-weight:700;min-height:28px;margin-top:12px}}
.quiz-feedback.ok{{color:#10b981}}
.quiz-feedback.fail{{color:#ef4444}}
.btn-next{{width:calc(100% - 32px);margin:0 16px 24px;background:#4f46e5;color:white;border:none;border-radius:16px;padding:16px;font-size:1rem;font-weight:700;cursor:pointer;display:none}}

/* ── 완료 화면 ── */
#screen-done{{background:linear-gradient(160deg,#4f46e5,#7c3aed);color:white;align-items:center;justify-content:center;text-align:center;padding:32px 24px;gap:20px}}
.done-emoji{{font-size:4rem}}
.done-title{{font-size:1.8rem;font-weight:900}}
.done-score{{font-size:3rem;font-weight:900;margin:-8px 0}}
.done-stats{{background:rgba(255,255,255,.15);border-radius:20px;padding:20px;width:100%}}
.wrong-list{{width:100%;text-align:left}}
.wrong-list h3{{font-size:0.9rem;opacity:.8;margin-bottom:10px}}
.wrong-item{{background:rgba(255,255,255,.1);border-radius:12px;padding:10px 14px;margin-bottom:8px;font-size:0.9rem}}
.wrong-item span{{opacity:.7;font-size:0.8rem;display:block;margin-top:2px}}
.btn-retry{{background:white;color:#4f46e5;border:none;border-radius:99px;padding:14px 40px;font-size:1rem;font-weight:800;cursor:pointer}}
</style>
</head>
<body>

<!-- ── 진입 화면 ── -->
<div class="screen active" id="screen-home">
  <div class="streak-badge">🔥</div>
  <div class="streak-num" id="streak-num">0</div>
  <div class="streak-label">일 연속 학습</div>
  <div class="home-stats">
    <div class="stat-row">
      <span class="stat-label">📌 복습 대기</span>
      <span class="stat-val" id="review-count">0개</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">🆕 오늘 단어</span>
      <span class="stat-val">{len(words)}개</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">⏱ 예상 시간</span>
      <span class="stat-val">약 5분</span>
    </div>
  </div>
  <button class="btn-start" onclick="startLearning()">학습 시작 →</button>
  <div style="font-size:.75rem;opacity:.6">{date_str} {weekday}</div>
</div>

<!-- ── 플래시카드 화면 ── -->
<div class="screen" id="screen-card">
  <div class="top-bar">
    <h1>📚 {title}</h1>
    <div class="sub" id="card-sub">카드를 탭해서 뒤집어 보세요</div>
    <div class="progress-wrap"><div class="progress-bar" id="card-progress" style="width:0%"></div></div>
  </div>
  <div class="card-counter" id="card-counter"></div>
  <div class="card-area">
    <div class="flashcard" id="flashcard" onclick="flipCard()">
      <div class="flashcard-inner">
        <div class="card-face card-front">
          <div class="card-pos" id="fc-pos"></div>
          <div class="card-word" id="fc-word"></div>
          <div style="display:flex;align-items:center;gap:6px">
            <div class="card-pron" id="fc-pron"></div>
            <button class="tts-btn" onclick="event.stopPropagation();speak('word')" title="발음 듣기">🔊</button>
          </div>
          <div class="card-hint">👆 탭해서 뜻 확인</div>
        </div>
        <div class="card-face card-back">
          <div class="card-meaning" id="fc-meaning"></div>
          <div style="position:relative;width:100%">
            <div class="card-example" id="fc-example"></div>
            <button class="tts-btn" style="position:absolute;top:6px;right:6px" onclick="event.stopPropagation();speak('example')" title="예문 듣기">🔊</button>
          </div>
          <div class="card-tip" id="fc-tip"></div>
        </div>
      </div>
    </div>
  </div>
  <div class="card-actions">
    <button class="btn-back" id="btn-back" onclick="goBack()" style="display:none">← 이전</button>
    <button class="btn-unknown" onclick="rateCard(false)">❌ 몰랐어요</button>
    <button class="btn-knew" onclick="rateCard(true)">✅ 알았어요</button>
  </div>
</div>

<!-- ── 퀴즈 화면 ── -->
<div class="screen" id="screen-quiz">
  <div class="top-bar">
    <h1>⚡ 인터리빙 퀴즈</h1>
    <div class="sub" id="quiz-sub"></div>
    <div class="progress-wrap"><div class="progress-bar" id="quiz-progress" style="width:0%"></div></div>
  </div>
  <div class="quiz-card">
    <div class="quiz-word" id="q-word"></div>
    <div class="quiz-instruction">뜻을 선택하세요</div>
    <div class="quiz-options" id="q-options"></div>
    <div class="quiz-feedback" id="q-feedback"></div>
  </div>
  <button class="btn-next" id="btn-next" onclick="nextQuiz()">다음 →</button>
</div>

<!-- ── 완료 화면 ── -->
<div class="screen" id="screen-done">
  <div class="done-emoji">🎉</div>
  <div class="done-title">오늘 완료!</div>
  <div class="done-score" id="done-score"></div>
  <div class="done-stats" id="done-stats"></div>
  <div class="wrong-list" id="wrong-list"></div>
  <button class="btn-retry" onclick="location.reload()">다시 하기</button>
  <div style="font-size:.75rem;opacity:.6">내일 틀린 단어가 자동 복습됩니다</div>
</div>

<script>
// ── TTS ──
function speak(type) {{
  if (!window.speechSynthesis) return;
  const w = WORDS[cardIndex];
  const text = type === 'word' ? w.word : w.example.replace('💬 ', '');
  const utt = new SpeechSynthesisUtterance(text);
  utt.lang = 'en-US';
  utt.rate = type === 'word' ? 0.85 : 0.9;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utt);
}}

// ── 데이터 ──
const WORDS = {words_json};
const TODAY = "{today.isoformat()}";

// ── localStorage helpers ──
function getLS(k, def) {{
  try {{ return JSON.parse(localStorage.getItem(k)) ?? def; }} catch {{ return def; }}
}}
function setLS(k, v) {{ localStorage.setItem(k, JSON.stringify(v)); }}

// ── Streak ──
function updateStreak() {{
  let streak = getLS('streak', 0);
  const last = getLS('last_study', '');
  const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0,10);
  if (last === TODAY) return streak;
  if (last === yesterday) streak++;
  else if (last !== TODAY) streak = 1;
  setLS('streak', streak);
  setLS('last_study', TODAY);
  return streak;
}}

// ── 오답 시스템 (SM-2 간소화) ──
function getWrongWords() {{ return getLS('wrong_words', {{}}); }}
function saveWrongWords(ww) {{ setLS('wrong_words', ww); }}

function markWrong(word) {{
  const ww = getWrongWords();
  if (!ww[word]) ww[word] = {{count:0, interval:1, ease:2.5, next:TODAY}};
  ww[word].count++;
  ww[word].ease = Math.max(1.3, ww[word].ease - 0.2);
  ww[word].interval = 1;
  const d = new Date(); d.setDate(d.getDate() + 1);
  ww[word].next = d.toISOString().slice(0,10);
  saveWrongWords(ww);
}}

function markCorrect(word) {{
  const ww = getWrongWords();
  if (!ww[word]) return;
  ww[word].interval = Math.round(ww[word].interval * ww[word].ease);
  ww[word].ease = Math.min(3.0, ww[word].ease + 0.1);
  const d = new Date(); d.setDate(d.getDate() + ww[word].interval);
  ww[word].next = d.toISOString().slice(0,10);
  saveWrongWords(ww);
}}

function getDueReviews() {{
  const ww = getWrongWords();
  return Object.keys(ww).filter(w => ww[w].next <= TODAY);
}}

// ── 진입 화면 초기화 ──
(function initHome() {{
  const streak = updateStreak();
  document.getElementById('streak-num').textContent = streak;
  const due = getDueReviews();
  document.getElementById('review-count').textContent = due.length + '개';
}})();

// ── 학습 상태 ──
let cardIndex = 0;
let wrongInSession = [];
let correctInSession = [];
let quizQueue = [];
let quizIndex = 0;
let quizCorrect = 0;
let quizTotal = 0;
const QUIZ_INTERVAL = 3; // 3단어마다 퀴즈
let isFlipped = false;

function showScreen(id) {{
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
}}

function startLearning() {{
  showScreen('screen-card');
  renderCard();
}}

// ── 플래시카드 ──
function renderCard() {{
  const w = WORDS[cardIndex];
  document.getElementById('fc-word').textContent = w.word;
  document.getElementById('fc-pron').textContent = w.pronunciation;
  document.getElementById('fc-pos').textContent = w.pos;
  document.getElementById('fc-meaning').textContent = w.meaning;
  document.getElementById('fc-example').textContent = '💬 ' + w.example;
  document.getElementById('fc-tip').textContent = '💡 ' + w.tip;
  document.getElementById('card-counter').textContent = (cardIndex+1) + ' / ' + WORDS.length;
  document.getElementById('card-progress').style.width = ((cardIndex+1)/WORDS.length*100) + '%';
  document.getElementById('btn-back').style.display = cardIndex > 0 ? 'block' : 'none';
  isFlipped = false;
  document.getElementById('flashcard').classList.remove('flipped');
}}

function goBack() {{
  if (cardIndex <= 0) return;
  // 마지막 평가 취소
  const lastWord = WORDS[cardIndex - 1].word;
  correctInSession = correctInSession.filter(w => w !== lastWord);
  wrongInSession = wrongInSession.filter(w => w !== lastWord);
  cardIndex--;
  renderCard();
}}

function flipCard() {{
  isFlipped = !isFlipped;
  document.getElementById('flashcard').classList.toggle('flipped', isFlipped);
}}

function rateCard(knew) {{
  const word = WORDS[cardIndex].word;
  if (knew) {{
    correctInSession.push(word);
    markCorrect(word);
  }} else {{
    wrongInSession.push(word);
    markWrong(word);
  }}
  cardIndex++;

  // 3단어마다 즉시 퀴즈
  if (cardIndex < WORDS.length && cardIndex % QUIZ_INTERVAL === 0) {{
    const batch = WORDS.slice(cardIndex - QUIZ_INTERVAL, cardIndex);
    startQuiz(batch, false);
    return;
  }}

  if (cardIndex >= WORDS.length) {{
    // 전체 학습 후 최종 퀴즈
    startQuiz(WORDS, true);
    return;
  }}
  renderCard();
}}

// ── 퀴즈 ──
let quizBatch = [];
let isFinalQuiz = false;
let afterQuizCallback = null;

function startQuiz(batch, isFinal) {{
  isFinalQuiz = isFinal;
  quizBatch = isFinal ? [...batch].sort(() => Math.random()-.5).slice(0, Math.min(5, batch.length)) : [...batch];
  quizIndex = 0;
  quizCorrect = 0;
  quizTotal = quizBatch.length;
  showScreen('screen-quiz');
  renderQuiz();
}}

function renderQuiz() {{
  const w = quizBatch[quizIndex];
  document.getElementById('q-word').textContent = w.word;
  document.getElementById('quiz-sub').textContent = (quizIndex+1) + ' / ' + quizTotal + ' 문제';
  document.getElementById('quiz-progress').style.width = ((quizIndex+1)/quizTotal*100) + '%';
  document.getElementById('q-feedback').textContent = '';
  document.getElementById('q-feedback').className = 'quiz-feedback';
  document.getElementById('btn-next').style.display = 'none';

  // 보기 생성 (정답 1 + 오답 3)
  const others = WORDS.filter(x => x.word !== w.word).sort(() => Math.random()-.5).slice(0,3);
  const opts = [w, ...others].sort(() => Math.random()-.5);
  const container = document.getElementById('q-options');
  container.innerHTML = '';
  opts.forEach(opt => {{
    const btn = document.createElement('button');
    btn.className = 'quiz-opt';
    btn.textContent = opt.meaning;
    btn.onclick = () => selectAnswer(btn, w.word, opt.word, w.meaning);
    container.appendChild(btn);
  }});
}}

function selectAnswer(btn, correct, chosen, correctMeaning) {{
  document.querySelectorAll('.quiz-opt').forEach(b => b.disabled = true);
  const fb = document.getElementById('q-feedback');
  if (chosen === correct) {{
    btn.classList.add('correct');
    fb.textContent = '✅ 정답!';
    fb.className = 'quiz-feedback ok';
    quizCorrect++;
  }} else {{
    btn.classList.add('wrong');
    fb.textContent = '❌ 오답 — 정답: ' + correctMeaning;
    fb.className = 'quiz-feedback fail';
    markWrong(correct);
    if (!wrongInSession.includes(correct)) wrongInSession.push(correct);
  }}
  document.getElementById('btn-next').style.display = 'block';
}}

function nextQuiz() {{
  quizIndex++;
  if (quizIndex >= quizTotal) {{
    if (isFinalQuiz) {{
      showDone();
    }} else {{
      showScreen('screen-card');
      renderCard();
    }}
    return;
  }}
  renderQuiz();
}}

// ── 완료 화면 ──
function showDone() {{
  showScreen('screen-done');
  const pct = Math.round(quizCorrect / quizTotal * 100);
  const emoji = pct >= 90 ? '🏆' : pct >= 70 ? '🎉' : pct >= 50 ? '👍' : '💪';
  document.getElementById('done-score').textContent = emoji + ' ' + quizCorrect + '/' + quizTotal + '점';

  const stats = document.getElementById('done-stats');
  stats.innerHTML = `
    <div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid rgba(255,255,255,.2)">
      <span style="opacity:.8">정확도</span><strong>${{pct}}%</strong>
    </div>
    <div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid rgba(255,255,255,.2)">
      <span style="opacity:.8">알았어요</span><strong>${{correctInSession.length}}개</strong>
    </div>
    <div style="display:flex;justify-content:space-between;padding:6px 0">
      <span style="opacity:.8">오답 (내일 재출제)</span><strong>${{wrongInSession.length}}개</strong>
    </div>
  `;

  if (wrongInSession.length > 0) {{
    const wl = document.getElementById('wrong-list');
    wl.innerHTML = '<h3>틀린 단어</h3>';
    wrongInSession.forEach(word => {{
      const w = WORDS.find(x => x.word === word);
      if (!w) return;
      const div = document.createElement('div');
      div.className = 'wrong-item';
      div.innerHTML = `<strong>${{w.word}}</strong><span>${{w.meaning}}</span>`;
      wl.appendChild(div);
    }});
  }}
}}
</script>
</body>
</html>"""
    return html  # _unused_old_html stub end


# ── 메인 ──────────────────────────────────────────────────────────────────

def push_to_github(html_content, tokens):
    import base64
    gh_user  = tokens["github_user"]
    gh_repo  = tokens["github_repo"]
    gh_token = tokens["github_token"]
    api_url  = f"https://api.github.com/repos/{gh_user}/{gh_repo}/contents/index.html"

    headers = {
        "Authorization": f"token {gh_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # 기존 파일 SHA 가져오기 (업데이트 시 필요)
    r = requests.get(api_url, headers=headers)
    sha = r.json().get("sha") if r.status_code == 200 else None

    content_b64 = base64.b64encode(html_content.encode("utf-8")).decode("utf-8")
    payload = {
        "message": f"Daily vocab update {date.today().isoformat()}",
        "content": content_b64,
    }
    if sha:
        payload["sha"] = sha

    r = requests.put(api_url, headers=headers, json=payload)
    if r.status_code in (200, 201):
        print("✅ GitHub Pages 업로드 성공!")
        return f"https://{gh_user}.github.io/{gh_repo}/"
    else:
        print(f"❌ GitHub 업로드 실패: {r.json()}")
        return None

def already_sent_today():
    flag = os.path.join(BASE_DIR, ".last_sent")
    today = date.today().isoformat()
    if os.path.exists(flag):
        with open(flag) as f:
            if f.read().strip() == today:
                return True
    with open(flag, "w") as f:
        f.write(today)
    return False

def main():
    if already_sent_today():
        print("⚠️ 오늘 이미 발송했습니다. 종료합니다.")
        return
    print(f"🚀 단어 발송 시작: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    tokens  = load_tokens()
    tokens  = refresh_access_token(tokens)
    tracker = load_tracker()
    today   = date.today()
    is_friday = today.weekday() == 4

    if is_friday:
        all_week = [w for w in VOCAB_LIST if any(tw["word"] == w["word"] for tw in tracker.get("weekly_words", []))]
        words = all_week if all_week else get_todays_words(tracker)
    else:
        words = get_todays_words(tracker)

    # 1. HTML 파일 생성
    html = generate_html(words, is_friday)
    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ HTML 생성: {HTML_FILE}")

    # 2. GitHub Pages에 업로드
    link_url = push_to_github(html, tokens)
    if not link_url:
        link_url = f"file://{HTML_FILE}"

    # 3. 카톡 알림 1개 발송 (버튼+링크 포함)
    label = "🎓 금요일 총복습" if is_friday else "📚 오늘의 영단어"
    word_list = ", ".join([w["word"] for w in words[:5]]) + (" 외..." if len(words) > 5 else "")
    msg = f"{label} {len(words)}개 도착!\n{word_list}"

    result = send_kakao_notification(tokens["access_token"], msg, link_url)
    if result.get("result_code") == 0:
        print("✅ 카톡 알림 발송 성공!")
    else:
        print(f"❌ 카톡 실패: {result}")

    # 4. Mac에서 HTML 자동 오픈
    subprocess.run(["open", HTML_FILE])
    print(f"🎉 완료! GitHub Pages: {link_url}")

if __name__ == "__main__":
    main()
