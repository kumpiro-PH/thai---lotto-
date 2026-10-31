import streamlit as st
import pandas as pd
from datetime import datetime
from collections import Counter
from itertools import combinations

# ==========================================
# 1. PAGE CONFIG & CUSTOM CSS (Sky Blue Theme)
# ==========================================
st.set_page_config(
    page_title="THAI AI PROFESSIONAL v7.8 - 15 Formula Frequency",
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

VERSION = "THAI AI PROFESSIONAL v7.9 SMART FORMULA RANKING"

# ==========================================
# 2. DEFAULT HISTORY DATA & INITIALIZATION
# ==========================================
DEFAULT_HISTORY = [
    {"date": "16/03/2569", "day": "Monday", "first": "833009", "front3": ["501", "983"], "back3": ["439", "954"], "back2": "64"},
    {"date": "01/04/2569", "day": "Wednesday", "first": "292514", "front3": ["113", "406"], "back3": ["098", "851"], "back2": "47"},
    {"date": "16/04/2569", "day": "Thursday", "first": "309612", "front3": ["108", "355"], "back3": ["424", "868"], "back2": "77"},
    {"date": "02/05/2569", "day": "Saturday", "first": "536077", "front3": ["267", "318"], "back3": ["065", "153"], "back2": "43"},
    {"date": "16/05/2569", "day": "Saturday", "first": "107387", "front3": ["091", "298"], "back3": ["602", "716"], "back2": "08"},
    {"date": "01/06/2569", "day": "Monday", "first": "173770", "front3": ["415", "848"], "back3": ["410", "938"], "back2": "95"},
    {"date": "16/06/2569", "day": "Tuesday", "first": "287184", "front3": ["434", "758"], "back3": ["007", "721"], "back2": "48"},
    {"date": "01/07/2569", "day": "Wednesday", "first": "751495", "front3": ["001", "980"], "back3": ["304", "531"], "back2": "62"},
    {"date": "16/07/2569", "day": "Thursday", "first": "639214", "front3": ["683", "709"], "back3": ["427", "746"], "back2": "71"},
    {"date": "01/08/2569", "day": "Saturday", "first": "932479", "front3": ["413", "672"], "back3": ["039", "154"], "back2": "69"},
    {"date": "16/08/2569", "day": "Sunday", "first": "004615", "front3": ["429", "731"], "back3": ["094", "937"], "back2": "53"},
    {"date": "01/09/2569", "day": "Tuesday", "first": "417212", "front3": ["257", "346"], "back3": ["136", "740"], "back2": "04"},
    {"date": "16/09/2569", "day": "Wednesday", "first": "730640", "front3": ["060", "521"], "back3": ["041", "266"], "back2": "64"},
    {"date": "01/10/2569", "day": "Thursday", "first": "402701", "front3": ["791", "912"], "back3": ["058", "396"], "back2": "70"},
    {"date": "16/10/2569", "day": "Friday", "first": "011781", "front3": ["392", "402"], "back3": ["171", "255"], "back2": "48"}
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
    "Thursday": "5078136", "Friday": "9627401", "Saturday": "8413657", "Sunday": "0426759",
}

# ==========================================
# 3. HELPER FUNCTIONS & FORMULAS
# ==========================================
def safe_int(value, default=0):
    try: return int(value)
    except: return default

def safe_digits(value):
    return "".join(ch for ch in str(value) if ch.isdigit())

def format_result(value, mode="back3"):
    value = safe_digits(value)
    if mode == "first": return value.zfill(6)[-6:]
    if mode in ("front3", "back3"): return value.zfill(3)[-3:]
    if mode == "back2": return value.zfill(2)[-2:]
    return value

def get_target_digits(target, mode="back3"):
    target = safe_digits(target).zfill(6)
    if mode == "first": return target
    if mode == "front3": return target[:3]
    if mode == "back3": return target[-3:]
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

# สูตรคำนวณทั้งหมด 16 สูตร
def formula_cross_multiply(number, mode="back3", daily_number="-"):
    target = get_target_digits(number, "first")[-4:]
    d1, d2 = safe_int(target[0]), safe_int(target[1])
    return format_result(f"{(d1 * d2 + 7) % 10}{(d1 + d2 + 3) % 10}", mode)

def formula1(target, mode="back3", daily_number="-"):
    digits = get_target_digits(target, "first")
    total_sum = sum(safe_int(x) for x in digits)
    return format_result((total_sum * 17 + safe_int(digits[-1]) * 23) % 1000, mode)

def formula2(number, mode="back3", daily_number="-"):
    a, b, c, d, e, f = map(safe_int, get_target_digits(number, "first"))
    return format_result((a * b) + (c * d) + (e * f), mode)

def formula3(number, mode="back3", daily_number="-"):
    return format_result(sum(map(safe_int, get_target_digits(number, "first"))) * 111, mode)

def formula4(number, mode="back3", daily_number="-"):
    digits = list(map(safe_int, get_target_digits(number, "first")))
    value = sum(digits[:3]) * sum(digits[3:])
    return formula5(number, mode, daily_number) if value == 0 else format_result(value, mode)

def formula5(number, mode="back3", daily_number="-"):
    digits = [safe_int(x) for x in get_target_digits(number, "first")]
    score = Counter({x: c * 5 for x, c in Counter(digits).items()})
    for i in range(len(digits) - 1):
        score[(digits[i] + digits[i + 1]) % 10] += 2
        score[(digits[i] * digits[i + 1]) % 10] += 2
        score[abs(digits[i] - digits[i + 1])] += 1
    ranking = sorted(score.items(), key=lambda x: (-x[1], x[0]))
    length = {"first": 6, "front3": 3, "back3": 3, "back2": 2}.get(mode, 4)
    return "".join(str(d) for d, _ in ranking[:length]).zfill(length)

def formula6(number, mode="back3", daily_number="-"):
    d = list(map(safe_int, get_target_digits(number, "first")))
    return format_result((d[0] + d[2] + d[4]) * (d[1] + d[3] + d[5]), mode)

def formula7(number, mode="back3", daily_number="-"):
    d = list(map(safe_int, get_target_digits(number, "first")))
    return format_result((d[0] * 10 + d[1]) + (d[4] * 10 + d[5]), mode)

def formula8(number, mode="back3", daily_number="-"):
    return format_result(sum(map(safe_int, get_target_digits(number, "first"))) * 123, mode)

def formula9(number, mode="back3", daily_number="-"):
    d = list(map(safe_int, get_target_digits(number, "first")))
    return format_result(abs((d[0] * 100 + d[1] * 10 + d[2]) - (d[3] * 100 + d[4] * 10 + d[5])), mode)

def formula10(number, mode="back3", daily_number="-"):
    d = list(map(safe_int, get_target_digits(number, "first")))
    return format_result((d[0] * d[5]) + (d[1] * d[4]) + (d[2] * d[3]), mode)

def formula11(number, mode="back3", daily_number="-"):
    d = [safe_int(x) for x in get_target_digits(number, "first")]
    return format_result((d[0] * d[1] + d[4] * d[5]) % 1000, mode)

def formula12(number, mode="back3", daily_number="-"):
    d = [safe_int(x) for x in get_target_digits(number, "first")]
    b = (d[3] + d[4]) % 10
    return format_result(int(f"{b}{(b + 1) % 10}{(b + 2) % 10}{(b + 3) % 10}"), mode)

def formula13(number, mode="back3", daily_number="-"):
    d = [safe_int(x) for x in get_target_digits(number, "first")]
    return format_result((d[0] + d[2] + d[5]) * 9, mode)

def formula14(number, mode="back3", daily_number="-"):
    first_digits = get_target_digits(number, "first")
    f = safe_int(first_digits[5]) if len(first_digits) >= 6 else 0
    return format_result(int(f"{f}{f}{(f + 1) % 10}{(f + 1) % 10}"), mode)

def formula_neighbor(number, mode="back3", daily_number="-"):
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
    """
    Apply the daily-number blend to all six base digits, then pass the FULL
    six-digit value to the formula. The formula itself selects/formats the
    requested output (first/front3/back3/back2).
    """
    target = safe_digits(target).zfill(6)[-6:]
    length = {"first": 6, "front3": 3, "back3": 3, "back2": 2}.get(mode, 3)

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


# ==========================================
# 3.1 ALL 15 FORMULAS: RESULT + DIGIT FREQUENCY
# ==========================================
# The 15-formula set intentionally excludes Cross Multiply.
FORMULAS_15 = [(name, func) for name, func in formulas if name != "Cross Multiply"]


def analyse_all_15_formulas(target_number, daily_number="-", mode="back3"):
    """
    Calculate the same 15 formulas shown in the report, then count only their
    blended outputs. Echo Core and Hybrid Pool are deliberately excluded.
    """
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

    # Include every digit 0-9, even when its frequency is zero.
    raw_counts = Counter(combined_digits)
    counts = {str(digit): raw_counts.get(str(digit), 0) for digit in range(10)}

    # Sort by frequency descending; ties are resolved by digit ascending.
    frequency = sorted(counts.items(), key=lambda item: (-item[1], int(item[0])))
    return rows, frequency, len(combined_digits)


def _best_back3_hit(prediction, actual_values):
    """Best unordered digit overlap against either official back3 result."""
    pred = safe_digits(prediction)
    if not pred or not actual_values:
        return 0
    best = 0
    for actual in actual_values:
        actual = safe_digits(actual)
        hit = sum((Counter(pred) & Counter(actual)).values())
        best = max(best, hit)
    return best


def analyse_smart_formula_ranking(target_number, daily_number="-", history_data=None, mode="back3"):
    """
    Rank the 15 formulas using walk-forward historical accuracy.
    Formula definitions and dynamic_formula_wrapper are left unchanged.
    Historical target uses the next draw's official back3 results when present.
    """
    history_data = history_data or []
    performance = []
    formula_weights = {}

    # Evaluate only transitions where a next draw exists.
    for name, func in FORMULAS_15:
        total_hits = 0
        total_possible = 0
        valid_draws = 0

        for index in range(len(history_data) - 1):
            previous = history_data[index]
            following = history_data[index + 1]

            actual_values = following.get("back3", [])
            if isinstance(actual_values, str):
                actual_values = actual_values.split()
            actual_values = [safe_digits(x) for x in actual_values if safe_digits(x)]

            # If official back3 data is absent, fall back to the last 3 digits
            # of the next first-prize number, and label this limitation in UI.
            if not actual_values:
                first_value = safe_digits(following.get("first", ""))
                if len(first_value) >= 3:
                    actual_values = [first_value[-3:]]

            if not actual_values:
                continue

            next_day = following.get("day", "")
            historical_daily = DAILY_NUMBERS.get(next_day, "-")
            prediction = dynamic_formula_wrapper(
                func, previous.get("first", ""), "back3", historical_daily
            )
            total_hits += _best_back3_hit(prediction, actual_values)
            total_possible += 3
            valid_draws += 1

        # Smoothed weight prevents a tiny history from assigning zero weight.
        accuracy = (total_hits / total_possible) if total_possible else 0.0
        weight = 0.50 + accuracy
        formula_weights[name] = weight
        performance.append({
            "สูตร": name,
            "จำนวนงวดทดสอบ": valid_draws,
            "เลขตรงสะสม": total_hits,
            "โอกาสเทียบทั้งหมด": total_possible,
            "ความแม่นยำ (%)": round(accuracy * 100, 2),
            "น้ำหนัก": round(weight, 4),
        })

    # Calculate current outputs using the existing formula wrapper.
    current_outputs = {}
    for name, func in FORMULAS_15:
        current_outputs[name] = dynamic_formula_wrapper(
            func, target_number, "back3", daily_number
        )

    # When several formulas return the same 3-digit output, divide their
    # combined contribution so duplicate outputs do not dominate the ranking.
    output_groups = Counter(current_outputs.values())
    weighted_scores = {str(d): 0.0 for d in range(10)}
    raw_counts = Counter()

    for name, output in current_outputs.items():
        weight = formula_weights.get(name, 0.50)
        contribution = weight / max(1, output_groups[output])
        for digit in safe_digits(output):
            raw_counts[digit] += 1
            weighted_scores[digit] += contribution

    weighted_ranking = sorted(
        weighted_scores.items(),
        key=lambda item: (-item[1], -raw_counts[item[0]], int(item[0]))
    )
    performance.sort(
        key=lambda row: (-row["ความแม่นยำ (%)"], -row["เลขตรงสะสม"], row["สูตร"])
    )
    return current_outputs, performance, weighted_ranking, raw_counts

def get_echo_core(history_data):
    if not history_data: return ["0", "1", "2", "3", "4"]
    pool = []
    for rec in history_data[-5:]:
        pool.extend(list(safe_digits(rec.get("first", ""))))
        pool.extend(list(safe_digits(rec.get("back2", ""))))
    return [d for d, _ in Counter(pool).most_common(5)]

def analyse_formulas(mode="back3", target_number=None, daily_number="-"):
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
            if isinstance(nxt, list): nxt = nxt[0] if nxt else ""
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
        default_target = st.session_state.history[-1]["first"] if st.session_state.history else "723294"
        target_number = st.text_input("📌 เลขฐาน 6 หลักงวดล่าสุด:", value=default_target, max_chars=6)
    with col2:
        day_choice = st.selectbox("📅 เลือกวันประจำงวด:", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "ไม่ใช้ (Manual)"])
        daily_number = DAILY_NUMBERS.get(day_choice, "-")

    if st.button("🚀 ประมวลผล Master Report", type="primary", use_container_width=True):
        if len(target_number) != 6 or not target_number.isdigit():
            st.error("❌ กรุณากรอกเลขฐาน 6 หลักให้ถูกต้อง")
        else:
            analysis = {m: analyse_formulas(m, target_number, daily_number) for m in ["first", "front3", "back3", "back2"]}
            
            # การคำนวณแบบผสมวัน vs ดิบ
            f1_res = dynamic_formula_wrapper(FORMULA_MAP["Formula 1"], target_number, "back3", daily_number)
            f1_raw = dynamic_formula_wrapper(FORMULA_MAP["Formula 1"], target_number, "back3", "-")
            f2_res = dynamic_formula_wrapper(FORMULA_MAP["Formula 2"], target_number, "back3", daily_number)
            f2_raw = dynamic_formula_wrapper(FORMULA_MAP["Formula 2"], target_number, "back3", "-")
            cross_res = dynamic_formula_wrapper(FORMULA_MAP["Cross Multiply"], target_number, "back3", daily_number)
            cross_raw = dynamic_formula_wrapper(FORMULA_MAP["Cross Multiply"], target_number, "back3", "-")

            st.markdown("### 📊 เปรียบเทียบผลลัพธ์สูตรเด่น (สถิติดิบ vs ผสมวัน)")
            comp_data = [
                {"สูตร": "Formula 1 (ผันแปร)", "สถิติดิบ": f1_raw, "ผสมวัน": f1_res, "เด่น 2 ตัว": f1_res[-2:]},
                {"สูตร": "Formula 2 (คูณคู่)", "สถิติดิบ": f2_raw, "ผสมวัน": f2_res, "เด่น 2 ตัว": f2_res[-2:]},
                {"สูตร": "Cross Multiply (คูณไขว้)", "สถิติดิบ": cross_raw, "ผสมวัน": cross_res, "เด่น 2 ตัว": cross_res[-2:]},
            ]
            st.table(pd.DataFrame(comp_data))

            # --------------------------------------------------
            # Full 15-formula report + combined digit frequency
            # --------------------------------------------------
            st.markdown("### 🧮 ผลลัพธ์ครบ 15 สูตร (ไม่รวม Cross Multiply)")
            formula_rows, digit_frequency, digit_total = analyse_all_15_formulas(
                target_number, daily_number, mode="back3"
            )
            st.dataframe(
                pd.DataFrame(formula_rows),
                use_container_width=True,
                hide_index=True
            )

            st.markdown("### 🔢 ความถี่เลขจากผลลัพธ์ 15 สูตรเท่านั้น")
            st.caption(
                "นับจากเลขผสมวัน Back3 ของ Formula 1–14 และ Formula Neighbor "
                "รวม 15 สูตร × 3 หลัก = 45 หลัก โดยไม่รวม Echo Core, Hybrid Pool "
                "หรือ Cross Multiply"
            )
            freq_df = pd.DataFrame(
                [{"เลข": digit, "จำนวนครั้ง": count} for digit, count in digit_frequency]
            )
            st.dataframe(freq_df, use_container_width=True, hide_index=True)

            # Back3 must contain exactly 45 counted digits (15 formulas × 3 digits).
            if digit_total != 45:
                st.warning(
                    f"ตรวจพบจำนวนหลักรวม {digit_total} หลัก แต่ควรเป็น 45 หลัก "
                    "กรุณาตรวจสอบความยาวผลลัพธ์ของสูตร"
                )

            top_digits = [digit for digit, _ in digit_frequency]
            top5_digits = top_digits[:5]
            top3_digits = top_digits[:3]

            st.markdown(
                f"""
                <div class="report-card">
                    <div class="report-title">🏆 สรุปความถี่จาก 15 สูตร รวม {digit_total} หลัก</div>
                    <p><b>เรียงเลขตามความถี่มากไปน้อย:</b>
                    <span style="color:#0284c7;font-size:22px;font-weight:800;">
                    {' - '.join(top_digits)}</span></p>
                    <p><b>เลขเด่น 5 ตัว:</b>
                    <span style="color:#0369a1;font-size:20px;font-weight:800;">
                    {' - '.join(top5_digits)}</span></p>
                    <p><b>เลขเด่น 3 ตัว:</b>
                    <span style="color:#0369a1;font-size:20px;font-weight:800;">
                    {' - '.join(top3_digits)}</span></p>
                </div>
                """,
                unsafe_allow_html=True,
            )


            # --------------------------------------------------
            # Smart Formula Ranking (historical accuracy-weighted)
            # --------------------------------------------------
            st.markdown("### 🧠 Smart Formula Ranking — จัดอันดับด้วยผลย้อนหลัง")
            st.caption(
                "คงสูตรเดิมทั้ง 15 สูตรและวิธีผสมวันเดิม "
                "เพิ่มน้ำหนักตามการทดสอบย้อนหลังแบบเดินหน้า "
                "และหารน้ำหนักเมื่อหลายสูตรให้ผล 3 หลักซ้ำกัน"
            )

            smart_outputs, formula_performance, smart_frequency, smart_raw_counts = (
                analyse_smart_formula_ranking(
                    target_number,
                    daily_number,
                    st.session_state.history,
                    mode="back3"
                )
            )

            st.markdown("#### 🏅 ผล Backtest แยกตามสูตร")
            st.dataframe(
                pd.DataFrame(formula_performance),
                use_container_width=True,
                hide_index=True
            )

            st.markdown("#### 🔢 เปรียบเทียบความถี่เดิมกับ Smart Ranking")
            smart_df = pd.DataFrame([
                {
                    "เลข": digit,
                    "ความถี่เดิม": smart_raw_counts.get(digit, 0),
                    "คะแนนถ่วงน้ำหนัก": round(score, 3),
                    "อันดับ Smart": rank
                }
                for rank, (digit, score) in enumerate(smart_frequency, 1)
            ])
            st.dataframe(smart_df, use_container_width=True, hide_index=True)

            smart_digits = [digit for digit, _ in smart_frequency]
            st.markdown(
                f"""
                <div class="report-card">
                    <div class="report-title">🧠 สรุป Smart Ranking</div>
                    <p><b>เรียงอันดับ:</b>
                    <span style="color:#0284c7;font-size:22px;font-weight:800;">
                    {' - '.join(smart_digits)}</span></p>
                    <p><b>Smart Top 5:</b>
                    <span style="color:#0369a1;font-size:20px;font-weight:800;">
                    {' - '.join(smart_digits[:5])}</span></p>
                    <p><b>Smart Top 3:</b>
                    <span style="color:#0369a1;font-size:20px;font-weight:800;">
                    {' - '.join(smart_digits[:3])}</span></p>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.info(
                "หมายเหตุ: Backtest ใช้เลขท้าย 3 ตัวของผลสูตรเทียบกับเลขท้าย 3 ตัว "
                "ที่บันทึกในช่อง back3 ของงวดถัดไป (ถ้าไม่มีข้อมูลจึงใช้ 3 ตัวท้ายรางวัลที่ 1) "
                "ผลคะแนนเป็นสถิติย้อนหลัง ไม่ใช่การรับประกันผลรางวัล"
            )

            # Echo Core / Hybrid Pool are separate history-based modules.
            # They are intentionally NOT merged into the 15-formula frequency count.
            st.markdown("### 📚 ระบบสถิติย้อนหลัง (แยกจากความถี่ 15 สูตร)")
            st.caption(
                "Echo Core และ Hybrid Pool คำนวณจากประวัติย้อนหลัง/เลขฐาน "
                "จึงแสดงแยกต่างหาก และไม่ถูกนำไปเพิ่มจำนวนครั้งในตารางความถี่ 15 สูตร"
            )
            # สรุป Super Core & 2D Pairings
            echo_core = get_echo_core(st.session_state.history)
            top_5_digits = " - ".join(echo_core[:5])
            super_core = sorted(list(set(echo_core) & set(list(target_number[:3]))))
            pairs = [f"{a}{b}" for a, b in combinations(echo_core, 2)]
            combined_6_pool = list(dict.fromkeys(list(target_number) + echo_core))
            top_6_digits = " - ".join(combined_6_pool[:6]) if len(combined_6_pool) >= 6 else "0 - 1 - 2 - 4 - 6 - 7"

            st.markdown(f"""
            <div class="report-card">
                <div class="report-title">🎯 ชุดเลขเด่น 5–6 ตัวเน้นๆ (แนะนำสำหรับการลงทุน)</div>
                <p><b>⭐ ชุดเลขเด่น 5 ตัว (Echo Core):</b> <span style="color: #0284c7; font-size: 18px; font-weight: bold;">{top_5_digits}</span></p>
                <p><b>🌟 ชุดเลขเด่น 6 ตัว (Hybrid Pool):</b> <span style="color: #0369a1; font-size: 18px; font-weight: bold;">{top_6_digits}</span></p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="report-card">
                <div class="report-title">🔥 เลขชนสุดยอด (SUPER CORE) & ชุดวิควิค 2 ตัว</div>
                <p><b>เลขไหลสะสม (Echo Core):</b> {' - '.join(echo_core)}</p>
                <p><b>เลขชนสุดยอด (Super Core):</b> {' - '.join(super_core) if super_core else 'ไม่มีเลขชน'}</p>
                <div><b>ชุดวิน 2 ตัวเด็ด:</b> {" ".join([f'<span class="badge-core">{p}</span>' for p in pairs])}</div>
            </div>
            """, unsafe_allow_html=True)

# ==========================================
# 6. MANAGEMENT HISTORY PAGE
# ==========================================
elif menu == "1. เพิ่ม/จัดการประวัติหวย":
    st.title("📚 เพิ่ม / จัดการประวัติหวย")
    
    with st.form("add_history_form"):
        st.subheader("➕ เพิ่มรางวัลงวดใหม่")
        col_a, col_b, col_c = st.columns(3)
        date_in = col_a.text_input("งวดวันที่ (เช่น 16 พ.ย. 2569)")
        day_in = col_b.selectbox("วัน", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        first_in = col_c.text_input("รางวัลที่ 1 (6 หลัก)")
        
        col_d, col_e, col_f = st.columns(3)
        f3_in = col_d.text_input("หน้า 3 ตัว (เว้นวรรค)")
        b3_in = col_e.text_input("ท้าย 3 ตัว (เว้นวรรค)")
        b2_in = col_f.text_input("ท้าย 2 ตัว (2 หลัก)")
        
        submitted = st.form_submit_button("บันทึกข้อมูล")
        if submitted:
            if len(first_in) == 6 and first_in.isdigit():
                st.session_state.history.append({
                    "date": date_in, "day": day_in, "first": first_in,
                    "front3": f3_in.split(), "back3": b3_in.split(), "back2": b2_in
                })
                st.success("✅ บันทึกข้อมูลสำเร็จ!")
            else:
                st.error("❌ รางวัลที่ 1 ต้องเป็นตัวเลข 6 หลักเท่านั้น")

    st.subheader("📋 ประวัติสลากย้อนหลังในระบบ")
    st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True)

# ==========================================
# 7. BACKTEST PAGE
# ==========================================
elif menu == "10. รันระบบทดสอบย้อนหลัง (Backtest)":
    st.title("📈 รันระบบทดสอบย้อนหลัง (Backtest Engine)")
    
    if len(st.session_state.history) < 2:
        st.warning("⚠️ ต้องการข้อมูลอย่างน้อย 2 งวดขึ้นไปในการทำ Backtest")
    else:
        st.info(f"ประมวลผลจากประวัติสะสมทั้งหมด {len(st.session_state.history)} งวด")
        
        res_b2 = analyse_formulas("back2")
        st.subheader("🏆 Top 3 สูตรเจาะตำแหน่ง: เลขท้าย 2 ตัว (Back 2)")
        for rank, item in enumerate(res_b2[:3], 1):
            st.write(f"**อันดับ {rank}: {item[3]}** | คะแนนคูณน้ำหนัก: {item[0]:.2f} | ความแม่นยำรวม: {item[2]:.2f}%")

# ==========================================
# 8. SETTINGS PAGE
# ==========================================
elif menu == "9. ตั้งค่าน้ำหนัก AI (Settings)":
    st.title("⚙️ ตั้งค่าน้ำหนัก AI (Weight Settings)")
    
    w_f = st.slider("Formula Weight", 0.1, 2.0, st.session_state.ai_settings["formula_weight"])
    w_c = st.slider("Cross Weight", 0.1, 2.0, st.session_state.ai_settings["cross_weight"])
    
    if st.button("บันทึกค่าน้ำหนัก"):
        st.session_state.ai_settings["formula_weight"] = w_f
        st.session_state.ai_settings["cross_weight"] = w_c
        st.success("✅ บันทึกค่าน้ำหนักใหม่เรียบร้อย!")
