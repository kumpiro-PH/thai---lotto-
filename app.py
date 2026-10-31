import streamlit as st
import pandas as pd
from collections import Counter
from datetime import datetime

# ============================================================
# LAO AI PROFESSIONAL v4.0 - STREAMLIT FREQUENCY ANALYSIS
# ใช้สูตรเดิมจาก LAO AI PROFESSIONAL v4.0 FINAL
# 15 สูตร: Formula 1-14 + Formula Neighbor
# ============================================================

st.set_page_config(
    page_title="LAO AI PROFESSIONAL v4.0 - Formula Frequency",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 LAO AI PROFESSIONAL v4.0")
st.caption("15 Formula Frequency Analysis | Streamlit Edition")

DAILY_NUMBERS = {
    "Monday": "056787",
    "Tuesday": "657872",
    "Wednesday": "211628",
    "Thursday": "897693",
    "Friday": "305687",
    "Saturday": "7890123",
    "Sunday": "8901234",
}
DAY_THAI = {
    "Monday": "วันจันทร์",
    "Tuesday": "วันอังคาร",
    "Wednesday": "วันพุธ",
    "Thursday": "วันพฤหัสบดี",
    "Friday": "วันศุกร์",
    "Saturday": "วันเสาร์",
    "Sunday": "วันอาทิตย์",
}


def formula1(number):
    a, b, c, d, e, f = map(int, number)
    value = ((a+b+c)*(d+e+f)+(a*f)+(c*e)) % 10000
    result = f"{value:04d}"
    return formula5(number) if result == "0000" else result


def formula2(number):
    a, b, c, d, e, f = map(int, number)
    return f"{((a*b)+(c*d)+(e*f)) % 10000:04d}"


def formula3(number):
    return f"{(sum(map(int, number))*111) % 10000:04d}"


def formula4(number):
    a, b, c, d, e, f = map(int, number)
    value = ((a+b+c)*(d+e+f)) % 10000
    result = f"{value:04d}"
    return formula5(number) if result == "0000" else result


def formula5(number):
    digits = list(map(int, number))
    score = Counter()
    counter = Counter(digits)

    for digit, count in counter.items():
        score[digit] += count * 5

    for i in range(len(digits)-1):
        score[(digits[i] + digits[i+1]) % 10] += 2

    for i in range(len(digits)-1):
        score[(digits[i] * digits[i+1]) % 10] += 2

    for i in range(len(digits)-1):
        score[abs(digits[i] - digits[i+1])] += 1

    ranking = sorted(score.items(), key=lambda x: (-x[1], x[0]))
    return "".join(str(d) for d, _ in ranking[:4]).zfill(4)


def formula6(number):
    a, b, c, d, e, f = map(int, number)
    return f"{((a+c+e)*(b+d+f)) % 10000:04d}"


def formula7(number):
    a, b, c, d, e, f = map(int, number)
    return f"{((a*10+b)+(e*10+f)) % 10000:04d}"


def formula8(number):
    return f"{(sum(map(int, number))*123) % 10000:04d}"


def formula9(number):
    a, b, c, d, e, f = map(int, number)
    return f"{abs((a*100+b*10+c)-(d*100+e*10+f)) % 10000:04d}"


def formula10(number):
    a, b, c, d, e, f = map(int, number)
    return f"{((a*f)+(b*e)+(c*d)) % 10000:04d}"


def formula11(number):
    digits = list(map(int, number))
    results = []
    for i in range(len(digits)):
        for j in range(i+1, len(digits)):
            results.append(f"{(digits[i]*digits[j]) % 100:02d}")
    ranking = sorted(Counter(results).items(), key=lambda x: (-x[1], int(x[0])))
    if not ranking:
        return "0000"
    if len(ranking) == 1:
        return ranking[0][0] + ranking[0][0]
    return ranking[0][0] + ranking[1][0]


def formula12(number):
    _, _, _, d, e, _ = map(int, number)
    base = (d+e) % 10
    return f"{base}{(base+1)%10}{(base+2)%10}{(base+3)%10}"


def formula13(number):
    a, _, c, _, _, f = map(int, number)
    return f"{((a+c+f)*9) % 10000:04d}"


def formula14(number):
    f = int(number[5])
    return f"{f}{f}{(f+1)%10}{(f+1)%10}"


def formula_neighbor(number):
    pos4, pos6 = int(number[3]), int(number[5])
    front = (pos6-1) % 10
    back = (pos4+2) % 10
    return f"{front}{back}{(back+1)%10}{(back+2)%10}"


FORMULAS = [
    ("Formula 1", formula1), ("Formula 2", formula2),
    ("Formula 3", formula3), ("Formula 4", formula4),
    ("Formula 5", formula5), ("Formula 6", formula6),
    ("Formula 7", formula7), ("Formula 8", formula8),
    ("Formula 9", formula9), ("Formula 10", formula10),
    ("Formula 11", formula11), ("Formula 12", formula12),
    ("Formula 13", formula13), ("Formula 14", formula14),
    ("Formula Neighbor", formula_neighbor),
]


def calculate_all(number):
    rows = []
    digits = []
    for name, func in FORMULAS:
        result = func(number)
        rows.append({"สูตร": name, "ผลลัพธ์ 4 หลัก": result})
        digits.extend(result)

    counts = Counter(digits)
    frequency = sorted(
        [(str(d), counts.get(str(d), 0)) for d in range(10)],
        key=lambda x: (-x[1], int(x[0]))
    )
    return rows, frequency, digits


def overlap_count(prediction, actual):
    """นับเลขตรงแบบไม่สนตำแหน่ง และนับเลขซ้ำตามจำนวนที่มีจริง"""
    return sum((Counter(prediction) & Counter(actual)).values())


# ------------------------- SIDEBAR -------------------------
st.sidebar.header("ตั้งค่าการคำนวณ")
base_number = st.sidebar.text_input(
    "เลขฐาน 6 หลัก",
    value="402701",
    max_chars=6
).strip()

day_options = list(DAILY_NUMBERS.keys())
today_name = datetime.now().strftime("%A")
default_day_index = day_options.index(today_name) if today_name in day_options else 0
selected_day = st.sidebar.selectbox(
    "เลือกวันประจำงวด",
    day_options,
    index=default_day_index,
    format_func=lambda x: f"{DAY_THAI[x]} ({x})"
)
daily_number = DAILY_NUMBERS[selected_day]

actual_result = st.sidebar.text_input(
    "ผลรางวัลจริง 4 หลัก (ไม่บังคับ)",
    value="",
    max_chars=4
).strip()

run = st.sidebar.button("🚀 คำนวณผล", type="primary", use_container_width=True)

if "run_analysis" not in st.session_state:
    st.session_state.run_analysis = True
if run:
    st.session_state.run_analysis = True

if st.session_state.run_analysis:
    if len(base_number) != 6 or not base_number.isdigit():
        st.error("กรุณากรอกเลขฐานให้ครบ 6 หลัก")
        st.stop()

    if actual_result and (len(actual_result) != 4 or not actual_result.isdigit()):
        st.error("ผลรางวัลจริงต้องเป็นตัวเลข 4 หลัก หรือเว้นว่างไว้")
        st.stop()

    rows, frequency, all_digits = calculate_all(base_number)

    st.subheader("📌 ข้อมูลที่ใช้คำนวณ")
    c1, c2, c3 = st.columns(3)
    c1.metric("เลขฐาน", base_number)
    c2.metric("เลขประจำวัน", daily_number)
    c3.metric("จำนวนสูตร", "15 สูตร")

    st.info(
        "ตามสูตรต้นฉบับ LAO AI v4.0 เลขประจำวันแสดงเป็นข้อมูลประกอบ "
        "ไม่ได้ถูกนำไปผสมกับเลขฐานก่อนคำนวณผลลัพธ์ทั้ง 15 สูตร"
    )

    st.subheader("1. ผลลัพธ์จากสูตรทั้ง 15 สูตร")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.subheader("2. ความถี่รวมจาก 15 สูตร")
    st.caption("15 สูตร × 4 หลัก = 60 หลัก นับทุกหลักเต็มจำนวน รวมเลขซ้ำ")
    freq_df = pd.DataFrame([
        {"อันดับ": i+1, "เลข": digit, "จำนวนครั้ง": count}
        for i, (digit, count) in enumerate(frequency)
    ])
    st.dataframe(freq_df, use_container_width=True, hide_index=True)

    top5 = [d for d, _ in frequency[:5]]
    top3 = [d for d, _ in frequency[:3]]
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("### 🏆 Top 5")
        st.markdown("## " + " – ".join(top5))
    with col_b:
        st.markdown("### ⭐ Top 3")
        st.markdown("## " + " – ".join(top3))

    if actual_result:
        st.subheader("3. ตรวจสอบกับผลรางวัลจริง")
        hit_rows = []
        total_hits = 0
        for row in rows:
            hit = overlap_count(row["ผลลัพธ์ 4 หลัก"], actual_result)
            total_hits += hit
            hit_rows.append({
                "สูตร": row["สูตร"],
                "ผลสูตร": row["ผลลัพธ์ 4 หลัก"],
                "ผลจริง": actual_result,
                "เลขตรง (ไม่สนตำแหน่ง)": hit
            })
        st.dataframe(pd.DataFrame(hit_rows), use_container_width=True, hide_index=True)
        st.metric("จำนวนหลักที่ตรงรวมทุกสูตร", f"{total_hits} / 60")
        top5_hits = overlap_count("".join(top5), actual_result)
        top3_hits = overlap_count("".join(top3), actual_result)
        x, y = st.columns(2)
        x.metric("เลข Top 5 ตรงกับผลจริง", f"{top5_hits} / 4")
        y.metric("เลข Top 3 ตรงกับผลจริง", f"{top3_hits} / 4")

    st.caption(
        "หมายเหตุ: ความถี่เป็นเพียงสถิติการปรากฏในผลลัพธ์ของสูตร "
        "ไม่ใช่ความน่าจะเป็นหรือการรับประกันผลรางวัล"
    )
