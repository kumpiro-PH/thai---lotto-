# app.py - THAI AI PROFESSIONAL v7.9 (GitHub API Sync Edition)
import streamlit as st
import pandas as pd
import os
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
    "Saturday":  "895260",
    "Sunday":    "062341",
}

VERSION = "หวยรัฐบาลไทย by TOMMY v7.9 GITHUB SYNC"

# ==========================================
# 1. PAGE CONFIG & CUSTOM CSS (Sky Blue Theme)
# ==========================================
st.set_page_config(
    page_title="THAI AI PROFESSIONAL v7.9 - GitHub API Sync",
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

if "uploaded_csvs" not in st.session_state:
    st.session_state.uploaded_csvs = {}

if "target_number" not in st.session_state:
    st.session_state.target_number = "423224"

if "current_day" not in st.session_state:
    st.session_state.current_day = "Monday"

if "ai_settings" not in st.session_state:
    st.session_state.ai_settings = {
        "formula_weight": 1.00,
        "cross_weight": 0.90,
        "daily_weight": 1.50,
        "echo_weight": 0.70,
        "recovery_weight": 0.60,
    }

# ==========================================
# 3. GITHUB API & ROBUST CSV LOADER/SAVER
# ==========================================
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

def load_csv_data_from_github(filename):
    """อ่าน CSV จาก GitHub API (พร้อม fallback มาอ่านในเครื่อง)"""
    github_token = st.secrets.get("GITHUB_TOKEN")
    repo_name = st.secrets.get("GITHUB_REPO")
    
    if github_token and repo_name and filename:
        headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github+json"
        }
        file_url = f"https://api.github.com/repos/{repo_name}/contents/{filename}"
        try:
            res = requests.get(file_url, headers=headers)
            if res.status_code == 200:
                file_data = res.json()
                content_decoded = base64.b64decode(file_data["content"]).decode("utf-8")
                return pd.read_csv(StringIO(content_decoded), dtype=str).fillna("")
        except Exception:
            pass
            
    # Fallback อ่านในเครื่อง
    if os.path.exists(filename):
        try:
            return pd.read_csv(filename, dtype=str).fillna("")
        except Exception:
            pass
            
    return pd.DataFrame(columns=["date_be", "first_prize", "last_2_digits"])

def save_csv_to_github(filename, updated_df, new_date):
    """บันทึกและซิงก์ข้อมูล CSV ตรงขึ้น GitHub ผ่าน API อัตโนมัติ"""
    github_token = st.secrets.get("GITHUB_TOKEN")
    repo_name = st.secrets.get("GITHUB_REPO")
    branch = st.secrets.get("GITHUB_BRANCH", "main")
    
    if not github_token or not repo_name:
        st.error("ยังไม่ได้ตั้งค่า GITHUB_TOKEN หรือ GITHUB_REPO ใน Streamlit Secrets")
        return False
        
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json"
    }
    file_url = f"https://api.github.com/repos/{repo_name}/contents/{filename}"
    
    # 1. ดึงไฟล์เดิมจาก GitHub เพื่อเอา SHA
    res = requests.get(file_url, headers=headers)
    file_sha = None
    if res.status_code == 200:
        file_sha = res.json().get("sha")
        
    # 2. แปลงเป็น CSV string และเข้ารหัส Base64
    csv_string = updated_df.to_csv(index=False, encoding="utf-8-sig")
    encoded_content = base64.b64encode(csv_string.encode("utf-8")).decode("utf-8")
    
    # 3. ส่งคำขอ PUT ไปที่ GitHub API
    payload = {
        "message": f"Update {filename} for {new_date} via Streamlit App",
        "content": encoded_content,
        "branch": branch
    }
    if file_sha:
        payload["sha"] = file_sha
        
    put_res = requests.put(file_url, headers=headers, json=payload)
    if put_res.status_code in [200, 201]:
        return True
    else:
        st.error(f"❌ GitHub API Error ({put_res.status_code}): {put_res.text}")
        return False

def load_history_by_day(day_name):
    if day_name in st.session_state.uploaded_csvs:
        df = st.session_state.uploaded_csvs[day_name]
    else:
        filename = get_csv_filename_by_day(day_name)
        df = load_csv_data_from_github(filename)

    if df.empty:
        return []

    history_list = []
    for _, row in df.iterrows():
        raw_first = str(row.get("first_prize", ""))
        try:
            first_val = str(int(float(raw_first))).zfill(6)
        except:
            first_val = "000000"

        history_list.append({
            "date": str(row.get("date_be", "")),
            "day": day_name,
            "first": first_val,
            "back2": str(row.get("last_2_digits", "")).zfill(2)
        })
    return history_list

# ==========================================
# 4. HELPER FUNCTIONS & FORMULAS
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

def run_backtest_analysis(day_name, history_list, daily_number):
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

        for index in range(len(history_list) - 1):
            nxt = history_list[index + 1].get("back2", "")
            if not nxt: 
                continue
            valid += 1
            pred = dynamic_formula_wrapper(func, history_list[index].get("first", ""), "back2", daily_number)
            
            pt = calculate_score(pred, nxt)
            classic_score += pt
            current_weight = c_weight if name == "Cross Multiply" else f_weight
            weighted_score += (pt * (index + 1)) * current_weight

            if pred == nxt:
                exact_hits += 1
            
            hit_count, _ = calculate_digit_accuracy(pred, nxt)
            any_digit_hits += hit_count

            details_data.append({
                "Formula": name,
                "Date": history_list[index + 1].get("date", ""),
                "Prediction": pred,
                "Actual": nxt,
                "Score": pt
            })

        percent = ((classic_score / (valid * 100)) * 100) if valid else 0
        exact_pct = ((exact_hits / valid) * 100) if valid else 0
        pos_acc = percent

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

def build_formula_back2_rows(base_number, daily_number, actual_back2=None):
    prediction_rows = []
    for idx, (name, func) in enumerate(formulas, start=1):
        raw_res = dynamic_formula_wrapper(func, base_number, "back2", "-")
        blend_res = dynamic_formula_wrapper(func, base_number, "back2", daily_number)
        back2_val = blend_res[-2:]
        
        if actual_back2 and back2_val == str(actual_back2).zfill(2):
            back2_display = f"{back2_val} 🏆 (ตัวอย่างสูตรที่ {idx} เข้าเป้า)"
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
# 6. ALL-IN-ONE MASTER REPORT 
# ==========================================
if menu == "8. All-in-One Master Report":
    st.title("🏆 สรุปผลวิเคราะห์หวยรัฐบาลไทยจากสถิติ (GitHub Sync)")
    st.caption(f"เวอร์ชัน: {VERSION}")
    
    col1, col2 = st.columns(2)
    with col1:
        day_choice = st.selectbox(
            "📅 เลือกวันประจำงวด:", 
            DAYS
        )
        
        loaded_history = load_history_by_day(day_choice)
        st.session_state.history = loaded_history
        daily_number = DAILY_NUMBERS.get(day_choice, "462793")

        if st.session_state.current_day != day_choice:
            st.session_state.current_day = day_choice
            if loaded_history:
                st.session_state.target_number = loaded_history[0]["first"]

    with col2:
        if loaded_history and not st.session_state.target_number:
            st.session_state.target_number = loaded_history[0]["first"]

        target_number = st.text_input(
            "📌 เลขฐาน 6 หลักงวดล่าสุด:", 
            value=st.session_state.target_number, 
            max_chars=6,
            key="target_number_input"
        )
        st.session_state.target_number = target_number

    if not st.session_state.history:
        st.warning(f"⚠️ ไม่พบข้อมูลประวัติสำหรับวัน {day_choice} กรุณาตรวจสอบไฟล์ CSV หรืออัปโหลดผ่านเมนู 'เพิ่ม/จัดการประวัติหวย'")
    else:
        if st.button("🚀 ประมวลผล Master Report", type="primary", use_container_width=True):
            if len(target_number) != 6 or not target_number.isdigit():
                st.error("❌ กรุณากรอกเลขฐาน 6 หลักให้ถูกต้อง")
            else:
                frequency_rows, frequency, frequency_total = analyse_all_15_formulas(
                    target_number=target_number,
                    daily_number=daily_number,
                    mode="back2"
                )

                frequency_counts = dict(frequency)
                top_digits = [digit for digit, _ in frequency]
                top_6 = top_digits[:6]
                remaining = top_digits[6:]

                st.markdown(f"""
                    <div style="background-color: #f8fafc; padding: 10px 15px; border-radius: 6px; border: 1px solid #e2e8f0; margin-bottom: 15px; font-weight: 600; color: #1e293b;">
                        วัน: {day_choice}   |   เลขฐาน: {target_number}   |   Daily Number: {daily_number}   |   จำนวนสูตร: 15   |   จำนวนหลัก: {frequency_total}
                    </div>
                """, unsafe_allow_html=True)

                cols = st.columns([1, 1, 1, 1, 1, 1, 1.2])
                colors = ["#0284c7", "#0369a1", "#0284c7", "#0369a1", "#0284c7", "#0369a1"]
                for i in range(6):
                    if i < len(top_6):
                        d = top_6[i]
                        cnt = frequency_counts.get(d, 0)
                        with cols[i]:
                            st.markdown(f"""
                                <div style="background: white; border: 1px solid #cbd5e1; border-radius: 8px; text-align: center; padding: 12px 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                                    <div style="font-size: 24px; font-weight: bold; color: {colors[i]};">{d}</div>
                                    <div style="font-size: 12px; color: #64748b; margin-top: 4px;">{cnt} ครั้ง</div>
                                </div>
                            """, unsafe_allow_html=True)

                with cols[6]:
                    rem_text = "   |   ".join([f"{d} = {frequency_counts.get(d, 0)} ครั้ง" for d in remaining])
                    st.markdown(f"""
                        <div style="background: white; border: 1px solid #cbd5e1; border-radius: 8px; padding: 10px; font-size: 11px; color: #475569; height: 100%; display: flex; align-items: center;">
                            <div><b>เลขที่เหลือ:</b><br>{rem_text}</div>
                        </div>
                    """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                st.markdown("##### ชุดเลขเด่นจากความถี่รวม 15 สูตร")
                set_cols = st.columns(4)
                
                def get_stat_str(digits_list):
                    return " | ".join([f"{d}:{frequency_counts.get(d, 0)}" for d in digits_list])

                set5 = top_digits[:5]
                with set_cols[0]:
                    st.markdown(f"""
                        <div style="background: white; border: 1px solid #cbd5e1; border-radius: 8px; text-align: center; padding: 15px;">
                            <div style="font-size: 12px; color: #64748b; margin-bottom: 5px;">ชุด 5 ตัว</div>
                            <div style="font-size: 20px; font-weight: bold; color: #15803d; letter-spacing: 3px;">{" ".join(set5)}</div>
                            <div style="font-size: 10px; color: #94a3b8; margin-top: 8px;">{get_stat_str(set5)}</div>
                        </div>
                    """, unsafe_allow_html=True)

                set4 = top_digits[:4]
                with set_cols[1]:
                    st.markdown(f"""
                        <div style="background: white; border: 1px solid #cbd5e1; border-radius: 8px; text-align: center; padding: 15px;">
                            <div style="font-size: 12px; color: #64748b; margin-bottom: 5px;">ชุด 4 ตัว</div>
                            <div style="font-size: 20px; font-weight: bold; color: #0369a1; letter-spacing: 3px;">{" ".join(set4)}</div>
                            <div style="font-size: 10px; color: #94a3b8; margin-top: 8px;">{get_stat_str(set4)}</div>
                        </div>
                    """, unsafe_allow_html=True)

                set3 = top_digits[:3]
                with set_cols[2]:
                    st.markdown(f"""
                        <div style="background: white; border: 1px solid #cbd5e1; border-radius: 8px; text-align: center; padding: 15px;">
                            <div style="font-size: 12px; color: #64748b; margin-bottom: 5px;">ชุด 3 ตัว</div>
                            <div style="font-size: 20px; font-weight: bold; color: #7e22ce; letter-spacing: 3px;">{" ".join(set3)}</div>
                            <div style="font-size: 10px; color: #94a3b8; margin-top: 8px;">{get_stat_str(set3)}</div>
                        </div>
                    """, unsafe_allow_html=True)

                set2 = top_digits[:2]
                with set_cols[3]:
                    st.markdown(f"""
                        <div style="background: white; border: 1px solid #cbd5e1; border-radius: 8px; text-align: center; padding: 15px;">
                            <div style="font-size: 12px; color: #64748b; margin-bottom: 5px;">ชุด 2 ตัว</div>
                            <div style="font-size: 20px; font-weight: bold; color: #b45309; letter-spacing: 3px;">{" ".join(set2)}</div>
                            <div style="font-size: 10px; color: #94a3b8; margin-top: 8px;">{get_stat_str(set2)}</div>
                        </div>
                    """, unsafe_allow_html=True)

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
            input_date = st.text_input("📅 วันที่ (พ.ศ.) เช่น 01/07/2569", value="01/07/2569")
        with col_f2:
            input_first = st.text_input("🎯 รางวัลที่ 1 (6 หลัก)", max_chars=6, value="")
        with col_f3:
            input_back2 = st.text_input("🔢 เลขท้าย 2 ตัว", max_chars=2, value="")
            
        if st.button("💾 บันทึกและซิงก์ขึ้น GitHub"):
            if len(input_first) == 6 and input_first.isdigit() and len(input_back2) == 2 and input_back2.isdigit():
                current_list = load_history_by_day(day_upload)
                new_entry = {
                    "date_be": input_date.strip(),
                    "first_prize": input_first.strip(),
                    "last_2_digits": input_back2.strip()
                }
                current_list.insert(0, new_entry)
                
                # แปลงเป็น DataFrame และบันทึกผ่าน GitHub API
                updated_df = pd.DataFrame(current_list)
                # จัดเรียงชื่อคอลัมน์ให้ตรงมาตรฐาน
                expected_cols = ["date_be", "first_prize", "last_2_digits"]
                for c in expected_cols:
                    if c not in updated_df.columns:
                        updated_df[c] = ""
                updated_df = updated_df[expected_cols]

                success = save_csv_to_github(target_csv, updated_df, input_date.strip())
                if success:
                    st.session_state.uploaded_csvs[day_upload] = updated_df
                    st.success(f"✅ บันทึกและซิงก์ข้อมูลลง GitHub (`{target_csv}`) สำเร็จเรียบร้อย!")
                    st.rerun()
                else:
                    st.error("❌ เกิดข้อผิดพลาดในการเชื่อมต่อ GitHub API")
            else:
                st.error("❌ กรุณากรอกรางวัลที่ 1 ให้ครบ 6 หลัก และเลขท้าย 2 ตัวให้ครบ 2 หลักด้วยตัวเลขเท่านั้น")

    st.markdown("---")

    uploaded_file = st.file_uploader(f"📂 หรืออัปโหลดไฟล์ CSV สำหรับวัน {day_upload}", type=["csv"])
    if uploaded_file is not None:
        try:
            df_up = pd.read_csv(uploaded_file, dtype=str).fillna("")
            success = save_csv_to_github(target_csv, df_up, "Uploaded CSV")
            if success:
                st.session_state.uploaded_csvs[day_upload] = df_up
                st.success(f"✅ อัปโหลดและซิงก์ไฟล์ CSV ของวัน {day_upload} ขึ้น GitHub สำเร็จ!")
                st.rerun()
        except Exception as e:
            st.error(f"❌ อ่านหรือซิงก์ไฟล์ไม่สำเร็จ: {e}")

    current_history = load_history_by_day(day_upload)
    if current_history:
        st.subheader(f"📋 ข้อมูลประวัติปัจจุบันของวัน: {day_upload}")
        st.dataframe(pd.DataFrame(current_history), use_container_width=True, hide_index=True)
    else:
        st.info(f"ยังไม่มีข้อมูลประวัติของวัน {day_upload}")

# ==========================================
# 8. COMPLETE BACKTEST ENGINE
# ==========================================
elif menu == "10. รันระบบทดสอบย้อนหลัง (Backtest)":
    st.title("📈 ระบบทดสอบย้อนหลัง (Backtest Engine)")
    st.caption("แสดงผล Backtest แยกรายสูตร พร้อมเลขท้าย 2 ตัวที่คำนวณจากเลขฐานล่าสุด")

    backtest_day = st.selectbox("📅 เลือกวันสำหรับรัน Backtest:", DAYS, key="bt_day")
    daily_number = DAILY_NUMBERS[backtest_day]
    history = load_history_by_day(backtest_day)

    base_number = st.text_input(
        "📌 เลขฐาน 6 หลักงวดล่าสุดสำหรับคำนวณเลขงวดถัดไป:",
        value=st.session_state.get("target_number", "423224"),
        max_chars=6,
        key="bt_target_number"
    )

    st.info(f"วันทดสอบ: {backtest_day} | ประวัติ: {len(history)} งวด | Daily Number: {daily_number}")

    if st.button("🚀 รันผล Backtest ทั้งหมด", type="primary", use_container_width=True):
        if len(base_number) != 6 or not base_number.isdigit():
            st.error("กรุณากรอกเลขฐานให้ครบ 6 หลัก")
        elif len(history) < 2:
            st.warning(f"ข้อมูล {backtest_day} ไม่เพียงพอ ต้องมีอย่างน้อย 2 งวด")
        else:
            summary, details, test_count = run_backtest_analysis(backtest_day, history, daily_number)
            prediction_df = build_formula_back2_rows(base_number, daily_number)

            df_bt_detail = summary.merge(prediction_df, on="Formula", how="left")
            df_bt_detail = df_bt_detail.rename(columns={
                "Rank": "อันดับ",
                "Formula": "สูตร",
                "Raw": "เลขดิบ (Raw)",
                "Blended": "เลขผสมวัน (Blended)",
                "Back2": "เลขท้าย 2 ตัว (Back2)",
                "Tests": "จำนวนงวดทดสอบ",
                "Exact Hits": "ถูกตรง 2 ตำแหน่ง",
                "Exact Match (%)": "Exact Match (%)",
                "Correct Positions": "จำนวนหลักถูกตำแหน่ง",
                "Position Accuracy (%)": "ความแม่นยำตำแหน่ง (%)",
                "Any Digit Hits": "จำนวนตัวเลขที่ตรงกัน",
                "Any Digit Rate (%)": "ความถี่ตัวเลขตรงกัน (%)",
                "Raw Score": "คะแนนดิบ",
                "Weight": "น้ำหนัก",
                "Weighted Score": "คะแนนคูณน้ำหนัก",
            })

            st.success(f"ประมวลผลสำเร็จ: ทดสอบย้อนหลัง {test_count} คู่ข้อมูล และคำนวณเลขงวดถัดไปครบ {len(prediction_df)} สูตร")

            st.subheader("📊 ตารางผลลัพธ์รายสูตร + เลขท้าย 2 ตัว")
            with st.expander("🔍 ดูตารางรายละเอียดทุกสูตร", expanded=True):
                display_columns = [
                    "อันดับ", "สูตร", "เลขดิบ (Raw)",
                    "เลขผสมวัน (Blended)", "เลขท้าย 2 ตัว (Back2)",
                    "คะแนนคูณน้ำหนัก", "คะแนนดิบ", "Exact Match (%)",
                    "ความแม่นยำตำแหน่ง (%)", "จำนวนงวดทดสอบ"
                ]
                st.dataframe(df_bt_detail[display_columns], use_container_width=True, hide_index=True)

            st.divider()
            st.subheader("🏆 TOP 3 FORMULA — ผล Backtest ย้อนหลัง")
            top3 = df_bt_detail.head(3)
            top_cols = st.columns(3)
            for col, (_, item) in zip(top_cols, top3.iterrows()):
                with col:
                    st.metric(
                        label=f"อันดับ {int(item['อันดับ'])}: {item['สูตร']}",
                        value=f"{item['Exact Match (%)']:.2f}%",
                        delta=f"ความแม่นยำ {item['ความแม่นยำตำแหน่ง (%)']:.2f}%"
                    )
                    st.markdown(f"**เลข Back2 งวดถัดไป: {item['เลขท้าย 2 ตัว (Back2)']}**")
                    st.caption(f"คะแนนคูณน้ำหนัก: {item['คะแนนคูณน้ำหนัก']:.2f}")

            st.divider()
            st.subheader("📈 เปรียบเทียบ Exact Match (%)")
            chart_data = df_bt_detail.set_index("สูตร")[["Exact Match (%)"]]
            st.bar_chart(chart_data)

            with st.expander("📥 ดาวน์โหลดรายงาน Backtest"):
                st.download_button(
                    "ดาวน์โหลดสรุป Backtest + เลขทำนาย CSV",
                    df_bt_detail.to_csv(index=False).encode("utf-8-sig"),
                    file_name=f"backtest_{backtest_day}_with_predictions.csv",
                    mime="text/csv"
                )

# ==========================================
# 9. SETTINGS PAGE
# ==========================================
elif menu == "9. ตั้งค่าน้ำหนัก AI (Settings)":
    st.title("⚙️ ตั้งค่าน้ำหนัก AI (Weight Settings)")
    w_f = st.slider("Formula Weight", 0.1, 2.0, st.session_state.ai_settings["formula_weight"])
    w_c = st.slider("Cross Weight", 0.1, 2.0, st.session_state.ai_settings["cross_weight"])
    
    if st.button("บันทึกค่าน้ำหนัก"):
        st.session_state.ai_settings["formula_weight"] = w_f
        st.session_state.ai_settings["cross_weight"] = w_c
        st.success("✅ บันทึกค่าน้ำหนักใหม่เรียบร้อย!")
