import streamlit as st
import pandas as pd
import os
from datetime import datetime, date
from collections import Counter
from itertools import combinations, permutations

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

VERSION = "THAI AI PROFESSIONAL v7.8 MASTER AI - FIXED"

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

def parse_be_date(value):
    """Parse common Thai/Buddhist or Gregorian date strings for chronological sorting."""
    text = str(value or "").strip()
    if not text:
        return None
    parsed = None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%y"):
        try:
            parsed = datetime.strptime(text, fmt).date()
            break
        except ValueError:
            continue
    if parsed is None:
        try:
            parsed = pd.to_datetime(text, dayfirst=True, errors="coerce")
            if pd.isna(parsed):
                return None
            parsed = parsed.date()
        except Exception:
            return None
    if parsed.year >= 2400:
        parsed = parsed.replace(year=parsed.year - 543)
    return parsed


def normalize_history_row(row):
    """Normalize supported CSV columns into the app's internal history schema."""
    date_value = row.get("date", row.get("date_be", row.get("งวดหวยย้อนหลัง", "")))
    first_value = row.get("first", row.get("first_prize", row.get("รางวัลที่ 1", "")))
    back2_value = row.get("back2", row.get("last_2_digits", row.get("เลขท้าย 2 ตัว", "")))
    front_value = row.get("front3", row.get("front_3_digits", row.get("เลขหน้า 3 ตัว", "")))
    back_value = row.get("back3", row.get("back_3_digits", row.get("เลขท้าย 3 ตัว", "")))
    day_value = str(row.get("day", "") or "").strip()

    def to_list(value):
        if isinstance(value, list):
            raw_values = value
        else:
            raw_values = str(value or "").replace(",", " ").split()
        return [str(x).strip().zfill(3)[-3:] for x in raw_values if str(x).strip().isdigit()]

    first_digits = "".join(ch for ch in str(first_value) if ch.isdigit())
    if len(first_digits) != 6:
        return None
    first_digits = first_digits.zfill(6)[-6:]
    back2_digits = "".join(ch for ch in str(back2_value) if ch.isdigit())
    back2_digits = back2_digits.zfill(2)[-2:] if back2_digits else ""

    parsed_date = parse_be_date(date_value)
    valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    if day_value not in valid_days:
        day_value = valid_days[parsed_date.weekday()] if parsed_date else ""
    return {
        "date": str(date_value or "").strip(),
        "day": day_value,
        "first": first_digits,
        "front3": to_list(front_value),
        "back3": to_list(back_value),
        "back2": back2_digits,
        "_sort_date": parsed_date,
    }


def load_history_csv():
    """Load history_thai.csv beside this script; fall back to built-in sample history."""
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history_thai.csv")
    if not os.path.isfile(csv_path):
        return [dict(row) for row in DEFAULT_HISTORY], None, "ไม่พบไฟล์ history_thai.csv"
    try:
        frame = pd.read_csv(csv_path, dtype=str, encoding="utf-8-sig").fillna("")
        normalized = []
        for record in frame.to_dict(orient="records"):
            item = normalize_history_row(record)
            if item:
                normalized.append(item)
        if not normalized:
            return [dict(row) for row in DEFAULT_HISTORY], csv_path, "ไฟล์ CSV ไม่มีแถวข้อมูลที่มีรางวัลที่ 1 ครบ 6 หลัก"
        # Sort by real calendar date; preserve file order for rows without a parseable date.
        indexed = list(enumerate(normalized))
        indexed.sort(key=lambda pair: (pair[1]["_sort_date"] is not None,
                                       pair[1]["_sort_date"] or date.min,
                                       pair[0]))
        result = []
        for _, item in indexed:
            item.pop("_sort_date", None)
            result.append(item)
        return result, csv_path, None
    except Exception as exc:
        return [dict(row) for row in DEFAULT_HISTORY], csv_path, f"อ่าน CSV ไม่สำเร็จ: {exc}"


_loaded_history, HISTORY_CSV_PATH, HISTORY_LOAD_WARNING = load_history_csv()

if "history" not in st.session_state:
    st.session_state.history = _loaded_history

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
VALID_DAYS = list(DAILY_NUMBERS.keys())
MODE_LENGTHS = {"first": 6, "front3": 3, "back3": 3, "back2": 2}

# ==========================================
# 3. HELPER FUNCTIONS & FORMULAS
# ==========================================
def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_digits(value):
    return "".join(ch for ch in str(value) if ch.isdigit())


def format_result(value, mode="back3"):
    """Format a formula result only after calculation; preserve leading zeroes."""
    value = safe_digits(value)
    length = MODE_LENGTHS.get(mode)
    if length is None:
        return value
    return value.zfill(length)[-length:]


def get_target_digits(target, mode="first"):
    """Formula inputs are always the complete six-digit first-prize number."""
    target = safe_digits(target).zfill(6)[-6:]
    if mode == "first":
        return target
    if mode == "front3":
        return target[:3]
    if mode == "back3":
        return target[-3:]
    if mode == "back2":
        return target[-2:]
    return target


def get_daily_six(daily_number="-"):
    """Chosen policy: use the first six digits of the seven-digit Daily Number."""
    digits = safe_digits(daily_number)
    if not digits or daily_number == "-":
        return ""
    return digits[:6].ljust(6, "0")


def blend_base_with_daily(target, daily_number="-"):
    """Position-wise modulo-10 blend of 6-digit base and first 6 daily digits."""
    base = safe_digits(target).zfill(6)[-6:]
    daily = get_daily_six(daily_number)
    if not daily:
        return base
    return "".join(str((int(a) + int(b)) % 10) for a, b in zip(base, daily))


def calculate_digit_accuracy(prediction, answer):
    """Unordered digit overlap; useful for the any-position metric."""
    p_counter = Counter(safe_digits(prediction))
    a_counter = Counter(safe_digits(answer))
    hit = sum((p_counter & a_counter).values())
    denominator = max(len(safe_digits(prediction)), len(safe_digits(answer)))
    accuracy = (hit / denominator * 100) if denominator else 0.0
    return hit, accuracy


def evaluate_prediction(prediction, answer):
    """Return exact-position hits and any-position (multiset) hits."""
    pred = safe_digits(prediction)
    actual = safe_digits(answer)
    if not pred or not actual:
        return 0, 0, 0
    length = min(len(pred), len(actual))
    exact_hits = sum(1 for i in range(length) if pred[i] == actual[i])
    any_hits = sum((Counter(pred) & Counter(actual)).values())
    return exact_hits, any_hits, max(len(pred), len(actual))


def calculate_score(result, answer):
    """Compatibility helper: 0-100 score based on any-position digit overlap."""
    hit, _ = calculate_digit_accuracy(result, answer)
    denominator = max(len(safe_digits(result)), len(safe_digits(answer)))
    return (hit / denominator * 100) if denominator else 0.0


# ---- Original formula definitions (formula logic retained) ----
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
    # Initialise all ten digits so output length is achieved by ranked scores,
    # not by padding artificial zeroes.
    score = Counter({digit: 0 for digit in range(10)})
    for digit, count in Counter(digits).items():
        score[digit] += count * 5
    for i in range(len(digits) - 1):
        score[(digits[i] + digits[i + 1]) % 10] += 2
        score[(digits[i] * digits[i + 1]) % 10] += 2
        score[abs(digits[i] - digits[i + 1])] += 1
    ranking = sorted(score.items(), key=lambda item: (-item[1], item[0]))
    length = MODE_LENGTHS.get(mode, 4)
    return "".join(str(digit) for digit, _ in ranking[:length])


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
FORMULAS_15 = [(name, func) for name, func in formulas if name != "Cross Multiply"]


def dynamic_formula_wrapper(func, target, mode, daily_number="-"):
    """
    Corrected wrapper:
    1) Always pass all six base digits to the formula.
    2) If daily is selected, blend first-six daily digits with all six base digits.
    3) Format/truncate only the formula output, never the formula input.
    """
    base = safe_digits(target).zfill(6)[-6:]
    formula_input = blend_base_with_daily(base, daily_number)
    try:
        result = func(formula_input, mode, "-")
    except TypeError:
        try:
            result = func(formula_input, mode)
        except TypeError:
            result = func(formula_input)
    return format_result(result, mode)


# ==========================================
# 3.1 ALL 15 FORMULAS: RESULT + DIGIT FREQUENCY
# ==========================================
def analyse_all_15_formulas(target_number, daily_number="-", mode="back3"):
    rows = []
    combined_digits = []
    for name, func in FORMULAS_15:
        raw_result = dynamic_formula_wrapper(func, target_number, mode, "-")
        blended_result = dynamic_formula_wrapper(func, target_number, mode, daily_number)
        rows.append({
            "Formula": name,
            "Raw": raw_result,
            "Blended": blended_result,
            "Last 2": blended_result[-2:],
        })
        combined_digits.extend(safe_digits(blended_result))
    counts = Counter(combined_digits)
    frequency = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return rows, frequency, len(combined_digits)


def get_echo_core(history_data):
    if not history_data:
        return ["0", "1", "2", "3", "4"]
    pool = []
    for rec in history_data[-5:]:
        pool.extend(list(safe_digits(rec.get("first", ""))))
        pool.extend(list(safe_digits(rec.get("back2", ""))))
    counts = Counter(pool)
    return [digit for digit, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:5]]


def build_hybrid_pool(target_number, echo_core):
    """Rank digits using both current base occurrence and Echo Core support."""
    scores = Counter({str(d): 0 for d in range(10)})
    for digit, count in Counter(safe_digits(target_number).zfill(6)[-6:]).items():
        scores[digit] += count * 2
    for rank, digit in enumerate(echo_core):
        scores[digit] += max(1, 6 - rank)
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    return [digit for digit, _ in ranked[:6]]


def get_target_answers(record, mode):
    value = record.get(mode, "")
    if isinstance(value, list):
        return [format_result(item, mode) for item in value if safe_digits(item)]
    if value:
        return [format_result(value, mode)]
    return []


def get_daily_for_record(record):
    """Backtest uses the Daily Number belonging to the target draw's weekday."""
    return DAILY_NUMBERS.get(record.get("day", ""), "-")


def analyse_formulas(mode="back3", target_number=None, daily_number="-"):
    """Walk-forward backtest. Each historical prediction uses the next draw's weekday."""
    history = st.session_state.history
    test_range = min(max(len(history) - 1, 0), 70)
    target_history = history[-(test_range + 1):] if test_range > 0 else history
    f_weight = st.session_state.ai_settings.get("formula_weight", 1.0)
    c_weight = st.session_state.ai_settings.get("cross_weight", 0.9)

    results = []
    for name, func in formulas:
        exact_hits_total = 0
        any_hits_total = 0
        digit_slots_total = 0
        exact_draws = 0
        any_draws = 0
        valid_draws = 0
        weighted_any = 0.0
        weight_total = 0.0
        current_weight = c_weight if name == "Cross Multiply" else f_weight

        for index in range(len(target_history) - 1):
            current = target_history[index]
            next_record = target_history[index + 1]
            answers = get_target_answers(next_record, mode)
            if not answers:
                continue

            # Use the weekday of the draw being predicted, not today's selected day.
            draw_daily = get_daily_for_record(next_record)
            prediction = dynamic_formula_wrapper(
                func, current.get("first", ""), mode, draw_daily
            )

            # For multiple official 3-digit prizes, score against the best matching answer.
            metrics = [evaluate_prediction(prediction, answer) for answer in answers]
            best = max(metrics, key=lambda item: (item[0], item[1]))
            exact_hits, any_hits, slots = best

            valid_draws += 1
            exact_hits_total += exact_hits
            any_hits_total += any_hits
            digit_slots_total += slots
            exact_draws += int(exact_hits == slots)
            any_draws += int(any_hits == slots)

            recency_weight = index + 1
            weighted_any += (any_hits / slots) * recency_weight * current_weight if slots else 0
            weight_total += recency_weight * current_weight

        exact_accuracy = (exact_hits_total / digit_slots_total * 100) if digit_slots_total else 0.0
        any_accuracy = (any_hits_total / digit_slots_total * 100) if digit_slots_total else 0.0
        exact_match_rate = (exact_draws / valid_draws * 100) if valid_draws else 0.0
        any_match_rate = (any_draws / valid_draws * 100) if valid_draws else 0.0
        weighted_score = (weighted_any / weight_total * 100) if weight_total else 0.0

        results.append({
            "name": name,
            "weighted_score": weighted_score,
            "exact_accuracy": exact_accuracy,
            "any_accuracy": any_accuracy,
            "exact_match_rate": exact_match_rate,
            "any_match_rate": any_match_rate,
            "valid_draws": valid_draws,
        })

    return sorted(
        results,
        key=lambda row: (
            -row["weighted_score"],
            -row["any_accuracy"],
            -row["exact_accuracy"],
            row["name"],
        )
    )


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

    # Refresh CSV on demand so an already-running Streamlit session can pick up new draws.
    refresh_col, source_col = st.columns([1, 3])
    with refresh_col:
        if st.button("🔄 โหลดข้อมูลล่าสุดจาก CSV"):
            refreshed_history, refreshed_path, refresh_warning = load_history_csv()
            if refreshed_path and not refresh_warning:
                st.session_state.history = refreshed_history
                st.session_state["target_number_input"] = refreshed_history[-1]["first"]
                st.success(f"โหลดข้อมูลใหม่แล้ว {len(refreshed_history)} งวด")
                st.rerun()
            else:
                st.error(refresh_warning or "ไม่สามารถโหลด CSV ได้")
    with source_col:
        if HISTORY_CSV_PATH:
            st.caption(f"แหล่งข้อมูล: {os.path.basename(HISTORY_CSV_PATH)}")
        else:
            st.warning("กำลังใช้ DEFAULT_HISTORY เพราะไม่พบ history_thai.csv ในโฟลเดอร์เดียวกับไฟล์ Python")

    if HISTORY_LOAD_WARNING:
        st.warning(f"หมายเหตุแหล่งข้อมูล: {HISTORY_LOAD_WARNING}")

    col1, col2 = st.columns(2)
    with col1:
        default_target = st.session_state.history[-1]["first"] if st.session_state.history else "723294"
        target_number = st.text_input(
            "📌 เลขฐาน 6 หลักงวดล่าสุด:",
            value=default_target,
            max_chars=6,
            key="target_number_input"
        )
        if st.session_state.history:
            latest_row = st.session_state.history[-1]
            st.caption(f"งวดล่าสุดในฐานข้อมูล: {latest_row.get('date', '-')} | รางวัลที่ 1: {latest_row['first']}")
    with col2:
        day_choice = st.selectbox(
            "📅 เลือกวันประจำงวด:",
            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "ไม่ใช้ (Manual)"]
        )
        daily_number = DAILY_NUMBERS.get(day_choice, "-")

    if daily_number != "-":
        st.caption(f"Daily Number: {daily_number} | ใช้ 6 หลักแรก: {get_daily_six(daily_number)}")

    if st.button("🚀 ประมวลผล Master Report", type="primary", use_container_width=True):
        if len(safe_digits(target_number)) != 6 or not target_number.isdigit():
            st.error("❌ กรุณากรอกเลขฐาน 6 หลักให้ถูกต้อง")
        else:
            st.markdown("### 📊 เปรียบเทียบผลลัพธ์สูตรเด่น (สถิติดิบ vs ผสมวัน)")
            comp_data = []
            for formula_name in ["Formula 1", "Formula 2", "Cross Multiply"]:
                func = FORMULA_MAP[formula_name]
                raw = dynamic_formula_wrapper(func, target_number, "back3", "-")
                blended = dynamic_formula_wrapper(func, target_number, "back3", daily_number)
                comp_data.append({
                    "สูตร": formula_name,
                    "สถิติดิบ": raw,
                    "ผสมวัน": blended,
                    "เด่น 2 ตัว": blended[-2:],
                })
            st.dataframe(pd.DataFrame(comp_data), use_container_width=True, hide_index=True)

            st.markdown("### 🧮 ผลลัพธ์ครบ 15 สูตร (ไม่รวม Cross Multiply)")
            formula_rows, digit_frequency, digit_total = analyse_all_15_formulas(
                target_number, daily_number, mode="back3"
            )
            st.dataframe(pd.DataFrame(formula_rows), use_container_width=True, hide_index=True)

            st.markdown("### 🔢 ความถี่เลขเมื่อรวมผลลัพธ์จากทั้ง 15 สูตร")
            freq_df = pd.DataFrame(
                [{"เลข": digit, "จำนวนครั้ง": count} for digit, count in digit_frequency]
            )
            st.dataframe(freq_df, use_container_width=True, hide_index=True)

            if digit_frequency:
                top_digits = [digit for digit, _ in digit_frequency]
                top5_digits = top_digits[:5]
                top3_digits = top_digits[:3]
                st.markdown(
                    f"""
                    <div class="report-card">
                        <div class="report-title">🏆 สรุปความถี่จาก 15 สูตร รวม {digit_total} หลัก</div>
                        <p><b>เรียงเลขตามความถี่มากไปน้อย:</b>
                        <span style="color:#0284c7;font-size:22px;font-weight:800;">{' - '.join(top_digits)}</span></p>
                        <p><b>เลขเด่น 5 ตัว:</b>
                        <span style="color:#0369a1;font-size:20px;font-weight:800;">{' - '.join(top5_digits)}</span></p>
                        <p><b>เลขเด่น 3 ตัว:</b>
                        <span style="color:#0369a1;font-size:20px;font-weight:800;">{' - '.join(top3_digits)}</span></p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Formula rankings for all requested result groups (now actually displayed).
            st.markdown("### 🏅 อันดับสูตรจาก Backtest แยกตามประเภท")
            ranking_tables = []
            for mode_key, mode_label in [
                ("first", "รางวัลที่ 1"), ("front3", "หน้า 3 ตัว"),
                ("back3", "ท้าย 3 ตัว"), ("back2", "ท้าย 2 ตัว")
            ]:
                ranked = analyse_formulas(mode_key)
                if ranked:
                    best = ranked[0]
                    ranking_tables.append({
                        "ประเภท": mode_label,
                        "สูตรอันดับ 1": best["name"],
                        "ตรงตำแหน่ง (%)": round(best["exact_accuracy"], 2),
                        "สลับตำแหน่ง (%)": round(best["any_accuracy"], 2),
                        "ทดสอบ (งวด)": best["valid_draws"],
                    })
            st.dataframe(pd.DataFrame(ranking_tables), use_container_width=True, hide_index=True)

            # Echo Core, Super Core, hybrid selection and 2-way pairs.
            echo_core = get_echo_core(st.session_state.history)
            top_5_digits = " - ".join(echo_core)
            super_core = sorted(set(echo_core) & set(safe_digits(target_number[:3])))
            hybrid_digits = build_hybrid_pool(target_number, echo_core)
            top_6_digits = " - ".join(hybrid_digits)
            pairs = [f"{a}{b}" for a, b in combinations(echo_core, 2)]
            two_way_pairs = sorted(set(pairs + [p[::-1] for p in pairs]))

            st.markdown(f"""
            <div class="report-card">
                <div class="report-title">🎯 ชุดเลขเด่น 5–6 ตัว (Echo Core + Hybrid Pool)</div>
                <p><b>⭐ ชุดเลขเด่น 5 ตัว (Echo Core):</b>
                <span style="color:#0284c7;font-size:18px;font-weight:bold;">{top_5_digits}</span></p>
                <p><b>🌟 ชุดเลขเด่น 6 ตัว (Hybrid Pool):</b>
                <span style="color:#0369a1;font-size:18px;font-weight:bold;">{top_6_digits}</span></p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="report-card">
                <div class="report-title">🔥 เลขชนสุดยอด (SUPER CORE) & ชุด 2 ตัวไป–กลับ</div>
                <p><b>เลขไหลสะสม (Echo Core):</b> {' - '.join(echo_core)}</p>
                <p><b>เลขชนสุดยอด (Super Core):</b> {' - '.join(super_core) if super_core else 'ไม่มีเลขชน'}</p>
                <div><b>ชุด 2 ตัวไป–กลับ:</b> {" ".join([f'<span class="badge-core">{p}</span>' for p in two_way_pairs])}</div>
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
        day_in = col_b.selectbox("วัน", VALID_DAYS)
        first_in = col_c.text_input("รางวัลที่ 1 (6 หลัก)")

        col_d, col_e, col_f = st.columns(3)
        f3_in = col_d.text_input("หน้า 3 ตัว (เว้นวรรค)")
        b3_in = col_e.text_input("ท้าย 3 ตัว (เว้นวรรค)")
        b2_in = col_f.text_input("ท้าย 2 ตัว (2 หลัก)")

        submitted = st.form_submit_button("บันทึกข้อมูล")
        if submitted:
            first_clean = safe_digits(first_in)
            b2_clean = safe_digits(b2_in)
            front_values = [format_result(x, "front3") for x in f3_in.split() if safe_digits(x)]
            back_values = [format_result(x, "back3") for x in b3_in.split() if safe_digits(x)]
            if len(first_clean) != 6:
                st.error("❌ รางวัลที่ 1 ต้องเป็นตัวเลข 6 หลักเท่านั้น")
            elif b2_clean and len(b2_clean) != 2:
                st.error("❌ เลขท้าย 2 ตัวต้องมี 2 หลัก")
            elif any(len(safe_digits(x)) != 3 for x in front_values + back_values):
                st.error("❌ เลขหน้า/ท้าย 3 ตัวต้องมี 3 หลัก")
            elif date_in.strip() and any(row.get("date", "").strip() == date_in.strip() for row in st.session_state.history):
                st.error("❌ พบวันที่งวดนี้ในประวัติแล้ว กรุณาตรวจสอบข้อมูลซ้ำ")
            else:
                st.session_state.history.append({
                    "date": date_in.strip(),
                    "day": day_in,
                    "first": first_clean,
                    "front3": front_values,
                    "back3": back_values,
                    "back2": b2_clean,
                })
                st.success("✅ บันทึกข้อมูลสำเร็จ!")

    st.subheader("📋 ประวัติสลากย้อนหลังในระบบ")
    if st.session_state.history:
        latest_row = st.session_state.history[-1]
        st.info(f"ข้อมูลล่าสุดในระบบ: {latest_row.get('date', '-')} | รางวัลที่ 1: {latest_row.get('first', '-')}")
    st.caption("ไฟล์นำเข้าที่รองรับ: history_thai.csv (วางไว้โฟลเดอร์เดียวกับไฟล์ Python; รองรับ date_be, first_prize, last_2_digits)")
    history_df = pd.DataFrame(st.session_state.history)
    st.dataframe(history_df, use_container_width=True, hide_index=True)
    csv_data = history_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "⬇️ ดาวน์โหลดประวัติเป็น CSV",
        data=csv_data,
        file_name="thai_ai_history.csv",
        mime="text/csv",
    )


# ==========================================
# 7. BACKTEST PAGE
# ==========================================
elif menu == "10. รันระบบทดสอบย้อนหลัง (Backtest)":
    st.title("📈 รันระบบทดสอบย้อนหลัง (Backtest Engine)")

    if len(st.session_state.history) < 2:
        st.warning("⚠️ ต้องการข้อมูลอย่างน้อย 2 งวดขึ้นไปในการทำ Backtest")
    else:
        st.info(
            f"ประมวลผลแบบ Walk-forward จากประวัติ {len(st.session_state.history)} งวด "
            "(ใช้ Daily Number ตามวันของงวดเป้าหมาย)"
        )
        mode_labels = {
            "back2": "เลขท้าย 2 ตัว",
            "back3": "เลขท้าย 3 ตัว",
            "front3": "เลขหน้า 3 ตัว",
            "first": "รางวัลที่ 1 (6 หลัก)",
        }
        selected_mode = st.selectbox(
            "เลือกประเภทผลรางวัลสำหรับ Backtest:",
            list(mode_labels.keys()),
            format_func=lambda key: mode_labels[key],
            index=0,
        )
        results = analyse_formulas(selected_mode)

        st.subheader(f"🏆 อันดับสูตร: {mode_labels[selected_mode]}")
        result_rows = []
        for rank, item in enumerate(results, 1):
            result_rows.append({
                "อันดับ": rank,
                "สูตร": item["name"],
                "คะแนนถ่วงน้ำหนัก (%)": round(item["weighted_score"], 2),
                "ความตรงตำแหน่ง (%)": round(item["exact_accuracy"], 2),
                "ความตรงตำแหน่งครบทุกหลัก/งวด (%)": round(item["exact_match_rate"], 2),
                "ความตรงแบบสลับตำแหน่ง (%)": round(item["any_accuracy"], 2),
                "สลับตำแหน่งครบทุกหลัก/งวด (%)": round(item["any_match_rate"], 2),
                "จำนวนงวดทดสอบ": item["valid_draws"],
            })
        st.dataframe(pd.DataFrame(result_rows), use_container_width=True, hide_index=True)

        st.caption(
            "คำอธิบาย: ความตรงตำแหน่งนับเลขถูกในตำแหน่งเดียวกัน; "
            "ความตรงแบบสลับตำแหน่งนับจำนวนเลขที่ตรงโดยไม่สนใจตำแหน่ง "
            "(นับเลขซ้ำตามจำนวนครั้งจริง) ส่วน Match Rate คือสัดส่วนงวดที่ถูกครบทุกหลัก"
        )

        st.subheader("🥇 Top 3 สูตร")
        for rank, item in enumerate(results[:3], 1):
            st.write(
                f"**อันดับ {rank}: {item['name']}** | "
                f"ตรงตำแหน่ง {item['exact_accuracy']:.2f}% | "
                f"สลับตำแหน่ง {item['any_accuracy']:.2f}% | "
                f"ทดสอบ {item['valid_draws']} งวด"
            )


# ==========================================
# 8. SETTINGS PAGE
# ==========================================
elif menu == "9. ตั้งค่าน้ำหนัก AI (Settings)":
    st.title("⚙️ ตั้งค่าน้ำหนัก AI (Weight Settings)")

    w_f = st.slider("Formula Weight", 0.1, 2.0, float(st.session_state.ai_settings["formula_weight"]))
    w_c = st.slider("Cross Weight", 0.1, 2.0, float(st.session_state.ai_settings["cross_weight"]))

    if st.button("บันทึกค่าน้ำหนัก"):
        st.session_state.ai_settings["formula_weight"] = w_f
        st.session_state.ai_settings["cross_weight"] = w_c
        st.success("✅ บันทึกค่าน้ำหนักใหม่เรียบร้อย!")

    st.caption("น้ำหนักมีผลต่อคะแนนจัดอันดับสูตรใน Backtest ไม่ได้เปลี่ยนสูตรคณิตศาสตร์ดั้งเดิม.")
