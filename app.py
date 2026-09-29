# -*- coding: utf-8 -*-
"""
Math Practice Dashboard  (Streamlit, mobile-first)
Run:  streamlit run app.py
Progress local JSON file (progress.json) me save hota hai.
"""
import copy
import json
import math
import os
import random
import re
import time
from datetime import datetime, timedelta, timezone

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# =====================================================================
# CONFIG  (yahan se timer / ranges / topics badal sakte ho)
# =====================================================================
TIMER_SECONDS = 15                      # har question ka countdown
SPEED_SECONDS = 60                      # speed test ka time
DIFF_MAX = {"Easy": 10, "Medium": 20, "Hard": 30}   # difficulty -> max range
TOPICS = {                              # key: (icon, naam, css class)
    "table": ("🔢", "Table", "g-table"),
    "square": ("⬜", "Square", "g-square"),
    "cube": ("🧊", "Cube", "g-cube"),
    "frac": ("➗", "Fraction & Percentage", "g-frac"),
}
IST = timezone(timedelta(hours=5, minutes=30))     # India time (server UTC ho to bhi sahi din)

DEFAULT_PROG = {
    "daily": {},        # {"2026-07-01": {"total": 10, "correct": 8}}
    "topics": {t: {"total": 0, "correct": 0, "time": 0.0} for t in TOPICS},
    "mistakes": [],     # galat questions (streak = revision me kitni baar sahi)
    "best_streak": 0,   # lagatar sahi answers ka best
    "cur_streak": 0,    # abhi ka lagatar sahi answers
    "best_speed": 0,    # speed test ka best score
    "settings": {"daily_goal": 50, "timer_on": False, "sound": True, "difficulty": "Hard"},
    "resume": None,     # refresh par current question wapas laane ke liye
}

# =====================================================================
# CSS  (mobile-first, dark/light dono me readable)
# =====================================================================
CSS = """
#MainMenu, footer, header, [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"], .stDeployButton {display:none !important; visibility:hidden !important;}
.block-container {max-width:480px; padding:1rem .9rem 4rem !important;}
.stButton, [data-testid="stFormSubmitButton"] {width:100%;}
.stButton > button, [data-testid="stFormSubmitButton"] > button {
  width:100%; min-height:60px; font-size:20px; font-weight:700; border-radius:16px;}
.stButton > button p, [data-testid="stFormSubmitButton"] > button p {font-size:20px; font-weight:700;}
button[kind="primary"], button[kind="primaryFormSubmit"],
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"] {
  background:#16a34a !important; border-color:#16a34a !important; color:#fff !important;}
[data-testid="stForm"] {border:none !important; padding:0 !important;}
[data-testid="stNumberInput"] input {font-size:30px !important; height:64px; text-align:center; font-weight:700;}
[data-testid="stNumberInput"] button {display:none !important;}
.st-key-fracbox [data-testid="stHorizontalBlock"] {flex-direction:row !important; flex-wrap:nowrap !important; align-items:center; gap:.4rem;}
.st-key-fracbox [data-testid="stColumn"], .st-key-fracbox [data-testid="column"] {min-width:0 !important; width:auto !important; flex:1 1 0 !important;}
[class*="st-key-card_"] button {min-height:92px; border:none; color:#fff; box-shadow:0 4px 12px rgba(0,0,0,.25);}
[class*="st-key-card_"] button p {font-size:24px !important; font-weight:800; color:#fff !important;}
[class*="st-key-card_"] button:hover {filter:brightness(1.1); color:#fff;}
.st-key-card_table button {background:linear-gradient(135deg,#f97316,#ef4444);}
.st-key-card_square button {background:linear-gradient(135deg,#3b82f6,#6366f1);}
.st-key-card_cube button {background:linear-gradient(135deg,#10b981,#047857);}
.st-key-card_frac button {background:linear-gradient(135deg,#ec4899,#a855f7);}
.st-key-card_mixed button {background:linear-gradient(135deg,#475569,#0f172a);}
.st-key-card_mistakes button {background:linear-gradient(135deg,#dc2626,#7f1d1d);}
.g-table {background:linear-gradient(135deg,#f97316,#ef4444);}
.g-square {background:linear-gradient(135deg,#3b82f6,#6366f1);}
.g-cube {background:linear-gradient(135deg,#10b981,#047857);}
.g-frac {background:linear-gradient(135deg,#ec4899,#a855f7);}
.g-mixed {background:linear-gradient(135deg,#475569,#0f172a);}
.tiles {display:flex; gap:8px; margin:8px 0;}
.tile {flex:1; background:rgba(128,128,128,.15); border-radius:14px; padding:10px 4px; text-align:center;}
.tile b {display:block; font-size:22px;}
.tile span {font-size:12px; opacity:.75;}
.qcard {border-radius:22px; padding:22px 12px; text-align:center; color:#fff; margin:10px 0;}
.qcard .qt {font-size:15px; opacity:.92;}
.qcard .qx {font-size:clamp(28px,9vw,44px); font-weight:800; margin-top:6px; word-break:break-word;}
.res {border-radius:18px; padding:16px; text-align:center; color:#fff; font-size:28px; font-weight:800; margin:10px 0;}
.res span {display:block; font-size:20px; font-weight:600; margin-top:6px;}
.res.ok {background:#16a34a;} .res.bad {background:#dc2626;} .res.time {background:#d97706;}
.mini {border-radius:12px; padding:8px; text-align:center; color:#fff; font-weight:700; margin:6px 0;}
.mini.ok {background:#16a34a;} .mini.bad {background:#dc2626;}
.tip {background:rgba(250,204,21,.18); border-left:5px solid #facc15; border-radius:12px; padding:12px; margin:8px 0; font-size:16px;}
.pop {animation:pop .5s ease-out;}
.shake {animation:shake .5s;}
.flash {position:fixed; inset:0; pointer-events:none; z-index:9998; animation:flash .9s ease-out forwards;}
.flash.green {background:rgba(34,197,94,.45);} .flash.red {background:rgba(239,68,68,.45);}
@keyframes pop {0%{transform:scale(.5);opacity:0} 70%{transform:scale(1.12)} 100%{transform:scale(1);opacity:1}}
@keyframes shake {0%,100%{transform:translateX(0)} 20%{transform:translateX(-12px)} 40%{transform:translateX(12px)} 60%{transform:translateX(-8px)} 80%{transform:translateX(8px)}}
@keyframes flash {0%{opacity:1} 100%{opacity:0}}
.timer {font-size:22px; font-weight:800; text-align:center; margin-top:4px;}
.tbar {height:10px; border-radius:6px; background:rgba(128,128,128,.25); overflow:hidden; margin-bottom:6px;}
.tbar > div {height:100%; background:#22c55e; transition:width 1s linear;}
.tbar.low > div {background:#ef4444;}
.ctab {width:100%; border-collapse:collapse; font-size:18px;}
.ctab td, .ctab th {padding:8px; text-align:center; border-bottom:1px solid rgba(128,128,128,.3);}
.ctab th {background:rgba(128,128,128,.15);}
.trow {padding:12px; border-radius:14px; background:rgba(128,128,128,.15); margin:6px 0; display:flex; justify-content:space-between; gap:8px; flex-wrap:wrap;}
.trow.weak {background:rgba(239,68,68,.18); border:2px solid #ef4444;}
"""


def inject_css():
    st.markdown("<style>" + re.sub(r"\s*\n\s*", " ", CSS) + "</style>", unsafe_allow_html=True)


# =====================================================================
# STORAGE  (progress.json load / save)
# =====================================================================
def progress_path():
    """?u=naam lagane par alag file (progress_naam.json) - cloud par kaam aata hai."""
    uid = re.sub(r"[^a-zA-Z0-9_-]", "", str(st.query_params.get("u", "")))[:20]
    name = f"progress_{uid}.json" if uid else "progress.json"
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), name)


def load_progress(path):
    data = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            data = {}
    except (OSError, ValueError):
        data = {}                      # file nahi hai / kharab hai -> fresh start
    prog = copy.deepcopy(DEFAULT_PROG)
    for k, v in data.items():
        if k in ("settings", "topics") and isinstance(v, dict):
            prog[k].update(v)
        else:
            prog[k] = v
    for t in TOPICS:
        prog["topics"].setdefault(t, {"total": 0, "correct": 0, "time": 0.0})
    return prog


def save_progress():
    ss = st.session_state
    try:
        tmp = ss.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(ss.prog, f, ensure_ascii=False, indent=1)
        os.replace(tmp, ss.path)
    except OSError:
        ss.save_error = True


def S(key):
    """Setting padho."""
    return st.session_state.prog["settings"].get(key, DEFAULT_PROG["settings"][key])


def today_str():
    return datetime.now(IST).strftime("%Y-%m-%d")


def today_counts():
    d = st.session_state.prog["daily"].get(today_str(), {})
    return d.get("correct", 0), d.get("total", 0)


def overall():
    tp = st.session_state.prog["topics"].values()
    total = sum(t["total"] for t in tp)
    correct = sum(t["correct"] for t in tp)
    return total, correct, (correct * 100 // total if total else 0)


def daily_streak():
    """Kitne din lagatar practice ki (aaj na ki ho to kal se ginti)."""
    daily = st.session_state.prog["daily"]
    d = datetime.now(IST).date()
    if daily.get(d.isoformat(), {}).get("total", 0) == 0:
        d -= timedelta(days=1)
    n = 0
    while daily.get(d.isoformat(), {}).get("total", 0) > 0:
        n += 1
        d -= timedelta(days=1)
    return n


# =====================================================================
# QUESTION GENERATORS
# =====================================================================
TABLE_TIPS = {
    2: "x2 = number ko double karo.",
    3: "x3 = double karo, phir number ek baar aur jodo.",
    4: "x4 = double ka double.",
    5: "x5 = number ka aadha karo aur 10 se guna karo (ya x10 karke aadha).",
    6: "x6 = x5 nikalo, phir number ek baar jodo.",
    7: "x7 = x10 nikalo aur x3 ghatao.",
    8: "x8 = teen baar double karo (x2, x2, x2).",
    9: "x9 = x10 nikalo, phir number ghatao. Jaise 12x9 = 120 - 12 = 108.",
    10: "x10 = number ke aage 0 laga do.",
}
CUBE_LAST = {1: 1, 2: 8, 3: 7, 4: 4, 5: 5, 6: 6, 7: 3, 8: 2, 9: 9, 0: 0}


def gen_table(mx):
    a, b = random.randint(1, mx), random.randint(2, 10)
    return {"topic": "table", "text": f"{a} x {b} = ?", "kind": "num", "answer": a * b,
            "ans_text": str(a * b), "tip": TABLE_TIPS[b]}


def gen_square(mx):
    n = random.randint(1, mx)
    if n % 10 == 5:
        k = n // 10
        tip = f"5 par khatam hone wale square: {k} x {k + 1} = {k * (k + 1)}, uske aage 25 laga do -> {n * n}."
    elif n % 10 == 0:
        tip = f"{n}² = {n // 10}² ke aage 00 = {n * n}."
    elif n <= 10:
        tip = "1 se 10 ke square yaad kar lo (1, 4, 9, 16, 25, 36, 49, 64, 81, 100)."
    else:
        m = (n + 5) // 10 * 10
        d = abs(n - m)
        tip = f"Trick: ({n}+{d}) x ({n}-{d}) + {d}² = {n + d} x {n - d} + {d * d} = {n * n}."
    return {"topic": "square", "text": f"{n}² = ?", "kind": "num", "answer": n * n,
            "ans_text": str(n * n), "tip": tip}


def gen_cube(mx):
    n = random.randint(1, mx)
    ld = n % 10
    tip = (f"{n}³ = {n}² x {n} = {n * n} x {n}. Last digit trick: jis number ka last digit {ld} ho, "
           f"uske cube ka last digit {CUBE_LAST[ld]} hota hai.")
    return {"topic": "cube", "text": f"{n}³ = ?", "kind": "num", "answer": n ** 3,
            "ans_text": str(n ** 3), "tip": tip}


def gen_frac(mx):
    sub = random.choice(["f2p", "pof", "p2f"])
    if sub == "f2p":       # Fraction -> Percentage (Easy me sirf chhote denominators)
        dens = [2, 4, 5, 10] if mx <= 10 else [2, 4, 5, 10, 20, 25]
        den = random.choice(dens)
        num = random.randint(1, den - 1)
        mult = 100 // den
        ans = num * mult
        return {"topic": "frac", "text": f"{num}/{den} = ? %", "kind": "num", "answer": ans,
                "ans_text": f"{ans}%",
                "tip": f"100 / {den} = {mult}. Isliye {num}/{den} = {num} x {mult} = {ans}%."}
    if sub == "pof":       # Percentage of number (answer hamesha poora)
        p = random.randint(1, mx)
        step = 100 // math.gcd(p, 100)
        n = step * random.randint(1, max(1, 200 // step))
        ans = p * n // 100
        return {"topic": "frac", "text": f"{p}% of {n} = ?", "kind": "num", "answer": ans,
                "ans_text": str(ans),
                "tip": f"Pehle 1% nikalo (100 se bhaag): {n}/100 = {n / 100:g}. Phir x {p} = {ans}. (10% = ek zero hatao)"}
    p = random.randint(1, mx)  # Percentage -> Fraction (simplest form)
    g = math.gcd(p, 100)
    a, b = p // g, 100 // g
    tip = (f"{p}% = {p}/100. Upar-neeche {g} se kaato -> {a}/{b}." if g > 1
           else f"{p}% = {p}/100 (pehle se simplest form).")
    return {"topic": "frac", "text": f"{p}% = ? (a/b)", "kind": "frac", "answer": [a, b],
            "ans_text": f"{a}/{b}", "tip": tip}


GENERATORS = {"table": gen_table, "square": gen_square, "cube": gen_cube, "frac": gen_frac}


def make_question(topic, mx):
    return GENERATORS[topic](mx)


def new_question():
    """Naya question banao (pichle se alag)."""
    ss = st.session_state
    mx = DIFF_MAX.get(S("difficulty"), 30)
    q = None
    for _ in range(30):
        if ss.mode == "mistakes":
            ms = ss.prog["mistakes"]
            if not ms:
                q = None
                break
            q = {k: v for k, v in random.choice(ms).items() if k != "streak"}
        elif ss.mode == "speed":
            t = ss.speed["topic"]
            q = make_question(random.choice(list(TOPICS)) if t == "mixed" else t, mx)
        elif ss.mode == "mixed":
            q = make_question(random.choice(list(TOPICS)), mx)
        else:
            q = make_question(ss.topic, mx)
        if q["text"] != ss.last_text:
            break
    ss.q = q
    ss.q_start = time.time()
    ss.answered = False
    ss.result = None
    ss.qid += 1
    ss.last_text = q["text"] if q else None
    if ss.mode in ("topic", "mixed", "mistakes") and q:
        ss.prog["resume"] = {"mode": ss.mode, "topic": ss.topic, "q": q}
    else:
        ss.prog["resume"] = None
    save_progress()


# =====================================================================
# ANSWER CHECKING / RESULT REGISTER
# =====================================================================
def parse_input(q, raw):
    """(value, error) - khali/galat input par friendly message."""
    try:
        if q["kind"] == "num":
            if raw is None:
                return None, "Pehle apna answer likho 🙂"
            if raw != int(raw):
                return None, "Sirf poora number likho 🙂"
            return int(raw), None
        n, d = raw
        if n is None or d is None:
            return None, "Numerator aur denominator dono bharo 🙂"
        if d == 0:
            return None, "Denominator 0 nahi ho sakta 🙂"
        return (int(n), int(d)), None
    except (TypeError, ValueError):
        return None, "Answer sahi format me likho 🙂"


def judge(q, val):
    if q["kind"] == "num":
        return "ok" if val == q["answer"] else "wrong"
    a, b = q["answer"]
    n, d = val
    if n == a and d == b:
        return "ok"
    if n * b == d * a:
        return "unsimplified"      # barabar hai par simplest form nahi
    return "wrong"


def register_result(q, correct, elapsed):
    """Score, accuracy, streak, mistakes sab update + save."""
    ss = st.session_state
    prog = ss.prog
    day = prog["daily"].setdefault(today_str(), {"total": 0, "correct": 0})
    day["total"] += 1
    day["correct"] += int(correct)
    t = prog["topics"].setdefault(q["topic"], {"total": 0, "correct": 0, "time": 0.0})
    t["total"] += 1
    t["correct"] += int(correct)
    t["time"] += min(max(elapsed, 0.0), 120.0)
    milestone = False
    if correct:
        prog["cur_streak"] += 1
        prog["best_streak"] = max(prog["best_streak"], prog["cur_streak"])
        milestone = prog["cur_streak"] % 10 == 0
    else:
        prog["cur_streak"] = 0
    ms = prog["mistakes"]
    entry = next((m for m in ms if m["text"] == q["text"]), None)
    if ss.mode == "mistakes":
        if entry:
            if correct:
                entry["streak"] = entry.get("streak", 0) + 1
                if entry["streak"] >= 2:          # 2 baar sahi -> list se hatao
                    ms.remove(entry)
            else:
                entry["streak"] = 0
    elif not correct:
        if entry:
            entry["streak"] = 0
        else:
            ms.append({**q, "streak": 0})
            del ms[:-300]
    prog["resume"] = None
    goal_hit = day["total"] == prog["settings"]["daily_goal"]
    save_progress()
    return milestone, goal_hit


def finalize_answer(correct, timed_out=False):
    ss = st.session_state
    milestone, goal_hit = register_result(ss.q, correct, time.time() - ss.q_start)
    ss.answered = True
    ss.result = {"correct": correct, "timeout": timed_out, "milestone": milestone,
                 "goal_hit": goal_hit, "fx_done": False}


# =====================================================================
# ANIMATIONS / SOUND / FOCUS
# =====================================================================
def play_sound(kind):
    if not S("sound"):
        return
    notes = {"ok": [(660, 0.12), (880, 0.2)], "bad": [(220, 0.2), (150, 0.3)]}[kind]
    vib = "try{(window.parent.navigator||navigator).vibrate(200);}catch(e){}" if kind == "bad" else ""
    js = ("<script>try{const C=window.AudioContext||window.webkitAudioContext;const ctx=new C();"
          "let t=ctx.currentTime;" + json.dumps(notes) + ".forEach(([f,d])=>{const o=ctx.createOscillator(),"
          "g=ctx.createGain();o.frequency.value=f;g.gain.value=0.15;o.connect(g);g.connect(ctx.destination);"
          "o.start(t);o.stop(t+d);t+=d;});}catch(e){}" + vib + "</script>")
    components.html(js, height=0)


def autofocus(kind):
    """Input par cursor + numeric keypad, ya Next button par focus (Enter se next)."""
    marker = f"{kind}-{st.session_state.qid}"
    if kind == "input":
        js = ("const doc=window.parent.document;setTimeout(()=>{"
              "const list=Array.from(doc.querySelectorAll('input[type=\"number\"]'));"
              "list.forEach((el)=>{el.setAttribute('inputmode','numeric');"
              "if(!el.dataset.hk){el.dataset.hk='1';el.addEventListener('keydown',(e)=>{"
              "if(e.key!=='Enter')return;"
              "const l=Array.from(doc.querySelectorAll('input[type=\"number\"]'));const i=l.indexOf(el);"
              "if(i>=0&&i<l.length-1&&l[i+1].value===''){e.preventDefault();e.stopPropagation();l[i+1].focus();}"
              "},true);}});if(list.length){list[0].focus();}},250);")
    else:
        js = ("setTimeout(()=>{const b=Array.from(window.parent.document.querySelectorAll('button'))"
              ".find(x=>x.innerText.includes('Next'));if(b){b.focus();}},300);")
    components.html("<script>try{" + js + "}catch(e){}// " + marker + "</script>", height=0)


def run_result_fx(res):
    """Animation sirf ek baar chale (rerun par dobara nahi)."""
    if res.get("fx_done"):
        return
    res["fx_done"] = True
    if res["correct"]:
        st.balloons()
        if res.get("milestone"):
            st.snow()
        play_sound("ok")
    else:
        play_sound("bad")
    if res.get("goal_hit"):
        st.snow()
        st.toast("🎯 Daily goal poora ho gaya!")


# =====================================================================
# SMALL UI HELPERS
# =====================================================================
def tiles(items):
    h = "".join(f'<div class="tile"><b>{b}</b><span>{s}</span></div>' for b, s in items)
    st.markdown(f'<div class="tiles">{h}</div>', unsafe_allow_html=True)


def show_question(q):
    icon, name, cls = TOPICS[q["topic"]]
    st.markdown(f'<div class="qcard {cls}"><div class="qt">{icon} {name}</div>'
                f'<div class="qx">{q["text"]}</div></div>', unsafe_allow_html=True)


def answer_form(q, prefix):
    """Form: Enter dabane par bhi submit hota hai. Returns (submitted, raw)."""
    qid = st.session_state.qid
    with st.form(f"{prefix}_form_{qid}"):
        if q["kind"] == "num":
            raw = st.number_input("Answer", min_value=0, max_value=1_000_000, value=None, step=1,
                                  format="%d", key=f"{prefix}_ans_{qid}", placeholder="Answer likho",
                                  label_visibility="collapsed")
        else:
            with st.container(key="fracbox"):
                c1, c2, c3 = st.columns([5, 1, 5])
                n = c1.number_input("Numerator", min_value=0, max_value=1000, value=None, step=1,
                                    format="%d", key=f"{prefix}_n_{qid}", placeholder="a",
                                    label_visibility="collapsed")
                c2.markdown("<h2 style='text-align:center;margin:0'>/</h2>", unsafe_allow_html=True)
                d = c3.number_input("Denominator", min_value=0, max_value=1000, value=None, step=1,
                                    format="%d", key=f"{prefix}_d_{qid}", placeholder="b",
                                    label_visibility="collapsed")
            raw = (n, d)
        submitted = st.form_submit_button("✅ Submit", type="primary")
    return submitted, raw


def html_table(headers, rows):
    th = "".join(f"<th>{h}</th>" for h in headers)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    st.markdown(f'<table class="ctab"><tr>{th}</tr>{tr}</table>', unsafe_allow_html=True)


# =====================================================================
# NAVIGATION CALLBACKS
# =====================================================================
def go_home():
    ss = st.session_state
    if "prog" in ss:
        ss.prog["resume"] = None
        save_progress()
    ss.page = "home"
    ss.q = None
    ss.answered = False
    ss.result = None
    ss.confirm_reset = False


def goto(page):
    st.session_state.page = page


def start_quiz(mode, topic=None):
    ss = st.session_state
    ss.mode = mode
    if topic:
        ss.topic = topic
    ss.page = "quiz"
    ss.q = None
    ss.answered = False
    ss.result = None
    ss.last_text = None


def start_speed(topic):
    ss = st.session_state
    ss.speed = {"topic": topic, "start": time.time(), "attempted": 0, "correct": 0,
                "finished": False, "last": None, "new_best": False}
    ss.mode = "speed"
    ss.page = "speed"
    ss.last_text = None
    new_question()


def start_speed_from_widget():
    start_speed(st.session_state.get("w_speed_topic", "mixed"))


def set_setting(key, wkey):
    st.session_state.prog["settings"][key] = st.session_state[wkey]
    save_progress()


def ask_reset():
    st.session_state.confirm_reset = True


def cancel_reset():
    st.session_state.confirm_reset = False


def do_reset():
    ss = st.session_state
    settings = ss.prog["settings"]
    ss.prog = copy.deepcopy(DEFAULT_PROG)
    ss.prog["settings"] = settings
    ss.confirm_reset = False
    save_progress()


# =====================================================================
# PAGES
# =====================================================================
def page_home():
    ss = st.session_state
    st.markdown("## 🧮 Math Practice")
    c, t = today_counts()
    _, _, acc = overall()
    tiles([(f"{c}/{t}", "Aaj ka score"), (f"{acc}%", "Total accuracy"), (f"🔥 {daily_streak()}", "Din streak")])
    goal = S("daily_goal")
    st.progress(min(1.0, t / goal) if goal else 1.0)
    st.caption(f"🎯 Daily goal: {t}/{goal}" + ("  ✅ Poora!" if t >= goal else ""))

    keys = list(DIFF_MAX)
    st.radio("Difficulty", keys, index=keys.index(S("difficulty")), horizontal=True, key="w_diff",
             format_func=lambda k: f"{k} (1-{DIFF_MAX[k]})", on_change=set_setting,
             args=("difficulty", "w_diff"))

    for key, (icon, name, _) in TOPICS.items():
        st.button(f"{icon}  {name}", key=f"card_{key}", on_click=start_quiz, args=("topic", key))
    st.button("🎲  Mixed Test", key="card_mixed", on_click=start_quiz, args=("mixed",))
    n_m = len(ss.prog["mistakes"])
    st.button(f"❌  Mistakes Revision ({n_m})", key="card_mistakes", on_click=start_quiz, args=("mistakes",))

    st.markdown("##### 🛠️ Aur tools")
    st.button("⚡ Speed Test (60 sec)", key="tool_speed", on_click=goto, args=("speed_setup",))
    st.button("📚 Learning Mode (Charts)", key="tool_chart", on_click=goto, args=("chart",))
    st.button("📊 Stats", key="tool_stats", on_click=goto, args=("stats",))

    with st.expander("⚙️ Settings"):
        st.toggle("⏱️ Timer mode (15 sec / question)", value=S("timer_on"), key="w_timer",
                  on_change=set_setting, args=("timer_on", "w_timer"))
        st.toggle("🔊 Sound", value=S("sound"), key="w_sound", on_change=set_setting, args=("sound", "w_sound"))
        st.number_input("🎯 Daily goal (questions)", min_value=5, max_value=1000, value=int(goal), step=5,
                        key="w_goal", on_change=set_setting, args=("daily_goal", "w_goal"))
        if not ss.confirm_reset:
            st.button("🗑️ Reset Progress", key="reset_ask", on_click=ask_reset)
        else:
            st.warning("Pakka? Saara progress, stats aur mistakes delete ho jayenge.")
            st.button("Haan, reset karo", key="reset_yes", type="primary", on_click=do_reset)
            st.button("Nahi, rehne do", key="reset_no", on_click=cancel_reset)


@st.fragment(run_every=1)
def quiz_timer():
    """Har second sirf yeh chhota hissa refresh hota hai. Time khatam -> galat."""
    ss = st.session_state
    if ss.answered or ss.q is None:
        return
    left = TIMER_SECONDS - (time.time() - ss.q_start)
    if left <= 0:
        finalize_answer(False, timed_out=True)
        st.rerun()
    pct = max(0, min(100, left / TIMER_SECONDS * 100))
    cls = "low" if left <= 5 else ""
    st.markdown(f'<div class="timer">⏱️ {int(math.ceil(left))}s</div>'
                f'<div class="tbar {cls}"><div style="width:{pct:.0f}%"></div></div>', unsafe_allow_html=True)


def show_result(q):
    ss = st.session_state
    res = ss.result
    ans = q["ans_text"]
    if res["correct"]:
        html = (f'<div class="flash green"></div><div class="res ok pop">Sahi! 🎉'
                f'<span>Streak 🔥 {ss.prog["cur_streak"]}</span></div>')
    elif res["timeout"]:
        html = (f'<div class="flash red"></div><div class="res time shake">Time khatam ⏰ Galat ❌'
                f'<span>Sahi answer: {ans}</span></div>')
    else:
        html = (f'<div class="flash red"></div><div class="res bad shake">Galat ❌'
                f'<span>Sahi answer: {ans}</span></div>')
    st.markdown(html, unsafe_allow_html=True)
    if not res["correct"] and q.get("tip"):
        st.markdown(f'<div class="tip">💡 <b>Shortcut:</b> {q["tip"]}</div>', unsafe_allow_html=True)
    run_result_fx(res)


def next_question():
    new_question()


def page_quiz():
    ss = st.session_state
    st.button("🏠 Home", key="home_q", on_click=go_home)
    if ss.q is None:
        new_question()
    q = ss.q
    if q is None:                                   # mistakes list khali
        st.success("🎉 Koi galat question bacha nahi! Bahut badhiya.")
        return
    c, t = today_counts()
    tiles([(f"🔥 {ss.prog['cur_streak']}", "Streak"), (f"{c}/{t}", "Aaj ka score"),
           (f"{t}/{S('daily_goal')}", "Daily goal")])
    title = {"mixed": "🎲 Mixed Test", "mistakes": "❌ Mistakes Revision"}.get(ss.mode)
    if title:
        st.markdown(f"**{title}**")
    if not ss.answered and S("timer_on"):
        quiz_timer()
    show_question(q)

    if not ss.answered:
        submitted, raw = answer_form(q, "quiz")
        if submitted:
            if S("timer_on") and time.time() - ss.q_start > TIMER_SECONDS + 1:
                finalize_answer(False, timed_out=True)
                st.rerun()
            val, err = parse_input(q, raw)
            if err:
                st.warning(err)
            else:
                verdict = judge(q, val)
                if verdict == "unsimplified":
                    st.warning("Value barabar hai, par simplest form me likho (jaise 2/4 ki jagah 1/2) ✍️")
                else:
                    finalize_answer(verdict == "ok")
                    st.rerun()
        autofocus("input")
    else:
        show_result(q)
        st.button("➡️ Next Question", key="next_q", type="primary", on_click=next_question)
        autofocus("next")


# ---------------------------- SPEED TEST ----------------------------
def finish_speed():
    ss = st.session_state
    s = ss.speed
    if s["finished"]:
        return
    s["finished"] = True
    if s["correct"] > ss.prog["best_speed"]:
        ss.prog["best_speed"] = s["correct"]
        s["new_best"] = s["correct"] > 0
    ss.prog["resume"] = None
    save_progress()


@st.fragment(run_every=1)
def speed_timer():
    s = st.session_state.speed
    if s["finished"]:
        return
    left = SPEED_SECONDS - (time.time() - s["start"])
    if left <= 0:
        finish_speed()
        st.rerun()
    pct = max(0, min(100, left / SPEED_SECONDS * 100))
    cls = "low" if left <= 10 else ""
    st.markdown(f'<div class="timer">⚡ {int(math.ceil(left))}s &nbsp; ✅ {s["correct"]}/{s["attempted"]}</div>'
                f'<div class="tbar {cls}"><div style="width:{pct:.0f}%"></div></div>', unsafe_allow_html=True)


def page_speed_setup():
    st.button("🏠 Home", key="home_ss", on_click=go_home)
    st.markdown("## ⚡ Speed Test")
    st.write(f"{SPEED_SECONDS} second me jitne sahi kar sako! Best score: **{st.session_state.prog['best_speed']}**")
    opts = ["mixed"] + list(TOPICS)
    st.selectbox("Topic chuno", opts, key="w_speed_topic",
                 format_func=lambda k: "🎲 Mixed (sab topics)" if k == "mixed" else f"{TOPICS[k][0]} {TOPICS[k][1]}")
    st.button("▶️ Start", key="speed_go", type="primary", on_click=start_speed_from_widget)


def page_speed():
    ss = st.session_state
    s = ss.speed
    if not s:
        go_home()
        st.rerun()
    st.button("🏠 Home", key="home_sp", on_click=go_home)
    if s["finished"]:
        acc = s["correct"] * 100 // s["attempted"] if s["attempted"] else 0
        avg = SPEED_SECONDS / s["attempted"] if s["attempted"] else 0
        badge = "🏆 Naya best score!" if s["new_best"] else f"Best: {ss.prog['best_speed']}"
        st.markdown(f'<div class="res ok pop">⚡ Result<span>{s["correct"]} sahi / {s["attempted"]} attempt</span>'
                    f'<span>Accuracy {acc}% • {avg:.1f}s per question</span><span>{badge}</span></div>',
                    unsafe_allow_html=True)
        if s["new_best"] and not s.get("fx"):
            s["fx"] = True
            st.balloons()
            play_sound("ok")
        st.button("🔁 Dobara khelo", key="speed_again", type="primary", on_click=start_speed, args=(s["topic"],))
        return

    q = ss.q
    speed_timer()
    if s["last"]:
        L = s["last"]
        if L["ok"]:
            st.markdown('<div class="mini ok">✅ Sahi!</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="mini bad">❌ Galat - sahi answer: {L["ans"]}</div>', unsafe_allow_html=True)
        if not L["fx"]:
            L["fx"] = True
            play_sound("ok" if L["ok"] else "bad")
    show_question(q)
    submitted, raw = answer_form(q, "speed")
    if submitted:
        if time.time() - s["start"] >= SPEED_SECONDS + 0.5:
            finish_speed()
            st.rerun()
        val, err = parse_input(q, raw)
        if err:
            st.warning(err)
        else:
            verdict = judge(q, val)
            if verdict == "unsimplified":
                st.warning("Simplest form me likho (jaise 1/2) ✍️")
            else:
                ok = verdict == "ok"
                register_result(q, ok, time.time() - ss.q_start)
                s["attempted"] += 1
                s["correct"] += int(ok)
                s["last"] = {"ok": ok, "ans": q["ans_text"], "fx": False}
                new_question()
                st.rerun()
    autofocus("input")


# ---------------------------- STATS ----------------------------
def page_stats():
    prog = st.session_state.prog
    st.button("🏠 Home", key="home_st", on_click=go_home)
    st.markdown("## 📊 Stats")
    total, correct, acc = overall()
    tiles([(total, "Total questions"), (f"{acc}%", "Accuracy")])
    tiles([(f"🔥 {prog['best_streak']}", "Best streak (lagatar sahi)"), (f"📅 {daily_streak()}", "Din streak"),
           (f"⚡ {prog['best_speed']}", "Best speed")])

    st.markdown("#### Last 7 din")
    days = [(datetime.now(IST) - timedelta(days=i)).date() for i in range(6, -1, -1)]
    df = pd.DataFrame({"Total": [prog["daily"].get(d.isoformat(), {}).get("total", 0) for d in days],
                       "Sahi": [prog["daily"].get(d.isoformat(), {}).get("correct", 0) for d in days]},
                      index=pd.to_datetime(days))
    st.bar_chart(df, color=["#94a3b8", "#22c55e"])

    st.markdown("#### Topic-wise (weak topic tracking)")
    weak, weak_acc = None, 101
    for key in TOPICS:
        tp = prog["topics"][key]
        if tp["total"] >= 3 and tp["correct"] * 100 / tp["total"] < weak_acc:
            weak, weak_acc = key, tp["correct"] * 100 / tp["total"]
    for key, (icon, name, _) in TOPICS.items():
        tp = prog["topics"][key]
        if tp["total"]:
            a = f'{tp["correct"] * 100 / tp["total"]:.0f}%'
            avg = f'{tp["time"] / tp["total"]:.1f}s/q'
        else:
            a, avg = "-", "-"
        flag = " ⚠️ Sabse kamzor" if key == weak else ""
        cls = "trow weak" if key == weak else "trow"
        st.markdown(f'<div class="{cls}"><b>{icon} {name}{flag}</b>'
                    f'<span>{a} • {avg} • {tp["total"]} Q</span></div>', unsafe_allow_html=True)
    if weak is None:
        st.caption("Weak topic dekhne ke liye kisi topic me kam se kam 3 questions karo.")


# ---------------------------- LEARNING CHART ----------------------------
FRAC_LIST = [("1/2", "50%"), ("1/3", "33.33%"), ("2/3", "66.67%"), ("1/4", "25%"), ("3/4", "75%"),
             ("1/5", "20%"), ("2/5", "40%"), ("3/5", "60%"), ("4/5", "80%"), ("1/6", "16.67%"),
             ("5/6", "83.33%"), ("1/8", "12.5%"), ("3/8", "37.5%"), ("5/8", "62.5%"), ("7/8", "87.5%"),
             ("1/10", "10%"), ("1/12", "8.33%"), ("1/16", "6.25%"), ("1/20", "5%"), ("1/25", "4%"),
             ("1/40", "2.5%"), ("1/50", "2%")]


def page_chart():
    st.button("🏠 Home", key="home_ch", on_click=go_home)
    st.markdown("## 📚 Learning Mode")
    tabs = st.tabs(["🔢 Table", "⬜ Square", "🧊 Cube", "➗ Frac/%"])
    with tabs[0]:
        n = st.selectbox("Kaun si table?", list(range(1, 31)), index=1, key="w_tbl")
        html_table(["Table", "Answer"], [(f"{n} x {i}", n * i) for i in range(1, 11)])
    with tabs[1]:
        html_table(["n", "n²"], [(i, i * i) for i in range(1, 31)])
    with tabs[2]:
        html_table(["n", "n³"], [(i, i ** 3) for i in range(1, 31)])
    with tabs[3]:
        html_table(["Fraction", "Percentage"], FRAC_LIST)


# =====================================================================
# MAIN
# =====================================================================
def init_state():
    ss = st.session_state
    if "prog" in ss:
        return
    ss.path = progress_path()
    ss.prog = load_progress(ss.path)
    ss.update(page="home", mode="topic", topic="table", q=None, q_start=time.time(), answered=False,
              result=None, qid=0, last_text=None, speed=None, confirm_reset=False, save_error=False)
    r = ss.prog.get("resume")          # refresh ke baad wahi question wapas
    if (isinstance(r, dict) and isinstance(r.get("q"), dict) and r.get("mode") in ("topic", "mixed", "mistakes")
            and all(k in r["q"] for k in ("topic", "text", "kind", "answer", "ans_text"))
            and r["q"]["topic"] in TOPICS):
        ss.page, ss.mode, ss.q = "quiz", r["mode"], r["q"]
        ss.topic = r.get("topic") if r.get("topic") in TOPICS else "table"
        ss.last_text = r["q"]["text"]
        ss.qid = 1


PAGES = {"home": page_home, "quiz": page_quiz, "speed_setup": page_speed_setup,
         "speed": page_speed, "stats": page_stats, "chart": page_chart}


def main():
    st.set_page_config(page_title="Math Practice", page_icon="🧮", layout="centered",
                       initial_sidebar_state="collapsed")
    inject_css()
    init_state()
    PAGES.get(st.session_state.page, page_home)()
    if st.session_state.get("save_error"):
        st.caption("⚠️ Progress file save nahi ho payi (disk read-only ho sakti hai).")


try:
    main()
except Exception:                       # app crash na ho - friendly message
    st.error("😕 Kuch gadbad ho gayi. Home par jaakar dobara try karo.")
    st.button("🏠 Home", key="err_home", on_click=go_home)
