import datetime
import json
import os
import random
import time
import requests
import streamlit as st

# 1. Page Configuration
st.set_page_config(
    page_title="Omega CBT - Competitive Exam Portal",
    page_icon="🎯",
    layout="wide",
)

DATA_FILE = "questions.json"
USERS_FILE = "omega_users.json"
SHEETDB_API_URL = "https://sheetdb.io/api/v1/ptx6z420d876c"

# Fallback questions in case file isn't found
DEFAULT_QUESTIONS = [
    {
        "subject": "Electrical Engineering",
        "question": "Which motor is preferred for electric traction due to high starting torque?",
        "options": ["DC Series Motor", "DC Shunt Motor", "Synchronous Motor", "Stepper Motor"],
        "correct_option": "DC Series Motor",
        "image_path": None,
    },
    {
        "subject": "Electrical Engineering",
        "question": "The Buchholz relay is used for the protection of:",
        "options": ["Transformers against internal faults", "Transmission lines against lightning", "Generators against overspeed", "Induction motors against overloading"],
        "correct_option": "Transformers against internal faults",
        "image_path": None,
    }
]


def send_question_to_sheet(data_dict):
    try:
        response = requests.post(
            SHEETDB_API_URL,
            json={"data": [data_dict]},
            headers={"Content-Type": "application/json"},
            timeout=8,
        )
        return response.status_code in [200, 201]
    except Exception:
        return False


def load_data(filename, default_val):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    return data
                return default_val
            except json.JSONDecodeError:
                return default_val
    return default_val


def save_data(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# Initialize Session States
if "questions" not in st.session_state:
    st.session_state.questions = load_data(DATA_FILE, DEFAULT_QUESTIONS)

if "users" not in st.session_state:
    st.session_state.users = load_data(USERS_FILE, {})

if "test_started" not in st.session_state:
    st.session_state.test_started = False

if "test_submitted" not in st.session_state:
    st.session_state.test_submitted = False

if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}

# --- HEADER BRANDING ---
st.title("🎯 Omega CBT")
st.markdown("**Dedicated Competitive Exam Portal (SSC JE / RRB JE | Technical & Non-Tech)**")
st.markdown("---")

# --- USER IDENTIFICATION & 7-DAY TRIAL SYSTEM ---
st.sidebar.header("👤 Student Profile & Access")
user_email = st.sidebar.text_input("Enter Your Email / Student ID:", "student@omegacbt.com")

today_date = datetime.date.today().isoformat()

if user_email:
    if user_email not in st.session_state.users:
        expiry_date = (datetime.date.today() + datetime.timedelta(days=7)).isoformat()
        st.session_state.users[user_email] = {
            "trial_end": expiry_date,
            "is_subscribed": False,
        }
        save_data(USERS_FILE, st.session_state.users)

    user_info = st.session_state.users[user_email]
    trial_end_date = user_info["trial_end"]
    is_subscribed = user_info["is_subscribed"]
    is_trial_active = today_date <= trial_end_date

    if is_subscribed:
        st.sidebar.success("🟢 Status: Premium Active (Unlimited Access)")
    elif is_trial_active:
        st.sidebar.info(f"⏳ Status: Free Trial Active (Expires: {trial_end_date})")
    else:
        st.sidebar.error("🔴 Status: Free Trial Expired!")
        st.sidebar.warning("Please pay ₹10 to activate 1-Month Unlimited Access.")

# --- SIDEBAR NAVIGATION ---
st.sidebar.header("🧭 Navigation Menu")
app_mode = st.sidebar.radio(
    "Choose Mode:",
    [
        "📝 Give Mock Test (Custom Mix)",
        "➕ Manage & Add Questions",
        "📥 Community Q&A Box",
        "💳 Subscription (₹10/Month)",
    ],
)

TECHNICAL_BRANCHES = [
    "Electrical Engineering",
    "Mechanical Engineering",
    "Civil Engineering",
]
NON_TECH_SUBJECTS = ["GK / GS", "Reasoning", "Mathematics"]
ALL_SUBJECTS = TECHNICAL_BRANCHES + NON_TECH_SUBJECTS

# ==========================================
# MODE 1: GIVE MOCK TEST (LIVE TIMER + NEGATIVE MARKING)
# ==========================================
if app_mode == "📝 Give Mock Test (Custom Mix)":
    st.header("📝 Custom Mixed Mock Test")

    can_access = False
    if user_email and user_email in st.session_state.users:
        u_info = st.session_state.users[user_email]
        if u_info["is_subscribed"] or today_date <= u_info["trial_end"]:
            can_access = True

    if not can_access:
        st.error("🚫 Your 7-day free trial has expired! Please visit 'Subscription' tab to pay ₹10 and continue.")
    elif not st.session_state.questions:
        st.warning("⚠️ Question Bank is empty! Please add questions using the 'Manage & Add Questions' tab.")
    else:
        if not st.session_state.test_started and not st.session_state.test_submitted:
            st.subheader("⚙️ Test Configuration")
            col1, col2 = st.columns(2)

            with col1:
                selected_subjects = st.multiselect(
                    "Select Subjects for Your Test:",
                    ALL_SUBJECTS,
                    default=["Electrical Engineering"],
                )

            with col2:
                filtered_available = [
                    q for q in st.session_state.questions
                    if q.get("subject") in selected_subjects
                ]
                total_q_available = len(filtered_available)
                max_limit = min(100, max(1, total_q_available))
                num_questions = st.slider(
                    "Select Number of Questions (Max 100):",
                    min_value=1,
                    max_value=max_limit,
                    value=min(10, max_limit),
                )

            allocated_time_seconds = num_questions * 35
            minutes = allocated_time_seconds // 60
            seconds = allocated_time_seconds % 60

            st.info(f"⏱️ **Dynamic Time:** {minutes} Min {seconds} Sec ({num_questions} Questions × 35s)")

            if st.button("🚀 Start Test"):
                if filtered_available:
                    st.session_state.test_started = True
                    st.session_state.test_submitted = False
                    st.session_state.test_questions = random.sample(
                        filtered_available, min(len(filtered_available), num_questions)
                    )
                    st.session_state.start_time = time.time()
                    st.session_state.duration_seconds = allocated_time_seconds
                    st.session_state.user_answers = {}
                    st.rerun()
                else:
                    st.error("Selected subjects me questions available nahi hain.")

            st.markdown("---")
            with st.expander("💡 Submit / Suggest a Question for Omega CBT"):
                st.caption("आपका सवाल एडमिन रिव्यू के बाद वेरिफाई होकर टेस्ट बैंक में शामिल होगा।")
                with st.form("community_question_form_test_tab", clear_on_submit=True):
                    sub_val = st.selectbox("Subject", ALL_SUBJECTS, key="test_tab_sub")
                    q_val = st.text_area("Question Text*", placeholder="सवाल यहाँ लिखें...", key="test_tab_q")

                    col_o1, col_o2 = st.columns(2)
                    with col_o1:
                        oa = st.text_input("Option A (Optional)", key="test_tab_oa")
                        ob = st.text_input("Option B (Optional)", key="test_tab_ob")
                    with col_o2:
                        oc = st.text_input("Option C (Optional)", key="test_tab_oc")
                        od = st.text_input("Option D (Optional)", key="test_tab_od")

                    ans_val = st.text_input("Correct Answer / Solution Note (Optional)", key="test_tab_ans")
                    sender_val = st.text_input("Your Name / Telegram Handle (Optional)", key="test_tab_user")

                    btn_sub = st.form_submit_button("🚀 Submit Question to Admin")
                    if btn_sub:
                        if not q_val.strip():
                            st.error("⚠️ कृपया सवाल खाली न छोड़ें!")
                        else:
                            opts = [o.strip() for o in [oa, ob, oc, od] if o.strip()]
                            sheet_data = {
                                "Subject": sub_val,
                                "Question": q_val.strip(),
                                "Options": ", ".join(opts) if opts else "None",
                                "Answer": ans_val.strip() if ans_val.strip() else "Pending Review",
                                "Submitted_By": sender_val.strip() if sender_val.strip() else "Anonymous",
                            }
                            if send_question_to_sheet(sheet_data):
                                st.success("✅ सवाल एडमिन को सफलता से भेज दिया गया है!")
                            else:
                                st.warning("⚠️ अभी सबमिट नहीं हो सका, कृपया दोबारा प्रयास करें।")

        # Active Test Screen with Timer
        elif st.session_state.test_started and not st.session_state.test_submitted:
            elapsed = time.time() - st.session_state.start_time
            remaining_sec = max(0, int(st.session_state.duration_seconds - elapsed))

            rem_min = remaining_sec // 60
            rem_s = remaining_sec % 60

            st.markdown(
                f"""
                <div style="background-color:#1e293b; padding:10px 16px; border-radius:8px; display:flex; justify-content:space-between; align-items:center;">
                    <span style="color:#38bdf8; font-size:18px; font-weight:bold;">Total Questions: {len(st.session_state.test_questions)}</span>
                    <span style="color:{'#ef4444' if remaining_sec < 180 else '#22c55e'}; font-size:20px; font-weight:bold;">⏱️ Time Remaining: {rem_min:02d}:{rem_s:02d}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if remaining_sec == 0:
                st.warning("⚠️ Time Over! Test automatically submitted.")
                st.session_state.test_started = False
                st.session_state.test_submitted = True
                st.rerun()

            st.markdown("---")
            test_questions = st.session_state.test_questions

            for idx, q in enumerate(test_questions):
                st.markdown(f"**Q{idx+1}:** `[{q.get('subject')}]` {q['question']}")

                if q.get("image_path") and os.path.exists(q["image_path"]):
                    st.image(q["image_path"], width=350)

                if "options" in q:
                    options = q["options"]
                else:
                    options = [q.get("opt1"), q.get("opt2"), q.get("opt3"), q.get("opt4")]

                current_choice = st.session_state.user_answers.get(idx, None)
                def_idx = options.index(current_choice) if current_choice in options else None

                sel = st.radio(
                    f"Options for Q{idx+1}:",
                    options,
                    index=def_idx,
                    key=f"ans_{idx}",
                    label_visibility="collapsed",
                )
                st.session_state.user_answers[idx] = sel
                st.markdown("---")

            col_sub1, col_sub2 = st.columns([2, 1])
            with col_sub1:
                if st.button("📤 Final Submit Test", type="primary"):
                    st.session_state.test_started = False
                    st.session_state.test_submitted = True
                    st.rerun()
            with col_sub2:
                if st.button("❌ Quit Test"):
                    st.session_state.test_started = False
                    st.session_state.test_submitted = False
                    st.session_state.user_answers = {}
                    st.rerun()

        # Scorecard & Mistake Review
        elif st.session_state.test_submitted:
            st.subheader("📊 Your Scorecard & Performance")

            score = 0.0
            correct_count = 0
            wrong_count = 0
            unattempted = 0
            mistakes = []

            for idx, q in enumerate(st.session_state.test_questions):
                user_ans = st.session_state.user_answers.get(idx)
                correct_ans = q.get("correct_option") or q.get("answer")

                if not user_ans:
                    unattempted += 1
                elif user_ans == correct_ans:
                    correct_count += 1
                    score += 1.0
                else:
                    wrong_count += 1
                    score -= 0.25
                    mistakes.append((q, user_ans, correct_ans))

            st.metric(label="Net Score (with -0.25 Negative Marking)", value=f"{score:.2f} Marks")
            st.write(f"✅ **Correct:** {correct_count} | ❌ **Wrong:** {wrong_count} | ⚪ **Unattempted:** {unattempted}")

            if mistakes:
                st.markdown("---")
                st.subheader("🔍 Wrong Questions Review")
                for m_q, m_ans, c_ans in mistakes:
                    st.error(f"**Question:** {m_q['question']}")
                    st.write(f"❌ **Your Answer:** `{m_ans}`")
                    st.write(f"✅ **Correct Answer:** `{c_ans}`")
                    st.markdown("---")

            if st.button("🔄 Start New Test"):
                st.session_state.test_started = False
                st.session_state.test_submitted = False
                st.session_state.user_answers = {}
                st.rerun()

# ==========================================
# MODE 2: MANAGE & ADD QUESTIONS
# ==========================================
elif app_mode == "➕ Manage & Add Questions":
    st.header("➕ Add New Questions to Omega CBT Bank")

    with st.form("add_question_form"):
        sub = st.selectbox("Select Branch / Subject", ALL_SUBJECTS)
        q_text = st.text_area("Enter Question Text:")

        col_img1, col_img2 = st.columns(2)
        with col_img1:
            opt1 = st.text_input("Option A")
            opt2 = st.text_input("Option B")
        with col_img2:
            opt3 = st.text_input("Option C")
            opt4 = st.text_input("Option D")

        correct_ans = st.selectbox("Correct Answer", [opt1, opt2, opt3, opt4])

        uploaded_image = st.file_uploader(
            "Upload Diagram / Circuit / Figure (Optional)",
            type=["png", "jpg", "jpeg"],
        )

        submitted = st.form_submit_button("💾 Save Question")

        if submitted:
            if q_text and correct_ans:
                image_path = None
                if uploaded_image is not None:
                    os.makedirs("question_images", exist_ok=True)
                    image_path = os.path.join("question_images", uploaded_image.name)
                    with open(image_path, "wb") as f:
                        f.write(uploaded_image.getbuffer())

                new_q = {
                    "subject": sub,
                    "question": q_text,
                    "options": [opt1, opt2, opt3, opt4],
                    "correct_option": correct_ans,
                    "image_path": image_path,
                }
                st.session_state.questions.append(new_q)
                save_data(DATA_FILE, st.session_state.questions)
                st.success("✅ Question added successfully!")
            else:
                st.error("⚠️ Question text aur correct answer bharna zaroori hai.")

    st.markdown("---")
    if st.button("🗑️ Reset Question Bank to Default"):
        st.session_state.questions = list(DEFAULT_QUESTIONS)
        save_data(DATA_FILE, DEFAULT_QUESTIONS)
        st.warning("⚠️ Question bank reset!")

# ==========================================
# MODE 3: COMMUNITY Q&A BOX (CONNECTED TO GOOGLE SHEET)
# ==========================================
elif app_mode == "📥 Community Q&A Box":
    st.header("📥 Community Question Submission Box")
    st.markdown("छात्र यहाँ सवाल सबमिट कर सकते हैं। यह सीधे रिव्यू के लिए आपकी गूगल शीट में सुरक्षित होगा।")

    with st.form("community_form", clear_on_submit=True):
        c_sub = st.selectbox("Subject Category", ALL_SUBJECTS)
        c_q = st.text_area("Question Text*")

        col_a, col_b = st.columns(2)
        with col_a:
            co1 = st.text_input("Option A (Optional)")
            co2 = st.text_input("Option B (Optional)")
        with col_b:
            co3 = st.text_input("Option C (Optional)")
            co4 = st.text_input("Option D (Optional)")

        c_ans = st.text_input("Correct Answer / Solution Note (Optional)")
        c_sender = st.text_input("Your Name / Telegram Handle (Optional)")

        c_submit = st.form_submit_button("🚀 Submit to Admin")
        if c_submit:
            if not c_q.strip():
                st.error("⚠️ कृपया सवाल खाली न छोड़ें!")
            else:
                opts = [o.strip() for o in [co1, co2, co3, co4] if o.strip()]
                sheet_data = {
                    "Subject": c_sub,
                    "Question": c_q.strip(),
                    "Options": ", ".join(opts) if opts else "None",
                    "Answer": c_ans.strip() if c_ans.strip() else "Pending Review",
                    "Submitted_By": c_sender.strip() if c_sender.strip() else "Anonymous",
                }
                if send_question_to_sheet(sheet_data):
                    st.success("✅ सवाल एडमिन को सफलता से भेज दिया गया है!")
                else:
                    st.warning("⚠️ अभी सबमिट नहीं हो सका, कृपया दोबारा प्रयास करें।")

# ==========================================
# MODE 4: SUBSCRIPTION (₹10 / MONTH)
# ==========================================
elif app_mode == "💳 Subscription (₹10/Month)":
    st.header("💳 Omega CBT Premium Access")
    st.markdown("Har student ko **7-Day Free Trial** milta hai. Uske baad platform access ke liye sirf **₹10 / Month**.")

    st.info(
        f"User ID: `{user_email}`\n\n"
        f"Trial Expiry: `{st.session_state.users.get(user_email, {}).get('trial_end', 'N/A')}`"
    )

    if st.button("Pay ₹10 & Activate 1-Month Pass"):
        st.session_state.users[user_email]["is_subscribed"] = True
        save_data(USERS_FILE, st.session_state.users)
        st.balloons()
        st.success("✨ Access active for 1 Month!")
            
