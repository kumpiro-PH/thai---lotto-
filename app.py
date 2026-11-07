import streamlit as st
import pandas as pd
import os
from collections import Counter

# ==========================================
# 1. PAGE CONFIG & CUSTOM CSS (Sky Blue Theme)
# ==========================================
st.set_page_config(
    page_title="THAI AI PROFESSIONAL v7.9 - Auto CSV Master",
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

VERSION = "THAI AI PROFESSIONAL v7.9 MASTER AI - Auto Target Sync"

# ==========================================
# 2. SESSION STATE & DAILY NUMBERS INITIALIZATION
# ==========================================
if "history" not in st.session_state:
    st.session_state.history = []

if "uploaded_csvs" not in st.session_state:
    st.session_state.uploaded_csvs = {}

if "ai_settings" not in st.session_state:
    st.session_state.ai_settings = {
        "formula_weight": 1.00,
        "cross_weight": 0.90,
        "daily_weight": 1.50,
        "echo_weight": 0.70,
        "recovery_weight": 0.60,
    }

DAILY_NUMBERS = {
    "Monday":    "462793",
    "Tuesday":   "639170",
    "Wednesday": "257308",
    "Thursday":  "176904",
    "Friday":    "730259",
    "Saturday":  "895260",
    "Sunday":    "062341",
}

# ==========================================
# 3. CSV LOADER FUNCTION (จัดเรียงให้งวดล่าสุดขึ้นบนสุด)
# ==========================================
def load_history_by_day(day_name):
    if day_name in st.session_state.uploaded_csvs:
        df = st.session_state.uploaded_csvs[day_name]
    else:
        file_map = {
            "Monday": "thai_lottery_monday_history.csv",
            "Tuesday": "thai_lottery_tuesday_history.csv",
            "Wednesday": "thai_lottery_wednesday_history.csv",
            "Thursday": "thai_lottery_thursday_history.csv",
            "Friday": "thai_lottery_friday_history.csv",
            "Saturday": "thai_lottery_saturday_history.csv",
            "Sunday": "thai_lottery_sunday_history.csv"
        }
        filename = file_map.get(day_name)
        if filename and os.path.exists(filename):
            try:
                df = pd.read_csv(filename)
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาดในการอ่านไฟล์ {filename}: {e}")
                return []
        else:
            return []

    # 🌟 กลับลำดับให้งวดล่าสุด (วันที่ใหม่ที่สุด) อยู่แถวแรกเสมอ
    if not df.empty:
        df = df.iloc[::-1].reset_index(drop=True)

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

def analyse_formulas_by_day(mode="back2", target_day=None, daily_number="-"):
    results = []
    target_history = st.session_state.history
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
# 5. STREAMLIT UI SIDEBAR NAVIGATION
# ==========================================
st.sidebar.title("🧠 MENU CONTROL")
menu = st.sidebar.radio("เลือกหน้าเมนู:", [
    "8. All-in-One Master Report",
    "1. เพิ่ม/จัดการประวัติหวย",
    "10. รันระบบทดสอบย้อนหลัง (Backtest)",
    "9. ตั้งค่าน้ำหนัก AI (Settings)"
])

st.sidebar.markdown("---")
st.sidebar.markdown("### 📡 CSV Status Monitor")

# ==========================================
# 6. ALL-IN-ONE MASTER REPORT PAGE
# ==========================================
if menu == "8. All-in-One Master Report":
    st.title("🏆 ALL-IN-ONE MASTER REPORT")
    st.caption(f"เวอร์ชัน: {VERSION}")
    
    # 🌟 ฟังก์ชันอัปเดตเลขฐานอัตโนมัติทันทีที่เปลี่ยนวันใน Selectbox
    def on_day_change():
        selected_day = st.session_state.selected_day_box
        history_data = load_history_by_day(selected_day)
        if history_data:
            st.session_state.target_number_input = history_data[0]["first"]

    col1, col2 = st.columns(2)
    with col1:
        day_choice = st.selectbox(
            "📅 เลือกวันประจำงวด:", 
            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            key="selected_day_box",
            on_change=on_day_change
        )
        
        st.session_state.history = load_history_by_day(day_choice)
        daily_number = DAILY_NUMBERS.get(day_choice, "462793")

    with col2:
        # ดึงเลขงวดล่าสุดจากแถวแรกของ CSV ประจำวันนั้นๆ มาแสดงเป็นค่าตั้งต้น
        initial_target = st.session_state.history[0]["first"] if st.session_state.history else "423224"
        
        target_number = st.text_input(
            "📌 เลขฐาน 6 หลักงวดล่าสุด:", 
            value=initial_target, 
            max_chars=6,
            key="target_number_input"
        )

    if not st.session_state.history:
        st.warning(f"⚠️ ไม่พบข้อมูลประวัติสำหรับวัน {day_choice} กรุณาตรวจสอบไฟล์ CSV หรือเพิ่มข้อมูลในเมนู 'เพิ่ม/จัดการประวัติหวย'")
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
                        วัน: {day_choice}   |   เลขฐาน: {target_number}   |   Daily Number: {daily_number}   |   จำนวนสูตร: 15   |   จำนวนหลัก: {frequency_total}
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
                    rem_text = "  |  ".join([f"{d} = {frequency_counts.get(d, 0)} ครั้ง" for d in remaining])
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
# 7. MANAGEMENT HISTORY & ADD DATA PAGE
# ==========================================
elif menu == "1. เพิ่ม/จัดการประวัติหวย":
    st.title("📚 เพิ่ม / จัดการประวัติและอัปเดตข้อมูลหวย")
    day_upload = st.selectbox("เลือกวันประจำงวด:", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
    
    with st.expander("➕ เพิ่มข้อมูลงวดใหม่ (Add New Draw)", expanded=True):
        with st.form("add_form"):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                new_date = st.text_input("งวดวันที่ (เช่น 01/11/2569)", value="01/11/2569")
                new_first = st.text_input("รางวัลที่ 1 (6 หลัก)", max_chars=6, value="")
                new_back2 = st.text_input("เลขท้าย 2 ตัว", max_chars=2, value="")
            with col_f2:
                new_f3_1 = st.text_input("เลขหน้า 3 ตัว (1)", max_chars=3, value="")
                new_f3_2 = st.text_input("เลขหน้า 3 ตัว (2)", max_chars=3, value="")
                new_l3_1 = st.text_input("เลขท้าย 3 ตัว (1)", max_chars=3, value="")
                new_l3_2 = st.text_input("เลขท้าย 3 ตัว (2)", max_chars=3, value="")
            
            submitted = st.form_submit_button("💾 บันทึกข้อมูลงวดใหม่", type="primary")
            if submitted:
                if len(new_first) != 6 or not new_first.isdigit():
                    st.error("❌ กรุณากรอกรางวัลที่ 1 เป็นตัวเลข 6 หลักให้ถูกต้อง")
                else:
                    if day_upload in st.session_state.uploaded_csvs:
                        df_current = st.session_state.uploaded_csvs[day_upload]
                    else:
                        file_map_inner = {
                            "Monday": "thai_lottery_monday_history.csv", "Tuesday": "thai_lottery_tuesday_history.csv",
                            "Wednesday": "thai_lottery_wednesday_history.csv", "Thursday": "thai_lottery_thursday_history.csv",
                            "Friday": "thai_lottery_friday_history.csv", "Saturday": "thai_lottery_saturday_history.csv",
                            "Sunday": "thai_lottery_sunday_history.csv"
                        }
                        f_name = file_map_inner.get(day_upload)
                        if f_name and os.path.exists(f_name):
                            df_current = pd.read_csv(f_name)
                        else:
                            df_current = pd.DataFrame(columns=['date_be', 'first_prize', 'last_2_digits', 'front_3_1', 'front_3_2', 'last_3_1', 'last_3_2'])

                    new_row = pd.DataFrame([{
                        'date_be': new_date,
                        'first_prize': new_first,
                        'last_2_digits': new_back2,
                        'front_3_1': new_f3_1,
                        'front_3_2': new_f3_2,
                        'last_3_1': new_l3_1,
                        'last_3_2': new_l3_2
                    }])
                    
                    df_updated = pd.concat([new_row, df_current], ignore_index=True)
                    st.session_state.uploaded_csvs[day_upload] = df_updated
                    st.success(f"✅ บันทึกข้อมูลงวด {new_date} ของวัน {day_upload} เรียบร้อยแล้ว!")

    st.markdown("---")
    
    uploaded_file = st.file_uploader(f"📂 หรืออัปโหลดไฟล์ CSV ทั้งชุดสำหรับวัน {day_upload}", type=["csv"])
    if uploaded_file is not None:
        try:
            df_up = pd.read_csv(uploaded_file)
            st.session_state.uploaded_csvs[day_upload] = df_up
            st.success(f"✅ อัปโหลดไฟล์ CSV ของวัน {day_upload} สำเร็จ!")
        except Exception as e:
            st.error(f"❌ อ่านไฟล์ไม่สำเร็จ: {e}")

    current_history = load_history_by_day(day_upload)
    if current_history:
        st.subheader(f"📋 ข้อมูลประวัติปัจจุบันของวัน: {day_upload}")
        st.dataframe(pd.DataFrame(current_history), use_container_width=True)
    else:
        st.info(f"ยังไม่มีข้อมูลประวัติของวัน {day_upload}")

# ==========================================
# 8. BACKTEST PAGE
# ==========================================
elif menu == "10. รันระบบทดสอบย้อนหลัง (Backtest)":
    st.title("📈 รันระบบทดสอบย้อนหลัง (Backtest Engine)")
    selected_backtest_day = st.selectbox(
        "📅 เลือกวันสำหรับการทำ Backtest:", 
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    )
    
    st.session_state.history = load_history_by_day(selected_backtest_day)
    daily_num_arg = DAILY_NUMBERS.get(selected_backtest_day, "-")

    if len(st.session_state.history) < 2:
        st.warning(f"⚠️ ข้อมูลประวัติของวัน {selected_backtest_day} มีไม่เพียงพอสำหรับการทำ Backtest")
    else:
        st.info(f"ประมวลผล Backtest จากวัน {selected_backtest_day} (จำนวน {len(st.session_state.history)} งวด)")
        res_b2 = analyse_formulas_by_day("back2", target_day=selected_backtest_day, daily_number=daily_num_arg)
        st.subheader(f"🏆 Top 3 สูตรเจาะตำแหน่งยอดเยี่ยม ({selected_backtest_day})")
        for rank, item in enumerate(res_b2[:3], 1):
            st.write(f"**อันดับ {rank}: {item[3]}** | คะแนนคูณน้ำหนัก: {item[0]:.2f} | ความแม่นยำรวม: {item[2]:.2f}%")

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
