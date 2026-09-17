import datetime
import json
import os
import random
import time
import urllib.parse
import requests
import streamlit as st

st.set_page_config(page_title="Omega CBT", page_icon="🎯", layout="wide")

DATA_FILE = "questions.json"
USERS_FILE = "omega_users.json"
NOTICE_FILE = "omega_notice.json"
SHEETDB_API_URL = "https://sheetdb.io/api/v1/ptx6z420d876c"
ADMIN_SECRET_PIN = "omega999"
MERCHANT_UPI_ID = "soumodeeps53-2@oksbi"

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
        r = requests.post(SHEETDB_API_URL, json={"data": [data_dict]}, headers={"Content-Type": "application/json"}, timeout=8)
        return r.status_code in [200, 201]
    except Exception:
        return False

def load_data(filename, default_val):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                d = json.load(f)
                return d if (isinstance(d, list) and len(d) > 0) or isinstance(d, dict) else default_val
            except Exception:
                return default_val
    return default_val

def save_data(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if "questions" not in st.session_state:
    st.session_state.questions = load_data(DATA_FILE, DEFAULT_QUESTIONS)
if "users" not in st.session_state:
    st.session_state.users = load_data(USERS_FILE, {})
if "notice_data" not in st.session_state:
    st.session_state.notice_data = load_data(NOTICE_FILE, {"id": 1, "text": "Welcome to Omega CBT! Practice daily.", "date": str(datetime.date.today())})
if "last_read_notice_id" not in st.session_state:
    st.session_state.last_read_notice_id = 0
if "test_started" not in st.session_state:
    st.session_state.test_started = False
if "test_submitted" not in st.session_state:
    st.session_state.test_submitted = False
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}

st.title("🎯 Omega CBT")
st.markdown("**Dedicated Competitive Exam Portal (SSC JE / RRB JE | Technical & Non-Tech)**")

# Notice Banner
cur_notice = st.session_state.notice_data
is_new_notice = st.session_state.last_read_notice_id < cur_notice.get("id", 1)

if is_new_notice:
    st.markdown(f'<div style="background:#b91c1c;padding:10px;border-radius:6px;color:#fff;font-weight:bold;">🔴 NEW NOTICE ({cur_notice.get("date")}): Check notice board below!</div>', unsafe_allow_html=True)
else:
    st.markdown('<div style="background:#14532d;padding:8px;border-radius:6px;color:#86efac;">🟢 Notice Board (All Caught Up)</div>', unsafe_allow_html=True)

with st.expander("📢 View Notice Board"):
    st.info(f"Date: {cur_notice.get('date')}\n\n{cur_notice.get('text')}")
    if is_new_notice and st.button("Mark as Read"):
        st.session_state.last_read_notice_id = cur_notice.get("id", 1)
        st.rerun()

st.markdown("---")

# User & Access Control
st.sidebar.header("👤 Profile & Access")
user_email = st.sidebar.text_input("Enter Email / Student ID:", "student@omegacbt.com")
today = datetime.date.today()
today_str = today.isoformat()
can_access_test = False

if user_email:
    if user_email not in st.session_state.users:
        st.session_state.users[user_email] = {
            "trial_end": (today + datetime.timedelta(days=7)).isoformat(),
            "sub_end": None,
            "is_subscribed": False,
        }
        save_data(USERS_FILE, st.session_state.users)

    u_info = st.session_state.users[user_email]
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
app_mode = st.sidebar.radio("Choose Mode:", ["Give Mock Test", "Manage & Add Questions", "Community Q&A Box", "Subscription (Rs 10/Month)"])

with st.sidebar.expander("🔒 Admin Control"):
    if st.text_input("Pin:", type="password") == ADMIN_SECRET_PIN:
        st.success("Verified!")
        nt = st.text_area("Write Announcement:")
        if st.button("Publish Notice"):
            if nt.strip():
                nid = cur_notice.get("id", 0) + 1
                un = {"id": nid, "text": nt.strip(), "date": today_str}
                st.session_state.notice_data = un
                save_data(NOTICE_FILE, un)
                st.session_state.last_read_notice_id = nid
                st.rerun()

CORE_SUBS = ["Electrical Engineering", "GK / GS", "Reasoning", "Mathematics", "Mechanical Engineering", "Civil Engineering", "Technical", "Non-Technical"]
ALL_SUBJECTS = sorted(list(set(CORE_SUBS + [q.get("subject") for q in st.session_state.questions if q.get("subject")])))

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
            sel_subs = st.multiselect("Select Subjects:", ALL_SUBJECTS, default=["Electrical Engineering"] if "Electrical Engineering" in ALL_SUBJECTS else [ALL_SUBJECTS[0]])
        with c2:
            avail_q = [q for q in st.session_state.questions if q.get("subject") in sel_subs]
            tot = len(avail_q)
            num_q = st.slider("Number of Questions:", min_value=1, max_value=max(1, min(100, tot)), value=min(10, max(1, tot)))

        total_sec = num_q * 35
        st.write(f"⏱️ **Total Time:** {total_sec // 60} Min {total_sec % 60} Sec ({num_q} Qs × 35s)")

        if st.button("🚀 Start Test"):
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
        rem = max(0, int(st.session_state.duration_seconds - (time.time() - st.session_state.start_time)))
        st.markdown(f"**Total Questions: {len(st.session_state.test_questions)} | ⏱️ Time Left: {rem // 60:02d}:{rem % 60:02d}**")
        if rem == 0:
            st.session_state.test_started = False
            st.session_state.test_submitted = True
            st.rerun()

        for idx, q in enumerate(st.session_state.test_questions):
            st.markdown(f"**Q{idx+1}: [{q.get('subject')}]** {q['question']}")
            opts = q.get("options") or [q.get("opt1"), q.get("opt2"), q.get("opt3"), q.get("opt4")]
            cur_ch = st.session_state.user_answers.get(idx)
            sel = st.radio(f"Opt_{idx}:", opts, index=opts.index(cur_ch) if cur_ch in opts else None, key=f"ans_{idx}", label_visibility="collapsed")
            st.session_state.user_answers[idx] = sel
            st.markdown("---")

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
                st.write(f"❌ Your Answer: `{mua}` | ✅ Correct Answer: `{mca}`")
                st.markdown("---")

        if st.button("Start New Test"):
            st.session_state.test_started = False
            st.session_state.test_submitted = False
            st.rerun()

# 2. MANAGE QUESTIONS MODE
elif app_mode == "Manage & Add Questions":
    st.header("➕ Add New Questions")
    with st.form("add_q_form"):
        sub = st.selectbox("Subject:", ALL_SUBJECTS)
        qtxt = st.text_area("Question Text:")
        o1 = st.text_input("Option A")
        o2 = st.text_input("Option B")
        o3 = st.text_input("Option C")
        o4 = st.text_input("Option D")
        ans = st.selectbox("Correct Option:", [o1, o2, o3, o4])
        if st.form_submit_button("Save Question"):
            if qtxt and ans:
                new_q = {"subject": sub, "question": qtxt, "options": [o1, o2, o3, o4], "correct_option": ans, "image_path": None}
                st.session_state.questions.append(new_q)
                save_data(DATA_FILE, st.session_state.questions)
                st.success("Question saved!")
            else:
                st.error("Question and correct answer are required.")

    if st.button("Reset to Default Questions"):
        st.session_state.questions = list(DEFAULT_QUESTIONS)
        save_data(DATA_FILE, DEFAULT_QUESTIONS)
        st.warning("Reset completed!")

# 3. COMMUNITY Q&A MODE
elif app_mode == "Community Q&A Box":
    st.header("📥 Submit Question to Sheet")
    with st.form("comm_form", clear_on_submit=True):
        csub = st.selectbox("Subject:", ALL_SUBJECTS)
        cq = st.text_area("Question Text*")
        ca = st.text_input("Correct Answer (Optional)")
        cname = st.text_input("Your Name (Optional)")
        if st.form_submit_button("Submit Question"):
            if cq.strip():
                data = {"Subject": csub, "Question": cq.strip(), "Answer": ca.strip() or "Pending", "Submitted_By": cname.strip() or "Student"}
                if send_question_to_sheet(data):
                    st.success("Question submitted successfully!")
                else:
                    st.warning("Submission failed, please try again.")
            else:
                st.error("Question text cannot be empty!")

# 4. SUBSCRIPTION & ₹10 UPI GATEWAY
elif app_mode == "Subscription (Rs 10/Month)":
    st.header("💳 Omega CBT 1-Month Pass")
    u_info = st.session_state.users.get(user_email, {})
    st.info(f"User ID: `{user_email}` | Status: `{'Active' if u_info.get('is_subscribed') else 'Inactive'}` | Valid Till: `{u_info.get('sub_end', 'N/A')}`")

    upi_uri = f"upi://pay?pa={MERCHANT_UPI_ID}&pn=Omega%20CBT&am=10.00&cu=INR&tn=Omega%20CBT%201Month%20Pass"
    qr_api = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={urllib.parse.quote(upi_uri)}"

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Step 1: Scan & Pay Rs 10")
        st.image(qr_api, width=200, caption="Scan with GPay, PhonePe, Paytm")
        st.markdown(f"UPI ID: `{MERCHANT_UPI_ID}`")
        st.markdown(f'<a href="{upi_uri}" style="background:#2563eb;color:#fff;padding:8px 16px;border-radius:6px;text-decoration:none;font-weight:bold;">Pay via UPI App</a>', unsafe_allow_html=True)

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
