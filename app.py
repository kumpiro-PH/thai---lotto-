# app.py - THAI AI PROFESSIONAL v8.0 (Complete & Fixed Edition)
import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime
from collections import Counter
import base64
import requests
from io import StringIO

# ==========================================
# 0. GLOBAL CONSTANTS
# ==========================================
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

DAILY_NUMBERS = {
    "Monday":    "462793",
    "Tuesday":   "639170",
    "Wednesday": "257308",
    "Thursday":  "176904",
    "Friday":    "730259",
    "Saturday":  "384201",
    "Sunday":    "062341",
}

VERSION = "หวยรัฐบาลไทย by TOMMY v8.0 AI ENSEMBLE FIXED"

# ==========================================
# 1. PAGE CONFIG & CUSTOM CSS (Sky Blue Theme)
# ==========================================
st.set_page_config(
    page_title="THAI AI PROFESSIONAL v8.0 - AI Ensemble",
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
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. SESSION STATE INITIALIZATION
# ==========================================
if "history" not in st.session_state:
    st.session_state.history = []

if "target_number" not in st.session_state:
    st.session_state.target_number = ""

if "current_day" not in st.session_state:
    st.session_state.current_day = "Monday"

if "daily_number" not in st.session_state:
    st.session_state.daily_number = DAILY_NUMBERS["Monday"]

if "bt_current_day" not in st.session_state:
    st.session_state.bt_current_day = "Monday"

if "bt_daily_number" not in st.session_state:
    st.session_state.bt_daily_number = DAILY_NUMBERS["Monday"]

if "ai_settings" not in st.session_state:
    st.session_state.ai_settings = {
        "formula_weight": 1.00,
        "cross_weight": 0.90,
        "daily_weight": 1.50,
        "echo_weight": 0.70,
        "recovery_weight": 0.60,
    }

# ==========================================
# 3. DATE PARSER & GITHUB API CSV LOADER/SAVER
# ==========================================
def parse_be_date(date_str):
    """รองรับวันที่ทั้ง dd/mm/yyyy, dd-mm-yyyy และ yyyy-mm-dd (ทั้ง พ.ศ. และ ค.ศ.)"""
    s = str(date_str).strip()
    if not s:
        return None
    try:
        sep = "/" if "/" in s else ("-" if "-" in s else None)
        if sep:
            parts = [int(p) for p in s.split(sep)]
            if len(parts) == 3:
                if parts[0] > 1000:  # รูปแบบ yyyy-mm-dd
                    y, m, d = parts[0], parts[1], parts[2]
                else:  # รูปแบบ dd/mm/yyyy
                    d, m, y = parts[0], parts[1], parts[2]
                if y > 2400:
                    y -= 543
                return datetime(y, m, d)
    except Exception:
        pass
    return None

def get_actual_day_and_daily_num(date_str, fallback_day):
    """คืนค่า (ชื่อวันภาษาอังกฤษ, เลขประจำวันของวันนั้นจริง)"""
    dt = parse_be_date(date_str)
    if dt:
        actual_day = DAYS[dt.weekday()]
        return actual_day, DAILY_NUMBERS.get(actual_day, DAILY_NUMBERS[fallback_day])
    return fallback_day, DAILY_NUMBERS.get(fallback_day, "462793")

def clean_prize_digits(raw_val, length=6):
    """รักษาเลข 0 นำหน้า 100% ป้องกันปัญหา float/int ตัดเลขศูนย์"""
    s = str(raw_val).strip()
    if s.endswith(".0"):
        s = s[:-2]
    digits = re.sub(r"\D", "", s)
    if not digits:
        return ""
    return digits.zfill(length)[-length:]

def get_csv_filename_by_day(day_name):
    file_map = {
        "Monday": "thai_lottery_monday_history.csv",
        "Tuesday": "thai_lottery_tuesday_history.csv",
        "Wednesday": "thai_lottery_wednesday_history.csv",
        "Thursday": "thai_lottery_thursday_history.csv",
        "Friday": "thai_lottery_friday_history.csv",
        "Saturday": "thai_lottery_saturday_history.csv",
        "Sunday": "thai_lottery_sunday_history.csv"
    }
    return file_map.get(day_name, "thai_lottery_monday_history.csv")

@st.cache_data(ttl=60, show_spinner=False)
def load_csv_data_from_github(filename):
    github_token = st.secrets.get("GITHUB_TOKEN")
    repo_name = st.secrets.get("GITHUB_REPO")
    expected_cols = ["date_be", "first_prize", "last_2_digits"]
    
    if github_token and repo_name and filename:
        headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github+json"
        }
        file_url = f"https://api.github.com/repos/{repo_name}/contents/{filename}"
        try:
            res = requests.get(file_url, headers=headers, timeout=10)
            if res.status_code == 200:
                file_data = res.json()
                content_decoded = base64.b64decode(file_data["content"]).decode("utf-8-sig")
                df = pd.read_csv(StringIO(content_decoded), dtype=str).fillna("")
                for col in expected_cols:
                    if col not in df.columns:
                        df[col] = ""
                return df[expected_cols]
        except Exception as e:
            st.toast(f"⚠️ ไม่สามารถดึงข้อมูลจาก GitHub ได้: {e}")
            
    if os.path.exists(filename):
        try:
            df = pd.read_csv(filename, dtype=str).fillna("")
            for col in expected_cols:
                if col not in df.columns:
                    df[col] = ""
            return df[expected_cols]
        except Exception:
            pass
            
    return pd.DataFrame(columns=expected_cols)

def save_csv_to_github(filename, updated_df, new_date):
    github_token = st.secrets.get("GITHUB_TOKEN")
    repo_name = st.secrets.get("GITHUB_REPO")
    branch = st.secrets.get("GITHUB_BRANCH", "main")
    
    if not github_token or not repo_name:
        st.error("❌ ยังไม่ได้ตั้งค่า GITHUB_TOKEN หรือ GITHUB_REPO ใน Streamlit Secrets")
        return False
        
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json"
    }
    file_url = f"https://api.github.com/repos/{repo_name}/contents/{filename}"
    
    try:
        res = requests.get(file_url, headers=headers, timeout=10)
        file_sha = res.json().get("sha") if res.status_code == 200 else None
        
        csv_string = updated_df.to_csv(index=False, encoding="utf-8-sig")
        encoded_content = base64.b64encode(csv_string.encode("utf-8")).decode("utf-8")
        
        payload = {
            "message": f"Update {filename} for {new_date} via Streamlit App",
            "content": encoded_content,
            "branch": branch
        }
        if file_sha:
            payload["sha"] = file_sha
            
        put_res = requests.put(file_url, headers=headers, json=payload, timeout=10)
        if put_res.status_code in [200, 201]:
            load_csv_data_from_github.clear()
            return True
        else:
            st.error(f"❌ GitHub API Error ({put_res.status_code}): {put_res.text}")
            return False
    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาดในการเชื่อมต่อ: {e}")
        return False

def load_history_by_day(day_name):
    filename = get_csv_filename_by_day(day_name)
    df = load_csv_data_from_github(filename)

    if df.empty:
        return []

    history_list = []
    for idx, row in df.iterrows():
        raw_date = str(row.get("date_be", "")).strip()
        first_val = clean_prize_digits(row.get("first_prize", ""), 6)
        back2_val = clean_prize_digits(row.get("last_2_digits", ""), 2)

        if not raw_date or not first_val:
            continue

        dt_obj = parse_be_date(raw_date)
        actual_day, actual_daily_num = get_actual_day_and_daily_num(raw_date, day_name)

        history_list.append({
            "date": raw_date,
            "dt": dt_obj if dt_obj else datetime(1900, 1, 1),
            "orig_idx": idx,
            "day": actual_day,
            "daily_num": actual_daily_num,
            "first": first_val,
            "back2": back2_val
        })
        
    # เรียงลำดับจาก "ใหม่ล่าสุด -> เก่าสุด" อย่างแม่นยำตามวันที่ พ.ศ.
    history_list.sort(key=lambda x: (x["dt"], -x["orig_idx"]), reverse=True)
    return history_list

# ==========================================
# 4. HELPER FUNCTIONS & 16 FORMULAS
# ==========================================
def safe_int(value, default=0):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_digits(value):
    return "".join(ch for ch in str(value) if ch.isdigit())

def format_result(value, mode="back2"):
    value = safe_digits(value)
    if mode == "first":
        return value.zfill(6)[-6:]
    if mode == "back2":
        return value.zfill(2)[-2:]
    return value

def get_target_digits(target, mode="back2"):
    target = safe_digits(target).zfill(6)
    if mode == "first":
        return target
    if mode == "back2":
        return target[-2:]
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

def run_backtest_analysis(day_name, history_list, override_daily_number=None, use_each_draw_daily=True):
    chrono_history = sorted(history_list, key=lambda x: (x["dt"], -x["orig_idx"]))
    summary_data = []
    details_data = []
    
    f_weight = st.session_state.ai_settings.get("formula_weight", 1.0)
    c_weight = st.session_state.ai_settings.get("cross_weight", 0.9)

    valid_tests = 0
    for name, func in formulas:
        classic_score = 0
        weighted_score = 0
        exact_hits = 0
        correct_positions = 0
        any_digit_hits = 0
        valid = 0

        for index in range(len(chrono_history) - 1):
            nxt_draw = chrono_history[index + 1]
            nxt = nxt_draw.get("back2", "")
            if not nxt:
                continue
            valid += 1
            
            test_daily = nxt_draw.get("daily_num", override_daily_number) if use_each_draw_daily else override_daily_number
            pred = dynamic_formula_wrapper(func, chrono_history[index].get("first", ""), "back2", test_daily)
            
            pt = calculate_score(pred, nxt)
            classic_score += pt
            current_weight = c_weight if name == "Cross Multiply" else f_weight
            weighted_score += (pt * (index + 1)) * current_weight

            if pred == nxt:
                exact_hits += 1
            
            pos_match = sum(1 for p_ch, a_ch in zip(pred, nxt) if p_ch == a_ch)
            correct_positions += pos_match
            
            hit_count, _ = calculate_digit_accuracy(pred, nxt)
            any_digit_hits += hit_count

            details_data.append({
                "Formula": name,
                "Date": nxt_draw.get("date", ""),
                "Day": nxt_draw.get("day", ""),
                "Daily Used": test_daily,
                "Base First": chrono_history[index].get("first", ""),
                "Prediction": pred,
                "Actual": nxt,
                "Result": "✅ ตรงเป๊ะ" if pred == nxt else ("🟡 เข้าตัว" if hit_count > 0 else "❌ พลาด"),
                "Score": pt
            })

        percent = ((classic_score / (valid * 100)) * 100) if valid else 0
        exact_pct = ((exact_hits / valid) * 100) if valid else 0
        pos_acc = ((correct_positions / (valid * 2)) * 100) if valid else 0

        summary_data.append({
            "Rank": 0,
            "Formula": name,
            "Tests": valid,
            "Exact Hits": exact_hits,
            "Exact Match (%)": exact_pct,
            "Correct Positions": correct_positions,
            "Position Accuracy (%)": pos_acc,
            "Any Digit Hits": any_digit_hits,
            "Any Digit Rate (%)": percent,
            "Raw Score": classic_score,
            "Weight": c_weight if name == "Cross Multiply" else f_weight,
            "Weighted Score": weighted_score
        })
        valid_tests = max(valid_tests, valid)

    df_sum = pd.DataFrame(summary_data)
    if not df_sum.empty:
        df_sum = df_sum.sort_values(by=["Weighted Score", "Raw Score", "Exact Match (%)"], ascending=False).reset_index(drop=True)
        df_sum["Rank"] = df_sum.index + 1

    df_det = pd.DataFrame(details_data)
    return df_sum, df_det, valid_tests

def analyse_ai_ensemble(target_number, daily_number, history_list, day_name, mode="back2"):
    settings = st.session_state.ai_settings
    f_weight = settings.get("formula_weight", 1.0)
    c_weight = settings.get("cross_weight", 0.9)
    d_weight = settings.get("daily_weight", 1.5)
    e_weight = settings.get("echo_weight", 0.7)
    r_weight = settings.get("recovery_weight", 0.6)

    perf_multiplier = {name: 1.0 for name, _ in formulas}
    if len(history_list) >= 2:
        df_bt, _, _ = run_backtest_analysis(day_name, history_list, daily_number, use_each_draw_daily=True)
        if not df_bt.empty and df_bt["Weighted Score"].max() > 0:
            max_ws = df_bt["Weighted Score"].max()
            for _, r in df_bt.iterrows():
                perf_multiplier[r["Formula"]] = 0.5 + (r["Weighted Score"] / max_ws)

    rows = []
    digit_scores = {str(d): 0.0 for d in range(10)}
    raw_digit_counts = Counter()

    for name, func in formulas:
        raw_result = dynamic_formula_wrapper(func, target_number, mode, "-")
        blended_result = dynamic_formula_wrapper(func, target_number, mode, daily_number)
        
        base_w = c_weight if name == "Cross Multiply" else f_weight
        hist_mult = perf_multiplier.get(name, 1.0)
        
        for ch in safe_digits(raw_result):
            digit_scores[ch] += (1.0 * base_w * hist_mult)
            
        for ch in safe_digits(blended_result):
            digit_scores[ch] += (1.0 * base_w * d_weight * hist_mult)
            raw_digit_counts[ch] += 1

        rows.append({
            "สูตร": name,
            "น้ำหนักสูตร": round(base_w * hist_mult, 2),
            "เลขดิบ": raw_result,
            "เลขผสมวัน": blended_result,
            "ท้าย 2 ตัว": blended_result[-2:],
        })

    if history_list:
        latest_draw = history_list[0]
        echo_digits = set(safe_digits(latest_draw.get("first", "")) + safe_digits(latest_draw.get("back2", "")))
        for ch in echo_digits:
            if ch in digit_scores:
                digit_scores[ch] += e_weight

    if len(history_list) >= 3:
        recent_5 = history_list[:5]
        appeared_recent = set()
        for draw in recent_5:
            appeared_recent.update(safe_digits(draw.get("first", "")) + safe_digits(draw.get("back2", "")))
        for d in range(10):
            s_d = str(d)
            if s_d not in appeared_recent:
                digit_scores[s_d] += r_weight

    ranked_digits = sorted(
        [(d, round(score, 2), raw_digit_counts[d]) for d, score in digit_scores.items()],
        key=lambda x: (-x[1], -x[2], int(x[0]))
    )
    return rows, ranked_digits

def build_formula_back2_rows(base_number, daily_number, actual_back2=None):
    prediction_rows = []
    for idx, (name, func) in enumerate(formulas, start=1):
        raw_res = dynamic_formula_wrapper(func, base_number, "back2", "-")
        blend_res = dynamic_formula_wrapper(func, base_number, "back2", daily_number)
        back2_val = blend_res[-2:]
        
        if actual_back2 and back2_val == str(actual_back2).zfill(2):
            back2_display = f"{back2_val} 🏆 (เข้าเป้า)"
        else:
            back2_display = back2_val

        prediction_rows.append({
            "Formula": name,
            "Raw": raw_res,
            "Blended": blend_res,
            "Back2": back2_display
        })
    return pd.DataFrame(prediction_rows)

# ==========================================
# 5. STREAMLIT UI SIDEBAR NAVIGATION
# ==========================================
st.sidebar.title("🧠 MENU CONTROL")
menu = st.sidebar.radio("เลือกหน้าเมนู:", [
    "8. All-in-One Master Report",
    "1. เพิ่ม/จัดการประวัติหวย",
    "10. รันระบบทดสอบย้อนหลัง (Backtest)",
    "9. ตั้งค่าน้ำหนัก AI (Settings)"
])

# ==========================================
# 6. ALL-IN-ONE MASTER REPORT (AI ENSEMBLE)
# ==========================================
if menu == "8. All-in-One Master Report":
    st.title("🏆 สรุปผลวิเคราะห์หวยรัฐบาลไทย AI Ensemble")
    st.caption(f"เวอร์ชัน: {VERSION}")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        day_choice = st.selectbox("📅 เลือกวันประจำงวดที่ออก:", DAYS)
        loaded_history = load_history_by_day(day_choice)
        st.session_state.history = loaded_history

        if st.session_state.current_day != day_choice or not st.session_state.target_number:
            st.session_state.current_day = day_choice
            st.session_state.daily_number = DAILY_NUMBERS.get(day_choice, "462793")
            if loaded_history:
                st.session_state.target_number = loaded_history[0]["first"]
            else:
                st.session_state.target_number = "423224"

    with col2:
        col_t1, col_t2 = st.columns([3, 1])
        with col_t1:
            target_number = st.text_input(
                "📌 เลขฐาน 6 หลักงวดล่าสุด:", 
                value=st.session_state.target_number, 
                max_chars=6,
                key="target_number_input"
            )
            st.session_state.target_number = target_number
        with col_t2:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if st.button("🔄 ดึงล่าสุด", help="ดึงรางวัลงวดล่าสุดจาก CSV ทันที"):
                if loaded_history:
                    st.session_state.target_number = loaded_history[0]["first"]
                    st.rerun()

    with col3:
        daily_number = st.text_input(
            "🔑 เลขประจำวัน (แก้ไขได้):", 
            value=st.session_state.daily_number, 
            max_chars=10,
            key="daily_number_input"
        )
        st.session_state.daily_number = daily_number

    if loaded_history:
        latest = loaded_history[0]
        st.caption(f"📁 ข้อมูลล่าสุดในฐานข้อมูล ({day_choice}): งวดวันที่ **{latest['date']}** | รางวัลที่ 1: **{latest['first']}** | ล่าง: **{latest['back2']}** (รวม {len(loaded_history)} งวด)")
    else:
        st.warning(f"⚠️ ไม่พบข้อมูลประวัติสำหรับวัน {day_choice} ระบบจะคำนวณโดยไม่มีคะแนนถ่วงน้ำหนักย้อนหลัง")

    if st.button("🚀 ประมวลผล Master Report (AI Ensemble)", type="primary", use_container_width=True):
        if len(target_number) != 6 or not target_number.isdigit():
            st.error("❌ กรุณากรอกเลขฐาน 6 หลักให้ถูกต้อง")
        elif not daily_number.strip().isdigit():
            st.error("❌ กรุณากรอกเลขประจำวันเป็นตัวเลขให้ถูกต้อง")
        else:
            formula_rows, ranked_digits = analyse_ai_ensemble(
                target_number=target_number,
                daily_number=daily_number.strip(),
                history_list=loaded_history,
                day_name=day_choice,
                mode="back2"
            )

            top_digits = [d for d, _, _ in ranked_digits]
            score_map = {d: sc for d, sc, _ in ranked_digits}
            count_map = {d: cnt for d, _, cnt in ranked_digits}

            top_6 = top_digits[:6]
            remaining = top_digits[6:]

            st.markdown(f"""
                <div style="background-color: #f8fafc; padding: 10px 15px; border-radius: 6px; border: 1px solid #e2e8f0; margin-bottom: 15px; font-weight: 600; color: #1e293b;">
                    วัน: {day_choice}  |  เลขฐาน: {target_number}  |  Daily Number: {daily_number.strip()}  |  สูตร: 16 สูตร (AI Weighted)
                </div>
            """, unsafe_allow_html=True)

            cols = st.columns([1, 1, 1, 1, 1, 1, 1.3])
            colors = ["#0284c7", "#0369a1", "#0284c7", "#0369a1", "#0284c7", "#0369a1"]
            for i in range(6):
                d = top_6[i]
                sc = score_map[d]
                cnt = count_map[d]
                with cols[i]:
                    st.markdown(f"""
                        <div style="background: white; border: 1px solid #cbd5e1; border-radius: 8px; text-align: center; padding: 12px 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                            <div style="font-size: 26px; font-weight: bold; color: {colors[i]};">{d}</div>
                            <div style="font-size: 12px; font-weight: 600; color: #0f172a; margin-top: 2px;">{sc:.1f} คะแนน</div>
                            <div style="font-size: 11px; color: #64748b;">({cnt} สูตร)</div>
                        </div>
                    """, unsafe_allow_html=True)

            with cols[6]:
                rem_text = "<br>".join([f"<b>{d}</b> = {score_map[d]:.1f} ({count_map[d]} สูตร)" for d in remaining])
                st.markdown(f"""
                    <div style="background: white; border: 1px solid #cbd5e1; border-radius: 8px; padding: 10px; font-size: 11px; color: #475569; height: 100%; display: flex; align-items: center;">
                        <div><b>เลขรอง (อันดับ 7-10):</b><br>{rem_text}</div>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("##### 🎯 ชุดเลขเด่นจัดอันดับตามคะแนน AI Ensemble (ชุด 6, 5, 4, 3 และ 2 ตัว)")
            
            set_cols = st.columns(5)
            def get_stat_str(digits_list):
                return " | ".join([f"{d}:{score_map[d]:.1f}" for d in digits_list])

            configs = [
                ("ชุด 6 ตัว", top_digits[:6], "#0f766e"),
                ("ชุด 5 ตัว", top_digits[:5], "#15803d"),
                ("ชุด 4 ตัว", top_digits[:4], "#0369a1"),
                ("ชุด 3 ตัว", top_digits[:3], "#7e22ce"),
                ("ชุด 2 ตัว", top_digits[:2], "#b45309"),
            ]

            for idx, (title, d_list, hex_color) in enumerate(configs):
                with set_cols[idx]:
                    st.markdown(f"""
                        <div style="background: white; border: 1px solid #cbd5e1; border-radius: 8px; text-align: center; padding: 14px 6px;">
                            <div style="font-size: 12px; color: #64748b; margin-bottom: 5px;">{title}</div>
                            <div style="font-size: 19px; font-weight: bold; color: {hex_color}; letter-spacing: 2px;">{" ".join(d_list)}</div>
                            <div style="font-size: 10px; color: #94a3b8; margin-top: 8px;">{get_stat_str(d_list)}</div>
                        </div>
                    """, unsafe_allow_html=True)

            with st.expander("📋 ดูตารางผลลัพธ์รายสูตร (ครบทั้ง 16 สูตร พร้อมน้ำหนัก AI)", expanded=True):
                st.dataframe(pd.DataFrame(formula_rows), use_container_width=True, hide_index=True)

# ==========================================
# 7. MANAGEMENT HISTORY PAGE (GitHub Sync)
# ==========================================
elif menu == "1. เพิ่ม/จัดการประวัติหวย":
    st.title("📚 เพิ่มและจัดการประวัติหวยรายวัน (GitHub Sync)")
    day_upload = st.selectbox("เลือกวันสำหรับจัดการประวัติ:", DAYS)
    target_csv = get_csv_filename_by_day(day_upload)
    
    with st.expander("➕ เพิ่มข้อมูลงวดล่าสุดด้วยตนเอง (ซิงก์ขึ้น GitHub อัตโนมัติ)", expanded=True):
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            input_date = st.text_input("📅 วันที่ (พ.ศ.) เช่น 16/11/2569", value="16/11/2569")
        with col_f2:
            input_first = st.text_input("🎯 รางวัลที่ 1 (6 หลัก)", max_chars=6, value="")
        with col_f3:
            input_back2 = st.text_input("🔢 เลขท้าย 2 ตัว", max_chars=2, value="")
            
        if st.button("💾 บันทึกและซิงก์ขึ้น GitHub", type="primary"):
            if len(input_first) == 6 and input_first.isdigit() and len(input_back2) == 2 and input_back2.isdigit():
                existing_df = load_csv_data_from_github(target_csv)
                
                new_row = pd.DataFrame([{
                    "date_be": input_date.strip(),
                    "first_prize": str(input_first.strip()).zfill(6),
                    "last_2_digits": str(input_back2.strip()).zfill(2)
                }])
                
                updated_df = pd.concat([new_row, existing_df], ignore_index=True)
                updated_df = updated_df.drop_duplicates(subset=["date_be", "first_prize"], keep="first")
                
                updated_df["_sort_dt"] = updated_df["date_be"].apply(lambda x: parse_be_date(x) or datetime(1900, 1, 1))
                updated_df = updated_df.sort_values(by="_sort_dt", ascending=False).drop(columns=["_sort_dt"])
                
                expected_cols = ["date_be", "first_prize", "last_2_digits"]
                updated_df = updated_df[expected_cols]

                success = save_csv_to_github(target_csv, updated_df, input_date.strip())
                if success:
                    if st.session_state.current_day == day_upload:
                        st.session_state.target_number = str(input_first.strip()).zfill(6)
                    st.success(f"✅ บันทึกและซิงก์ข้อมูลลง GitHub (`{target_csv}`) สำเร็จเรียบร้อย!")
                    st.rerun()
            else:
                st.error("❌ กรุณากรอกรางวัลที่ 1 ให้ครบ 6 หลัก และเลขท้าย 2 ตัวให้ครบ 2 หลักด้วยตัวเลขเท่านั้น")

    current_history = load_history_by_day(day_upload)
    if current_history:
        st.subheader(f"📋 ข้อมูลประวัติปัจจุบันของวัน: {day_upload} (รวม {len(current_history)} งวด)")
        display_hist = pd.DataFrame(current_history)[["date", "day", "daily_num", "first", "back2"]]
        display_hist.columns = ["วันที่ (พ.ศ.)", "วันจริง", "เลขประจำวัน", "รางวัลที่ 1", "เลขท้าย 2 ตัว"]
        st.dataframe(display_hist, use_container_width=True, hide_index=True)
    else:
        st.info(f"ยังไม่มีข้อมูลประวัติของวัน {day_upload}")

# ==========================================
# 8. COMPLETE BACKTEST ENGINE (FIXED SYNC)
# ==========================================
elif menu == "10. รันระบบทดสอบย้อนหลัง (Backtest)":
    st.title("📈 ระบบทดสอบย้อนหลัง (Backtest Engine)")
    st.caption("ทดสอบความแม่นยำรายสูตร โดยเรียงลำดับตามวันที่จริงและใช้เลขประจำวันตรงตามวันออกรางวัลของแต่ละงวด")

    bt_col1, bt_col2, bt_col3 = st.columns(3)
    with bt_col1:
        backtest_day = st.selectbox("📅 เลือกวันสำหรับรัน Backtest:", DAYS, key="bt_day")
        history = load_history_by_day(backtest_day)
        if st.session_state.bt_current_day != backtest_day:
            st.session_state.bt_current_day = backtest_day
            st.session_state.bt_daily_number = DAILY_NUMBERS[backtest_day]
            if history:
                st.session_state["bt_target_number"] = history[0]["first"]

    with bt_col2:
        col_b1, col_b2 = st.columns([3, 1])
        with col_b1:
            if "bt_target_number" not in st.session_state or not st.session_state["bt_target_number"]:
                st.session_state["bt_target_number"] = st.session_state.get("target_number") or (history[0]["first"] if history else "423224")
            
            base_number = st.text_input(
                "📌 เลขฐาน 6 หลักงวดล่าสุด (สำหรับทำนายงวดถัดไป):",
                max_chars=6,
                key="bt_target_number"
            )
        with col_b2:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if st.button("🔄 ล่าสุด", key="bt_sync_btn", help="ดึงรางวัลงวดล่าสุดจาก CSV"):
                if history:
                    st.session_state["bt_target_number"] = history[0]["first"]
                    st.rerun()

    with bt_col3:
        daily_number = st.text_input(
            "🔑 เลขประจำวันงวดถัดไป (แก้ไขได้):",
            value=st.session_state.bt_daily_number,
            max_chars=10,
            key="bt_daily_number_input"
        )
        st.session_state.bt_daily_number = daily_number

    use_real_daily = st.checkbox("✅ ใช้เลขประจำวัน (Daily Number) ตรงตามวันออกรางวัลจริงของแต่ละงวดในอดีต", value=True)
    st.info(f"วันทดสอบ: {backtest_day} | ประวัติ: {len(history)} งวด | โหมดเลขประจำวันย้อนหลัง: {'ตามวันจริงของแต่ละงวด' if use_real_daily else f'ใช้ค่าเดียว ({daily_number.strip()})'}")

    if st.button("🚀 รันผล Backtest ทั้งหมด", type="primary", use_container_width=True):
        if len(base_number) != 6 or not base_number.isdigit():
            st.error("❌ กรุณากรอกเลขฐานให้ครบ 6 หลัก")
        elif not daily_number.strip().isdigit():
            st.error("❌ กรุณากรอกเลขประจำวันเป็นตัวเลขให้ถูกต้อง")
        elif len(history) < 2:
            st.warning(f"⚠️ ข้อมูล {backtest_day} ไม่เพียงพอ ต้องมีอย่างน้อย 2 งวด")
        else:
            summary, details, test_count = run_backtest_analysis(
                backtest_day, history, daily_number.strip(), use_each_draw_daily=use_real_daily
            )
            prediction_df = build_formula_back2_rows(base_number, daily_number.strip())

            df_bt_detail = summary.merge(prediction_df, on="Formula", how="left")
            df_bt_detail = df_bt_detail.rename(columns={
                "Rank": "อันดับ",
                "Formula": "สูตร",
                "Raw": "เลขดิบ (Raw)",
                "Blended": "เลขผสมวัน (Blended)",
                "Back2": "เลขท้าย 2 ตัวงวดถัดไป",
                "Tests": "งวดทดสอบ",
                "Exact Hits": "ถูกตรง 2 ตัว",
                "Exact Match (%)": "Exact Match (%)",
                "Correct Positions": "ถูกหลัก",
                "Position Accuracy (%)": "แม่นยำตำแหน่ง (%)",
                "Raw Score": "คะแนนดิบ",
                "Weight": "น้ำหนัก",
                "Weighted Score": "คะแนนคูณน้ำหนัก",
            })

            st.success(f"✅ ประมวลผลสำเร็จ: ทดสอบย้อนหลัง {test_count} คู่ข้อมูล (ทำนาย 2 ตัวล่างจากรางวัลที่ 1 งวดก่อนหน้า)")

            st.subheader("📊 ตารางผลลัพธ์รายสูตร + เลขท้าย 2 ตัวงวดถัดไป")
            display_columns = [
                "อันดับ", "สูตร", "เลขดิบ (Raw)",
                "เลขผสมวัน (Blended)", "เลขท้าย 2 ตัวงวดถัดไป",
                "คะแนนคูณน้ำหนัก", "Exact Match (%)",
                "แม่นยำตำแหน่ง (%)", "งวดทดสอบ"
            ]
            st.dataframe(
                df_bt_detail[display_columns].style.format({
                    "คะแนนคูณน้ำหนัก": "{:.2f}",
                    "Exact Match (%)": "{:.2f}%",
                    "แม่นยำตำแหน่ง (%)": "{:.2f}%"
                }),
                use_container_width=True,
                hide_index=True
            )

            st.divider()
            st.subheader("🏆 TOP 3 FORMULA — ผล Backtest ย้อนหลัง")
            top3 = df_bt_detail.head(3)
            top_cols = st.columns(3)
            for col, (_, item) in zip(top_cols, top3.iterrows()):
                with col:
                    st.metric(
                        label=f"อันดับ {int(item['อันดับ'])}: {item['สูตร']}",
                        value=f"{item['Exact Match (%)']:.2f}%",
                        delta=f"แม่นยำตำแหน่ง {item['แม่นยำตำแหน่ง (%)']:.2f}%"
                    )
                    st.markdown(f"**เลข Back2 งวดถัดไป: `{item['เลขท้าย 2 ตัวงวดถัดไป']}`**")
                    st.caption(f"คะแนนคูณน้ำหนัก: {item['คะแนนคูณน้ำหนัก']:.2f}")

            st.divider()
            st.subheader("📜 ประวัติการทายผลย้อนหลังรายงวด (Backtest Logs)")
            with st.expander("🔎 คลิกเพื่อดูประวัติการทายผลย้อนหลังทั้งหมด", expanded=False):
                if not details.empty:
                    filter_formula = st.selectbox("กรองดูเฉพาะสูตร:", ["ทั้งหมด"] + [f[0] for f in formulas])
                    filtered_det = details if filter_formula == "ทั้งหมด" else details[details["Formula"] == filter_formula]
                    st.dataframe(filtered_det, use_container_width=True, hide_index=True)

# ==========================================
# 9. AI WEIGHT SETTINGS PAGE (ACTIVE IN ENGINE)
# ==========================================
elif menu == "9. ตั้งค่าน้ำหนัก AI (Settings)":
    st.title("⚙️ ตั้งค่าน้ำหนัก AI และพารามิเตอร์ระบบ")
    st.caption("ค่าน้ำหนักทั้งหมดมีผลโดยตรงต่อการจัดอันดับเลขเด่นในหน้า Master Report และ Backtest")

    with st.form("ai_settings_form"):
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            f_weight = st.slider(
                "น้ำหนักสูตรหลัก (Formula Weight)",
                min_value=0.10, max_value=3.00,
                value=float(st.session_state.ai_settings["formula_weight"]),
                step=0.05
            )
            c_weight = st.slider(
                "น้ำหนักสูตร Cross Multiply (Cross Weight)",
                min_value=0.10, max_value=3.00,
                value=float(st.session_state.ai_settings["cross_weight"]),
                step=0.05
            )
            d_weight = st.slider(
                "น้ำหนักเลขประจำวัน (Daily Weight - ตัวคูณเลขผสมวัน)",
                min_value=0.10, max_value=3.00,
                value=float(st.session_state.ai_settings["daily_weight"]),
                step=0.05
            )
        with col_s2:
            e_weight = st.slider(
                "น้ำหนักเลขสะท้อนงวดล่าสุด (Echo Weight)",
                min_value=0.00, max_value=3.00,
                value=float(st.session_state.ai_settings["echo_weight"]),
                step=0.05
            )
            r_weight = st.slider(
                "น้ำหนักเลขดับ/ฟื้นตัวใน 5 งวด (Recovery Weight)",
                min_value=0.00, max_value=3.00,
                value=float(st.session_state.ai_settings["recovery_weight"]),
                step=0.05
            )

        submitted = st.form_submit_button("💾 บันทึกการตั้งค่า", type="primary")
        if submitted:
            st.session_state.ai_settings = {
                "formula_weight": f_weight,
                "cross_weight": c_weight,
                "daily_weight": d_weight,
                "echo_weight": e_weight,
                "recovery_weight": r_weight,
            }
            st.success("✅ บันทึกค่าน้ำหนัก AI เรียบร้อยแล้ว! ระบบ Master Report จะใช้ค่าใหม่ทันที")

    if st.button("🔄 รีเซ็ตกลับเป็นค่าเริ่มต้น (Default)"):
        st.session_state.ai_settings = {
            "formula_weight": 1.00,
            "cross_weight": 0.90,
            "daily_weight": 1.50,
            "echo_weight": 0.70,
            "recovery_weight": 0.60,
        }
        st.rerun()
