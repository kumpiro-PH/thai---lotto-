import streamlit as st
import pandas as pd
from datetime import datetime
from collections import Counter
from itertools import combinations

# ==========================================
# 1. PAGE CONFIG & CUSTOM CSS (Sky Blue Theme)
# ==========================================
st.set_page_config(
    page_title="THAI AI PROFESSIONAL v7.8",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .report-card {
        background-color: #f0f9ff;
        border-left: 5px solid #0284c7;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
    }
    .report-title {
        font-weight: 700;
        color: #0369a1;
        font-size: 16px;
        margin-bottom: 10px;
    }
    .badge-core {
        background-color: #0284c7;
        color: white;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 700;
        display: inline-block;
        margin: 2px;
    }
</style>
""", unsafe_allow_html=True)

VERSION = "THAI AI PROFESSIONAL v7.8 MASTER AI - 2D & Prize 1 Only"

# ==========================================
# 2. DEFAULT HISTORY DATA & INITIALIZATION
# ==========================================
DEFAULT_HISTORY = [
    {"date": "16/03/2569", "day": "Monday", "first": "833009", "back2": "64"},
    {"date": "01/04/2569", "day": "Wednesday", "first": "292514", "back2": "47"},
    {"date": "16/04/2569", "day": "Thursday", "first": "309612", "back2": "77"},
    {"date": "02/05/2569", "day": "Saturday", "first": "536077", "back2": "43"},
    {"date": "16/05/2569", "day": "Saturday", "first": "107387", "back2": "08"},
    {"date": "01/06/2569", "day": "Monday", "first": "173770", "back2": "95"},
    {"date": "16/06/2569", "day": "Tuesday", "first": "287184", "back2": "48"},
    {"date": "01/07/2569", "day": "Wednesday", "first": "751495", "back2": "62"},
    {"date": "16/07/2569", "day": "Thursday", "first": "639214", "back2": "71"},
    {"date": "01/08/2569", "day": "Saturday", "first": "932479", "back2": "69"},
    {"date": "16/08/2569", "day": "Sunday", "first": "004615", "back2": "53"},
    {"date": "01/09/2569", "day": "Tuesday", "first": "417212", "back2": "04"},
    {"date": "16/09/2569", "day": "Wednesday", "first": "730640", "back2": "64"},
    {"date": "01/10/2569", "day": "Thursday", "first": "402701", "back2": "70"},
    {"date": "16/10/2569", "day": "Friday", "first": "011781", "back2": "48"}
]

if "history" not in st.session_state:
    st.session_state.history = DEFAULT_HISTORY

if "ai_settings" not in st.session_state:
    st.session_state.ai_settings = {
        "formula_weight": 1.00,
        "cross_weight": 0.90,
        "daily_weight": 1.50,
        "echo_weight": 0.70,
        "recovery_weight": 0.60,
    }

DAILY_NUMBERS = {
    "Monday": "6185270", "Tuesday": "7306481", "Wednesday": "6845902",
    "Thursday": "5078136", "Friday": "9627401", "Saturday": "8413657", "Sunday": "2956814",
}

# ==========================================
# 3. HELPER FUNCTIONS & FORMULAS
# ==========================================
def safe_int(value, default=0):
    try: return int(value)
    except: return default

def safe_digits(value):
    return "".join(ch for ch in str(value) if ch.isdigit())

def format_result(value, mode="back2"):
    value = safe_digits(value)
    if mode == "first": return value.zfill(6)[-6:]
    if mode == "back2": return value.zfill(2)[-2:]
    return value

def get_target_digits(target, mode="back2"):
    target = safe_digits(target).zfill(6)
    if mode == "first": return target
    if mode == "back2": return target[-2:]
    return target

def calculate_digit_accuracy(prediction, answer):
    p_counter, a_counter = Counter(safe_digits(prediction)), Counter(safe_digits(answer))
    hit = sum((p_counter & a_counter).values())
    max_digit = max(len(safe_digits(prediction)), len(safe_digits(answer)))
    accuracy = round((hit / max_digit) * 100) if max_digit else 0
    return hit, accuracy

def calculate_score(result, answer):
    hit, _ = calculate_digit_accuracy(result, answer)
    return min(hit * 25, 100)

# สูตรคำนวณทั้งหมด
def formula_cross_multiply(number, mode="back2", daily_number="-"):
    target = get_target_digits(number, "first")[-4:]
    d1, d2 = safe_int(target[0]), safe_int(target[1])
    return format_result(f"{(d1 * d2 + 7) % 10}{(d1 + d2 + 3) % 10}", mode)

def formula1(target, mode="back2", daily_number="-"):
    digits = get_target_digits(target, "first")
    total_sum = sum(safe_int(x) for x in digits)
    return format_result((total_sum * 17 + safe_int(digits[-1]) * 23) % 1000, mode)

def formula2(number, mode="back2", daily_number="-"):
    a, b, c, d, e, f = map(safe_int, get_target_digits(number, "first"))
    return format_result((a * b) + (c * d) + (e * f), mode)

def formula3(number, mode="back2", daily_number="-"):
    return format_result(sum(map(safe_int, get_target_digits(number, "first"))) * 111, mode)

def formula4(number, mode="back2", daily_number="-"):
    digits = list(map(safe_int, get_target_digits(number, "first")))
    value = sum(digits[:3]) * sum(digits[3:])
    return formula5(number, mode, daily_number) if value == 0 else format_result(value, mode)

def formula5(number, mode="back2", daily_number="-"):
    digits = [safe_int(x) for x in get_target_digits(number, "first")]
    score = Counter({x: c * 5 for x, c in Counter(digits).items()})
    for i in range(len(digits) - 1):
        score[(digits[i] + digits[i + 1]) % 10] += 2
        score[(digits[i] * digits[i + 1]) % 10] += 2
        score[abs(digits[i] - digits[i + 1])] += 1
    ranking = sorted(score.items(), key=lambda x: (-x[1], x[0]))
    length = {"first": 6, "back2": 2}.get(mode, 2)
    return "".join(str(d) for d, _ in ranking[:length]).zfill(length)

def formula6(number, mode="back2", daily_number="-"):
    d = list(map(safe_int, get_target_digits(number, "first")))
    return format_result((d[0] + d[2] + d[4]) * (d[1] + d[3] + d[5]), mode)

def formula7(number, mode="back2", daily_number="-"):
    d = list(map(safe_int, get_target_digits(number, "first")))
    return format_result((d[0] * 10 + d[1]) + (d[4] * 10 + d[5]), mode)

def formula8(number, mode="back2", daily_number="-"):
    return format_result(sum(map(safe_int, get_target_digits(number, "first"))) * 123, mode)

def formula9(number, mode="back2", daily_number="-"):
    d = list(map(safe_int, get_target_digits(number, "first")))
    return format_result(abs((d[0] * 100 + d[1] * 10 + d[2]) - (d[3] * 100 + d[4] * 10 + d[5])), mode)

def formula10(number, mode="back2", daily_number="-"):
    d = list(map(safe_int, get_target_digits(number, "first")))
    return format_result((d[0] * d[5]) + (d[1] * d[4]) + (d[2] * d[3]), mode)

def formula11(number, mode="back2", daily_number="-"):
    d = [safe_int(x) for x in get_target_digits(number, "first")]
    return format_result((d[0] * d[1] + d[4] * d[5]) % 1000, mode)

def formula12(number, mode="back2", daily_number="-"):
    d = [safe_int(x) for x in get_target_digits(number, "first")]
    b = (d[3] + d[4]) % 10
    return format_result(int(f"{b}{(b + 1) % 10}{(b + 2) % 10}{(b + 3) % 10}"), mode)

def formula13(number, mode="back2", daily_number="-"):
    d = [safe_int(x) for x in get_target_digits(number, "first")]
    return format_result((d[0] + d[2] + d[5]) * 9, mode)

def formula14(number, mode="back2", daily_number="-"):
    first_digits = get_target_digits(number, "first")
    f = safe_int(first_digits[5]) if len(first_digits) >= 6 else 0
    return format_result(int(f"{f}{f}{(f + 1) % 10}{(f + 1) % 10}"), mode)

def formula_neighbor(number, mode="back2", daily_number="-"):
    d = [safe_int(x) for x in get_target_digits(number, "first")]
    rf = (d[5] - 1) % 10 if len(d) >= 6 else 0
    rb = (d[3] + 2) % 10 if len(d) >= 4 else 0
    return format_result(int(f"{rf}{rb}{(rb + 1) % 10}{(rb + 2) % 10}"), mode)

formulas = [
    ("Formula 1", formula1), ("Formula 2", formula2), ("Formula 3", formula3),
    ("Formula 4", formula4), ("Formula 5", formula5), ("Formula 6", formula6),
    ("Formula 7", formula7), ("Formula 8", formula8), ("Formula 9", formula9),
    ("Formula 10", formula10), ("Formula 11", formula11), ("Formula 12", formula12),
    ("Formula 13", formula13), ("Formula 14", formula14), ("Formula Neighbor", formula_neighbor),
    ("Cross Multiply", formula_cross_multiply)
]
FORMULA_MAP = dict(formulas)

def dynamic_formula_wrapper(func, target, mode, daily_number="-"):
    target = safe_digits(target).zfill(6)[-6:]
    length = {"first": 6, "back2": 2}.get(mode, 2)

    if daily_number and daily_number != "-":
        daily_digits = safe_digits(daily_number)
        if daily_digits:
            target = "".join(
                str((safe_int(target[i]) + safe_int(daily_digits[i % len(daily_digits)])) % 10)
                for i in range(6)
            )

    try:
        result = func(target, mode, daily_number)
    except TypeError:
        try:
            result = func(target, mode)
        except TypeError:
            result = func(target)

    return safe_digits(result).zfill(length)[-length:]

FORMULAS_15 = [(name, func) for name, func in formulas if name != "Cross Multiply"]

def analyse_all_15_formulas(target_number, daily_number="-", mode="back2"):
    rows = []
    combined_digits = []

    for name, func in FORMULAS_15:
        raw_result = dynamic_formula_wrapper(func, target_number, mode, "-")
        blended_result = dynamic_formula_wrapper(func, target_number, mode, daily_number)

        rows.append({
            "สูตร": name,
            "เลขดิบ": raw_result,
            "เลขผสมวัน": blended_result,
            "ท้าย 2 ตัว": blended_result[-2:],
        })
        combined_digits.extend(safe_digits(blended_result))

    raw_counts = Counter(combined_digits)
    counts = {str(digit): raw_counts.get(str(digit), 0) for digit in range(10)}

    frequency = sorted(counts.items(), key=lambda item: (-item[1], int(item[0])))
    return rows, frequency, len(combined_digits)

def get_echo_core(history_data):
    if not history_data: return ["0", "1", "2", "3", "4"]
    pool = []
    for rec in history_data[-5:]:
        pool.extend(list(safe_digits(rec.get("first", ""))))
        pool.extend(list(safe_digits(rec.get("back2", ""))))
    return [d for d, _ in Counter(pool).most_common(5)]

def analyse_formulas(mode="back2", target_number=None, daily_number="-"):
    results = []
    test_range = min(len(st.session_state.history) - 1, 70)
    target_history = st.session_state.history[-(test_range+1):] if test_range > 0 else st.session_state.history
    f_weight = st.session_state.ai_settings.get("formula_weight", 1.0)
    c_weight = st.session_state.ai_settings.get("cross_weight", 0.9)

    for name, func in formulas:
        classic_score, weighted_score, valid = 0, 0, 0
        current_weight = c_weight if name == "Cross Multiply" else f_weight
        for index in range(len(target_history) - 1):
            nxt = target_history[index + 1].get(mode, "")
            if not nxt: continue
            valid += 1
            pred = dynamic_formula_wrapper(func, target_history[index].get("first", ""), mode, daily_number)
            pt = calculate_score(pred, nxt)
            classic_score += pt
            weighted_score += (pt * (index + 1)) * current_weight
        percent = ((classic_score / (valid * 100)) * 100) if valid else 0
        results.append((weighted_score, classic_score, percent, name))
    return sorted(results, key=lambda x: (-x[0], -x[1], -x[2]))

# ==========================================
# 4. STREAMLIT UI SIDEBAR NAVIGATION
# ==========================================
st.sidebar.title("🧠 MENU CONTROL")
menu = st.sidebar.radio("เลือกหน้าเมนู:", [
    "8. All-in-One Master Report",
    "1. เพิ่ม/จัดการประวัติหวย",
    "10. รันระบบทดสอบย้อนหลัง (Backtest)",
    "9. ตั้งค่าน้ำหนัก AI (Settings)"
])

# ==========================================
# 5. ALL-IN-ONE MASTER REPORT (MAIN PAGE)
# ==========================================
if menu == "8. All-in-One Master Report":
    st.title("🏆 ALL-IN-ONE MASTER REPORT")
    st.caption(f"เวอร์ชัน: {VERSION}")
    
    col1, col2 = st.columns(2)
    with col1:
        default_target = st.session_state.history[-1]["first"] if st.session_state.history else "011781"
        target_number = st.text_input("📌 เลขฐาน 6 หลักงวดล่าสุด:", value=default_target, max_chars=6)
    with col2:
        day_choice = st.selectbox("📅 เลือกวันประจำงวด:", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "ไม่ใช้ (Manual)"])
        daily_number = DAILY_NUMBERS.get(day_choice
