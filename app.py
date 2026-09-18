import base64
import datetime
import json
import os
import random
import time
import urllib.parse
import requests
import streamlit as st

LOGO_PATH = "logo.png"
has_logo = os.path.exists(LOGO_PATH)

st.set_page_config(
    page_title="Omega CBT - Competitive Exam Portal",
    page_icon=LOGO_PATH if has_logo else "🎯",
    layout="wide",
)

# Custom CSS for Professional Floating Navigation Bar & Pull-to-Refresh Block
st.markdown(
    """
    <style>
        /* Prevent elastic bounce / pull-to-refresh on mobile */
        html, body {
            overscroll-behavior-y: none;
        }
        
        /* Floating Quick Navigation Panel for Test Screen */
        .floating-nav {
            position: fixed;
            right: 15px;
            bottom: 80px;
            z-index: 999999;
            background: rgba(15, 23, 42, 0.9);
            padding: 10px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.4);
            display: flex;
            flex-direction: column;
            gap: 8px;
            border: 1px solid rgba(255,255,255,0.2);
        }
        .floating-nav a {
            background: #2563eb;
            color: white;
            padding: 8px 12px;
            border-radius: 8px;
            text-align: center;
            font-size: 14px;
            font-weight: bold;
            text-decoration: none;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        .floating-nav a:hover {
            background: #1d4ed8;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

if has_logo:
    try:
        with open(LOGO_PATH, "rb") as _img_f:
            _b64_icon = base64.b64encode(_img_f.read()).decode("utf-8")
        st.markdown(
            f"""
            <head>
                <link rel="icon" type="image/png" href="data:image/png;base64,{_b64_icon}">
                <link rel="apple-touch-icon" href="data:image/png;base64,{_b64_icon}">
            </head>
            """,
            unsafe_allow_html=True,
        )
    except Exception:
        pass

DATA_FILE = "questions.json"
USERS_FILE = "omega_users.json"
NOTICE_FILE = "omega_notice.json"
CONFIG_FILE = "omega_config.json"
SHEETDB_API_URL = "https://sheetdb.io/api/v1/ptx6z420d876c"
MERCHANT_UPI_ID = "soumodeeps53-2@oksbi"

VIP_ADMIN_EMAILS = [
    "admin@omegacbt.com",
    "soumodeep@omegacbt.com",
]

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
        r = requests.post(
            SHEETDB_API_URL,
            json={"data": [data_dict]},
            headers={"Content-Type": "application/json"},
            timeout=8,
        )
        return r.status_code in [200, 201]
    except Exception:
        return False

def load_data(filename, default_val):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                d = json.load(f)
                if isinstance(d, list) and len(d) > 0:
                    for item in d:
                        if item.get("subject") == "GK GS":
                            item["subject"] = "GK / GS"
                    return d
                elif isinstance(d, dict):
                    return d
                return default_val
            except Exception:
                return default_val
    return default_val

def save_data(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def show_question_image(img_ref):
    if not img_ref:
        return
    if img_ref.startswith("http://") or img_ref.startswith("https://"):
        st.image(img_ref, width=380)
    elif os.path.exists(img_ref):
        st.image(img_ref, width=380)

if "questions" not in st.session_state:
    st.session_state.questions = load_data(DATA_FILE, DEFAULT_QUESTIONS)
if "users" not in st.session_state:
    st.session_state.users = load_data(USERS_FILE, {})
if "config" not in st.session_state:
    st.session_state.config = load_data(CONFIG_FILE, {"admin_pin": "omega999"})
if "notice_data" not in st.session_state:
    st.session_state.notice_data = load_data(
        NOTICE_FILE,
        {"id": 1, "text": "Welcome to Omega CBT! Practice daily.", "date": str(datetime.date.today())},
    )
if "last_read_notice_id" not in st.session_state:
    st.session_state.last_read_notice_id = 0
if "test_started" not in st.session_state:
    st.session_state.test_started = False
if "test_submitted" not in st.session_state:
    st.session_state.test_submitted = False
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}

for q in st.session_state.questions:
    if q.get("subject") == "GK GS":
        q["subject"] = "GK / GS"

# Header Branding
if has_logo:
    col_l, col_t = st.columns([1, 7])
    with col_l:
        st.image(LOGO_PATH, width=80)
    with col_t:
        st.title("Omega CBT")
        st.markdown("**Dedicated Competitive Exam Portal (SSC JE / RRB JE | Technical & Non-Tech)**")
else:
    st.title("🎯 Omega CBT")
    st.markdown("**Dedicated Competitive Exam Portal (SSC JE / RRB JE | Technical & Non-Tech)**")

# Dynamic Notice Banner
cur_notice = st.session_state.notice_data
is_new_notice = st.session_state.last_read_notice_id < cur_notice.get("id", 1)

if is_new_notice:
    st.markdown(
        f"""
        <div style="background:#b91c1c;padding:12px 18px;border-radius:8px;border:1px solid #f87171;color:#ffffff;font-weight:bold;margin-bottom:12px;">
            🔴 NEW NOTICE ({cur_notice.get('date')}): Check notice board below!
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
        <div style="background:#14532d;padding:10px 18px;border-radius:8px;border:1px solid #22c55e;color:#86efac;font-weight:500;margin-bottom:12px;">
            🟢 Notice Board (All Caught Up)
        </div>
        """,
        unsafe_allow_html=True,
    )

with st.expander("📢 View Notice Board"):
    st.info(f"**Date:** {cur_notice.get('date')}\n\n{cur_notice.get('text')}")
    if is_new_notice:
        if st.button("Mark as Read"):
            st.session_state.last_read_notice_id = cur_notice.get("id", 1)
            st.rerun()

st.markdown("---")

# Student Access Control
st.sidebar.header("👤 Profile & Access")
user_email = st.sidebar.text_input("Enter Email / Student ID:", "student@omegacbt.com")
today = datetime.date.today()
today_str = today.isoformat()
can_access_test = False

if user_email:
    clean_email = user_email.strip().lower()
    
    if clean_email in VIP_ADMIN_EMAILS:
        can_access_test = True
        st.sidebar.success("👑 Admin / VIP Lifetime Access")
    else:
        if clean_email not in st.session_state.users:
            st.session_state.users[clean_email] = {
                "trial_end": (today + datetime.timedelta(days=7)).isoformat(),
                "sub_end": None,
                "is_subscribed": False,
            }
            save_data(USERS_FILE, st.session_state.users)

        u_info = st.session_state.users[clean_email]
        if u_info.get("is_subscribed") and u_info.get("sub_end"):
            sub_end = datetime.date.fromisoformat(u_info["sub_end"])
            days_left = (sub_end - today).days
            if days_left >= 0:
                can_access_test = True
                if days_left <= 2:
                    st.sidebar.warning(f"Pass expiring in {days_left} day(s)!")
                else:
                    st.sidebar.success(f"Pass Active till {u_info['sub_end']}")
            else:
                u_info["is_subscribed"] = False
                save_data(USERS_FILE, st.session_state.users)
                st.sidebar.error("Pass Expired! Renew for Rs 10.")
        else:
            trial_end = datetime.date.fromisoformat(u_info.get("trial_end", today_str))
            days_trial = (trial_end - today).days
            if days_trial >= 0:
                can_access_test = True
                st.sidebar.info(f"Free Trial: {days_trial} days left")
            else:
                st.sidebar.error("Trial Ended! Get Rs 10 Pass.")

st.sidebar.header("🧭 Menu")
app_mode = st.sidebar.radio(
    "Choose Mode:",
    ["Give Mock Test", "Community Q&A Box", "Subscription (Rs 10/Month)"],
)

current_admin_pin = st.session_state.config.get("admin_pin", "omega999")

with st.sidebar.expander("🔒 Admin Control"):
    if st.text_input("Pin:", type="password") == current_admin_pin:
        st.success("Admin Verified!")
        
        st.markdown("---")
        st.subheader("🔑 Change Admin PIN")
        new_pin_input = st.text_input("Enter New PIN:", type="password")
        if st.button("Update PIN"):
            if len(new_pin_input.strip()) >= 4:
                st.session_state.config["admin_pin"] = new_pin_input.strip()
                save_data(CONFIG_FILE, st.session_state.config)
                st.success("PIN Updated Successfully!")
                st.rerun()
            else:
                st.warning("PIN must be at least 4 characters long.")

        st.markdown("---")
        st.subheader("⚡ Manual Student Bypass")
        target_student = st.text_input("Student Email to Approve:")
        pass_duration = st.selectbox("Grant Validity:", [30, 90, 365], format_func=lambda x: f"{x} Days")
        
        if st.button("Unlock Student Pass"):
            t_email = target_student.strip().lower()
            if t_email:
                exp_date = (today + datetime.timedelta(days=pass_duration)).isoformat()
                if t_email not in st.session_state.users:
                    st.session_state.users[t_email] = {}
                st.session_state.users[t_email]["is_subscribed"] = True
                st.session_state.users[t_email]["sub_end"] = exp_date
                st.session_state.users[t_email]["last_utr"] = "MANUAL_ADMIN_BYPASS"
                save_data(USERS_FILE, st.session_state.users)
                st.success(f"Unlocked {t_email} for {pass_duration} days!")
                st.rerun()
            else:
                st.warning("Please enter valid student email.")

        st.markdown("---")
        st.subheader("📢 Announcement")
        nt = st.text_area("Write Notice:")
        if st.button("Publish Notice"):
            if nt.strip():
                nid = cur_notice.get("id", 0) + 1
                un = {"id": nid, "text": nt.strip(), "date": today_str}
                st.session_state.notice_data = un
                save_data(NOTICE_FILE, un)
                st.session_state.last_read_notice_id = 0
                st.success("Notice Published Live!")
                st.rerun()

CORE_SUBS = [
    "Electrical Engineering",
    "Civil Engineering",
    "Mechanical Engineering",
    "Reasoning",
    "Mathematics",
    "GK / GS",
]
ALL_SUBJECTS = sorted([s for s in CORE_SUBS])

# 1. MOCK TEST MODE
if app_mode == "Give Mock Test":
    st.header("📝 Custom Mixed Mock Test")
    if not can_access_test:
        st.error("Access Locked! Please renew your Rs 10 Monthly Pass from the sidebar.")
    elif not st.session_state.questions:
        st.warning("Question Bank is empty!")
    elif not st.session_state.test_started and not st.session_state.test_submitted:
        st.info(f"📊 Available Questions in Bank: {len(st.session_state.questions)}")
        c1, c2 = st.columns(2)
        with c1:
            sel_subs = st.multiselect(
                "Select Subjects:",
                ALL_SUBJECTS,
                default=["Electrical Engineering"] if "Electrical Engineering" in ALL_SUBJECTS else [ALL_SUBJECTS[0]],
            )
        with c2:
            avail_q = [q for q in st.session_state.questions if q.get("subject") in sel_subs]
            tot = len(avail_q)
            
            if tot > 0:
                max_val = min(100, tot)
                init_val = min(10, max_val)
                num_q = st.slider("Number of Questions:", min_value=1, max_value=max_val, value=init_val)
            else:
                st.warning("No questions available for chosen subjects.")
                num_q = 0

        total_sec = num_q * 35
        if num_q > 0:
            st.write(f"⏱️ **Total Time:** {total_sec // 60} Min {total_sec % 60} Sec ({num_q} Qs × 35s)")

        if st.button("🚀 Start Test", disabled=(num_q == 0)):
            if avail_q:
                st.session_state.test_started = True
                st.session_state.test_submitted = False
                st.session_state.test_questions = random.sample(avail_q, min(tot, num_q))
                st.session_state.start_time = time.time()
                st.session_state.duration_seconds = total_sec
                st.session_state.user_answers = {}
                st.rerun()
            else:
                st.error("No questions found in selected subjects.")

    elif st.session_state.test_started and not st.session_state.test_submitted:
        # Floating Quick Scroll Bar on the right side of the screen
        st.markdown(
            """
            <div class="floating-nav">
                <a href="#top" title="Top">⬆️ Top</a>
                <a href="#bottom" title="Bottom">⬇️ End</a>
            </div>
            <div id="top"></div>
            """,
            unsafe_allow_html=True,
        )

        rem = max(0, int(st.session_state.duration_seconds - (time.time() - st.session_state.start_time)))
        st.markdown(f"**Total Questions: {len(st.session_state.test_questions)} | ⏱️ Time Left: {rem // 60:02d}:{rem % 60:02d}**")
        if rem == 0:
            st.session_state.test_started = False
            st.session_state.test_submitted = True
            st.rerun()

        for idx, q in enumerate(st.session_state.test_questions):
            st.markdown(f"**Q{idx+1}: [{q.get('subject')}]** {q['question']}")
            
            show_question_image(q.get("image_path"))

            raw_opts = q.get("options") or [q.get("opt1"), q.get("opt2"), q.get("opt3"), q.get("opt4")]
            
            clear_label = "-- Clear Selection (Unanswered) --"
            opts = [clear_label] + raw_opts
            
            cur_ch = st.session_state.user_answers.get(idx)
            default_idx = opts.index(cur_ch) if cur_ch in opts else 0
            
            sel = st.radio(
                f"Opt_{idx}:",
                opts,
                index=default_idx,
                key=f"ans_{idx}",
                label_visibility="collapsed",
            )
            
            if sel == clear_label:
                st.session_state.user_answers[idx] = None
            else:
                st.session_state.user_answers[idx] = sel
                
            st.markdown("---")

        st.markdown('<div id="bottom"></div>', unsafe_allow_html=True)

        c1, c2 = st.columns([2, 1])
        if c1.button("Final Submit Test", type="primary"):
            st.session_state.test_started = False
            st.session_state.test_submitted = True
            st.rerun()
        if c2.button("Quit Test"):
            st.session_state.test_started = False
            st.rerun()

    elif st.session_state.test_submitted:
        st.subheader("📊 Result & Scorecard")
        score, correct, wrong, unattempted, mistakes = 0.0, 0, 0, 0, []
        for idx, q in enumerate(st.session_state.test_questions):
            ua = st.session_state.user_answers.get(idx)
            ca = q.get("correct_option") or q.get("answer")
            if not ua:
                unattempted += 1
            elif ua == ca:
                correct += 1
                score += 1.0
            else:
                wrong += 1
                score -= 0.25
                mistakes.append((q, ua, ca))

        st.metric(label="Net Score (-0.25 negative)", value=f"{score:.2f} Marks")
        st.write(f"✅ Correct: {correct} | ❌ Wrong: {wrong} | ⚪ Skipped: {unattempted}")

        if mistakes:
            st.subheader("🔍 Review Mistakes")
            for mq, mua, mca in mistakes:
                st.error(f"**Q:** {mq['question']}")
                show_question_image(mq.get("image_path"))
                st.write(f"❌ Your Answer: `{mua}` | ✅ Correct Answer: `{mca}`")
                st.markdown("---")

        if st.button("Start New Test"):
            st.session_state.test_started = False
            st.session_state.test_submitted = False
            st.rerun()

# 2. COMMUNITY Q&A MODE (DIRECT TO GOOGLE SHEET)
elif app_mode == "Community Q&A Box":
    st.header("📥 Submit Question to Admin")
    st.markdown("Community questions are sent to admin for review before adding to test bank.")
    with st.form("comm_form", clear_on_submit=True):
        csub = st.selectbox("Subject:", ALL_SUBJECTS)
        cq = st.text_area("Question Text*")
        ca = st.text_input("Correct Answer (Optional)")
        cname = st.text_input("Your Name (Optional)")
        if st.form_submit_button("Submit Question"):
            if cq.strip():
                data = {"Subject": csub, "Question": cq.strip(), "Answer": ca.strip() or "Pending", "Submitted_By": cname.strip() or "Student"}
                if send_question_to_sheet(data):
                    st.success("Question submitted successfully for review!")
                else:
                    st.warning("Submission failed, please try again.")
            else:
                st.error("Question text cannot be empty!")

# 3. SUBSCRIPTION & ₹10 UPI GATEWAY
elif app_mode == "Subscription (Rs 10/Month)":
    st.header("💳 Omega CBT 1-Month Pass")
    u_info = st.session_state.users.get(user_email.strip().lower(), {})
    st.info(f"User ID: `{user_email}` | Status: `{'Active' if u_info.get('is_subscribed') else 'Inactive'}` | Valid Till: `{u_info.get('sub_end', 'N/A')}`")

    upi_uri_clean = f"upi://pay?pa={MERCHANT_UPI_ID}&am=10&cu=INR"
    qr_api = f"https://api.qrserver.com/v1/create-qr-code/?size=240x240&data={urllib.parse.quote(upi_uri_clean)}"

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Step 1: Scan & Pay ₹10")
        st.image(qr_api, width=220, caption="Scan using GPay / PhonePe / Paytm / BHIM")
        st.markdown("**Official UPI ID:**")
        st.code(MERCHANT_UPI_ID, language="text")
        st.caption("QR code scan karke ya UPI ID copy karke transfer karein.")

    with col2:
        st.subheader("Step 2: Instant Activation")
        with st.form("pay_verify_form"):
            utr = st.text_input("Enter 12-Digit UTR / Transaction No.:")
            if st.form_submit_button("Verify & Unlock"):
                if len(utr.strip()) >= 6:
                    exp = (today + datetime.timedelta(days=30)).isoformat()
                    u_info["is_subscribed"] = True
                    u_info["sub_end"] = exp
                    u_info["last_utr"] = utr.strip()
                    save_data(USERS_FILE, st.session_state.users)
                    st.balloons()
                    st.success(f"Pass Activated! Valid till {exp}")
                    st.rerun()
                else:
                    st.error("Please enter a valid Transaction / UTR number.")
                       
