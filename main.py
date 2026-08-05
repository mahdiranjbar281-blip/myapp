# -*- coding: utf-8 -*-
"""
برنامه‌ریز پیشرفته — نسخه کهکشانی متحرک (بدون نیاز به کتابخانه اضافی برای شمسی)
ساخته‌شده با Streamlit + SQLite + Plotly
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime, timedelta

DB_PATH = "research_planner_advanced.db"

# =================================================================
# تبدیل تاریخ شمسی (بومی - بدون نیاز به jdatetime)
# =================================================================
def gregorian_to_jalali(gy, gm, gd):
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    if (gy % 4 == 0 and gy % 100 != 0) or (gy % 400 == 0):
        g_d_m = [0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]
    gy -= 1600
    gm -= 1
    gd -= 1
    g_day_no = 365 * gy + (gy + 3) // 4 - (gy + 99) // 100 + (gy + 399) // 400
    g_day_no += g_d_m[gm] + gd
    j_day_no = g_day_no - 79
    j_np = j_day_no // 12053
    j_day_no %= 12053
    jy = 979 + 33 * j_np + 4 * (j_day_no // 1461)
    j_day_no %= 1461
    if j_day_no >= 366:
        jy += (j_day_no - 1) // 365
        j_day_no = (j_day_no - 1) % 365
    if j_day_no < 186:
        jm = j_day_no // 31
        jd = j_day_no % 31
    else:
        jm = 6 + (j_day_no - 186) // 30
        jd = (j_day_no - 186) % 30
    return jy, jm + 1, jd + 1

def get_persian_date_str():
    now = datetime.now()
    jy, jm, jd = gregorian_to_jalali(now.year, now.month, now.day)
    months = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
    days = ['دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنج‌شنبه', 'جمعه', 'شنبه', 'یکشنبه']
    week_day = days[now.weekday()]
    return f"{week_day} · {jd} {months[jm-1]} {jy}"

# =================================================================
# دیتابیس و مدیریت داده‌ها
# =================================================================
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, category TEXT, priority TEXT, due_date TEXT, done INTEGER DEFAULT 0, notes TEXT, created_at TEXT, completed_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS papers (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, journal TEXT, status TEXT, submit_date TEXT, last_update TEXT, notes TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS contacts_log (id INTEGER PRIMARY KEY AUTOINCREMENT, person TEXT NOT NULL, subject TEXT, sent_date TEXT, waiting_reply INTEGER DEFAULT 1, followup_date TEXT, notes TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, content TEXT, tag TEXT, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS reminders (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, remind_datetime TEXT, is_active INTEGER DEFAULT 1, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS not_to_do (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS habits (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, streak INTEGER DEFAULT 0, last_completed TEXT)""")
    conn.commit()
    conn.close()

def run_write(query, params=()):
    conn = get_conn()
    conn.execute(query, params)
    conn.commit()
    conn.close()

def run_read(query, params=()):
    conn = get_conn()
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df

def add_task(title, category, priority, due_date, notes): run_write("INSERT INTO tasks (title,category,priority,due_date,done,notes,created_at) VALUES (?,?,?,?,0,?,?)", (title, category, priority, str(due_date), notes, str(datetime.now())))
def toggle_task(tid, val): 
    if val: run_write("UPDATE tasks SET done=1, completed_at=? WHERE id=?", (str(date.today()), tid))
    else: run_write("UPDATE tasks SET done=0, completed_at=NULL WHERE id=?", (tid,))
def delete_task(tid): run_write("DELETE FROM tasks WHERE id=?", (tid,))
def get_tasks(): return run_read("SELECT * FROM tasks ORDER BY done ASC, due_date ASC")

def get_streak():
    df = run_read("SELECT DISTINCT completed_at FROM tasks WHERE completed_at IS NOT NULL")
    done_dates = set(df["completed_at"].tolist()) if not df.empty else set()
    streak, d = 0, date.today()
    while str(d) in done_dates:
        streak += 1
        d -= timedelta(days=1)
    return streak

def add_paper(t, j, s, sd, n): run_write("INSERT INTO papers (title,journal,status,submit_date,last_update,notes) VALUES (?,?,?,?,?,?)", (t, j, s, str(sd), str(date.today()), n))
def get_papers(): return run_read("SELECT * FROM papers ORDER BY last_update DESC")
def delete_paper(pid): run_write("DELETE FROM papers WHERE id=?", (pid,))

def add_contact(p, s, sd, w, fd, n): run_write("INSERT INTO contacts_log (person,subject,sent_date,waiting_reply,followup_date,notes) VALUES (?,?,?,?,?,?)", (p, s, str(sd), int(w), str(fd), n))
def get_contacts(): return run_read("SELECT * FROM contacts_log ORDER BY waiting_reply DESC, followup_date ASC")
def delete_contact(cid): run_write("DELETE FROM contacts_log WHERE id=?", (cid,))

def add_note(t, c, tag): run_write("INSERT INTO notes (title,content,tag,created_at) VALUES (?,?,?,?)", (t, c, tag, str(datetime.now())))
def get_notes(): return run_read("SELECT * FROM notes ORDER BY created_at DESC")
def delete_note(nid): run_write("DELETE FROM notes WHERE id=?", (nid,))

def add_reminder(t, dt): run_write("INSERT INTO reminders (title, remind_datetime, is_active, created_at) VALUES (?,?,?,?)", (t, str(dt), 1, str(datetime.now())))
def dismiss_reminder(rid): run_write("UPDATE reminders SET is_active=0 WHERE id=?", (rid,))
def get_reminders(): return run_read("SELECT * FROM reminders ORDER BY remind_datetime ASC")

def add_nottodo(t): run_write("INSERT INTO not_to_do (title, created_at) VALUES (?,?)", (t, str(datetime.now())))
def get_nottodos(): return run_read("SELECT * FROM not_to_do ORDER BY created_at DESC")
def delete_nottodo(nid): run_write("DELETE FROM not_to_do WHERE id=?", (nid,))

def add_habit(t): run_write("INSERT INTO habits (title, streak) VALUES (?, 0)", (t,))
def increment_habit(hid): run_write("UPDATE habits SET streak = streak + 1, last_completed = ? WHERE id = ?", (str(date.today()), hid))
def get_habits(): return run_read("SELECT * FROM habits")

# =================================================================
# استایل متحرک و شیشه‌ای (Galaxy Glassmorphism)
# =================================================================
st.set_page_config(page_title="برنامه‌ریز پیشرفته", page_icon="🪻", layout="wide")
init_db()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Vazirmatn', sans-serif !important;
    direction: rtl;
}

/* رقص رنگ پس‌زمینه سایت */
@keyframes gradientBG {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

.stApp {
    background: linear-gradient(-45deg, #0f0524, #2E1065, #4c1d95, #1e1b4b);
    background-size: 400% 400%;
    animation: gradientBG 15s ease infinite;
    color: #F8F5FC;
}

/* سایدبار شیشه‌ای */
section[data-testid="stSidebar"] {
    background: rgba(255, 255, 255, 0.85) !important;
    backdrop-filter: blur(25px);
    border-left: 1px solid rgba(255, 255, 255, 0.4);
}
section[data-testid="stSidebar"] * { color: #1e0b3e !important; font-weight: 600; }

/* کارت‌های شیشه‌ای برای شفافیت متن */
.glass-card {
    background: rgba(255, 255, 255, 0.93) !important;
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.5);
    border-radius: 20px;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 15px 35px -5px rgba(0, 0, 0, 0.4);
    transition: all 0.3s ease;
    color: #1e0b3e !important;
}
.glass-card * { color: #1e0b3e !important; }

.glass-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 20px 40px -5px rgba(0, 0, 0, 0.5);
    border-color: #A855F7;
}

/* هدر اصلی داشبورد */
.hero-card {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.75) 0%, rgba(109, 40, 217, 0.75) 100%);
    backdrop-filter: blur(15px);
    border-radius: 28px;
    padding: 35px 40px;
    margin-bottom: 30px;
    color: white !important;
    box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.3);
}
.hero-card * { color: white !important; }

.metric-card {
    background: rgba(255, 255, 255, 0.93);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.5);
    border-radius: 20px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 10px 25px rgba(0,0,0,0.3);
    border-top: 4px solid #A855F7;
    transition: transform 0.2s ease;
}
.metric-card:hover { transform: translateY(-3px); }
.metric-value { font-size: 38px; font-weight: 900; color: #4C1D95; margin: 5px 0; }
.metric-label { font-size: 14px; color: #2E1065; font-weight: 800; }

/* بج‌ها */
.badge { display: inline-block; padding: 5px 14px; border-radius: 99px; font-size: 12px; font-weight: 800; margin-left: 6px; }
.badge-high { background: #FEE2E2; color: #DC2626; border: 1px solid #FCA5A5; }
.badge-mid { background: #FEF3C7; color: #D97706; border: 1px solid #FDE68A; }
.badge-low { background: #D1FAE5; color: #059669; border: 1px solid #A7F3D0; }
.badge-lilac { background: #F3E8FF; color: #5B21B6; border: 1px solid #DDD6FE; }

/* دکمه‌ها */
.stButton>button {
    background: linear-gradient(135deg, #A855F7 0%, #7C3AED 100%);
    color: white !important;
    border: none;
    border-radius: 14px;
    padding: 10px 24px;
    font-weight: 700;
    box-shadow: 0 8px 20px rgba(0,0,0,0.3);
    transition: all 0.25s ease;
}
.stButton>button:hover { transform: translateY(-3px); box-shadow: 0 12px 25px rgba(0,0,0,0.4); }

/* تیترها روی پس‌زمینه تیره */
.section-title {
    font-size: 26px;
    font-weight: 900;
    color: #FFFFFF !important;
    text-shadow: 0 4px 15px rgba(0,0,0,0.5);
    margin: 25px 0 20px 0;
    display: flex;
    align-items: center;
    gap: 12px;
}
.section-title::before {
    content: "";
    width: 8px; height: 28px;
    background: #C084FC;
    border-radius: 99px;
    box-shadow: 0 0 15px #C084FC;
}

/* فرم‌ها */
div[data-testid="stExpander"] {
    background: rgba(255, 255, 255, 0.95) !important;
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.6);
    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
}
div[data-testid="stExpander"] * { color: #1e0b3e !important; }

.stTextInput>div>div>input, .stTextArea textarea, .stDateInput input, .stSelectbox div[data-baseweb="select"] {
    background-color: #FFFFFF !important;
    border: 2px solid #E9D5FF !important;
    border-radius: 12px !important;
    color: #2E1065 !important;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

def priority_badge(p):
    cls = {"زیاد": "badge-high", "متوسط": "badge-mid", "کم": "badge-low"}.get(p, "badge-lilac")
    return f'<span class="badge {cls}">{p}</span>'

TASK_CATEGORIES = ["شخصی 🪴", "مقاله 📄", "درس 📚", "مکاتبه 📧", "داده/آمار 📊", "پایان‌نامه 🎓", "ورزش 🏃🏻‍♂️", "سایر ⚙️"]
TASK_PRIORITIES = ["زیاد", "متوسط", "کم"]

# =================================================================
# سیستم آلارم
# =================================================================
reminders_df = get_reminders()
if not reminders_df.empty:
    active_rems = reminders_df[reminders_df['is_active'] == 1]
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for _, r in active_rems.iterrows():
        if r['remind_datetime'] <= now_str:
            st.markdown(f"""
            <div style="background: rgba(254, 226, 226, 0.95); border: 2px solid #EF4444; padding: 16px 20px; border-radius: 16px; margin-bottom: 20px; color: #991B1B; font-weight: 700;">
                🔔 <b>یادآور مهم:</b> {r['title']} (زمان: {r['remind_datetime']})
            </div>""", unsafe_allow_html=True)
            if st.button("تایید و بستن هشدار", key=f"dismiss_{r['id']}"):
                dismiss_reminder(r['id'])
                st.rerun()

# =================================================================
# سایدبار
# =================================================================
st.sidebar.markdown(f"""
<div style="padding: 10px 0 20px 0; text-align: center;">
    <div style="background: linear-gradient(135deg, #A855F7, #6D28D9); color: white !important; width: 65px; height: 65px; border-radius: 22px; display: inline-flex; align-items: center; justify-content: center; font-size: 32px; box-shadow: 0 10px 20px rgba(139,92,246,0.5);">🪻</div>
    <div style="font-size: 24px; font-weight: 900; color: #1e0b3e !important; margin-top: 15px;">برنامه‌ریز پیشرفته</div>
    <div style="font-size: 14px; color: #5B21B6 !important; font-weight: 700;">نسخه کهکشانی هوشمند</div>
</div>
""", unsafe_allow_html=True)

menu = st.sidebar.radio(
    "بخش‌ها",
    ["🏠 داشبورد امروز", "✅ مدیریت وظایف", "🌱 عادت‌ها و سبک زندگی", "🔔 مرکز یادآورها", "📄 مقالات و پژوهش", "📧 مکاتبات", "📝 یادداشت‌ها"],
    label_visibility="collapsed"
)

# =================================================================
# داشبورد
# =================================================================
if menu == "🏠 داشبورد امروز":
    
    clock_html = f"""
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px;">
        <div>
            <div style="font-size: 34px; font-weight: 900; margin-bottom: 8px;">روزت بخیر! 🪻</div>
            <div style="font-size: 18px; opacity: 0.95; font-weight: 600;">📅 {get_persian_date_str()}</div>
            <div style="margin-top: 15px; background: rgba(255,255,255,0.3); backdrop-filter: blur(10px); padding: 10px 20px; border-radius: 99px; display: inline-block; font-size: 15px; font-weight: 800; border: 1px solid rgba(255,255,255,0.4);">
                🔥 {get_streak()} روز متوالی تلاش مستمر
            </div>
        </div>
        <div style="background: rgba(0,0,0,0.35); padding: 20px 35px; border-radius: 24px; border: 1px solid rgba(255,255,255,0.25); text-align: center; box-shadow: inset 0 0 20px rgba(0,0,0,0.2);">
            <div id="live_clock" style="font-size: 46px; font-weight: 900; font-family: monospace; letter-spacing: 4px; text-shadow: 0 0 15px rgba(255,255,255,0.6);"></div>
            <div style="font-size: 13px; opacity: 0.85; margin-top: 5px; font-weight: 700; letter-spacing: 1px;">ساعت رسمی</div>
        </div>
    </div>
    <script>
        function updateClock() {{
            var now = new Date();
            var hours = String(now.getHours()).padStart(2, '0');
            var minutes = String(now.getMinutes()).padStart(2, '0');
            var seconds = String(now.getSeconds()).padStart(2, '0');
            document.getElementById('live_clock').innerText = hours + ':' + minutes + ':' + seconds;
        }}
        setInterval(updateClock, 1000);
        updateClock();
    </script>
    """
    st.markdown(f'<div class="hero-card">{clock_html}</div>', unsafe_allow_html=True)

    tasks, papers, contacts, rems = get_tasks(), get_papers(), get_contacts(), get_reminders()
    open_tasks = int((tasks["done"] == 0).sum()) if not tasks.empty else 0
    active_papers = len(papers) if not papers.empty else 0
    waiting_contacts = int((contacts["waiting_reply"] == 1).sum()) if not contacts.empty else 0
    active_rems = int((rems["is_active"] == 1).sum()) if not rems.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="metric-card"><div class="metric-label">✅ وظایف باز</div><div class="metric-value">{open_tasks}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-label">📄 مقالات فعال</div><div class="metric-value">{active_papers}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-label">📧 منتظر پاسخ</div><div class="metric-value">{waiting_contacts}</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-card"><div class="metric-label">🔔 آلارم فعال</div><div class="metric-value">{active_rems}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    colA, colB = st.columns([1.6, 1])

    with colA:
        st.markdown('<div class="section-title">🎯 برنامه تمرکز امروز</div>', unsafe_allow_html=True)
        if not tasks.empty:
            tasks["d"] = pd.to_datetime(tasks["due_date"], errors="coerce")
            today_tasks = tasks[(tasks["d"].dt.date == date.today()) & (tasks["done"] == 0)]
            if today_tasks.empty:
                st.markdown('<div class="glass-card" style="text-align:center;"><b>🎉 عالیه! برنامه امروزت کاملاً انجام شده.</b></div>', unsafe_allow_html=True)
            else:
                for _, r in today_tasks.iterrows():
                    st.markdown(f"""
                    <div class="glass-card" style="padding:16px 20px; margin-bottom:12px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:800; font-size:16px;">{r['title']}</span>
                            <div>{priority_badge(r['priority'])} <span class="badge badge-lilac">{r['category']}</span></div>
                        </div>
                    </div>""", unsafe_allow_html=True)
        else:
            st.info("وظیفه‌ای ثبت نشده است.")

    with colB:
        st.markdown('<div class="section-title">🚫 خطوط قرمز (نبایدها)</div>', unsafe_allow_html=True)
        nottodos = get_nottodos()
        if not nottodos.empty:
            for _, r in nottodos.iterrows():
                st.markdown(f"""
                <div class="glass-card" style="border-right: 5px solid #EF4444; padding:14px; margin-bottom:12px;">
                    <span style="color:#B91C1C !important; font-weight:800;">❌ {r['title']}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.caption("نبایدی ثبت نشده.")

# =================================================================
# سایر تب‌ها
# =================================================================
elif menu == "✅ مدیریت وظایف":
    st.markdown('<div class="section-title">✅ مدیریت وظایف و برنامه‌ریزی</div>', unsafe_allow_html=True)

    with st.expander("➕ افزودن وظیفه جدید", expanded=False):
        with st.form("task_form", clear_on_submit=True):
            title = st.text_input("عنوان وظیفه")
            c1, c2, c3 = st.columns(3)
            category = c1.selectbox("دسته‌بندی", TASK_CATEGORIES)
            priority = c2.selectbox("اولویت", TASK_PRIORITIES)
            due = c3.date_input("موعد انجام (میلادی)", value=date.today())
            notes = st.text_area("توضیحات تکمیلی")
            if st.form_submit_button("💾 ثبت وظیفه") and title:
                add_task(title, category, priority, due, notes)
                st.rerun()

    tasks = get_tasks()
    if not tasks.empty:
        open_df = tasks[tasks["done"] == 0]
        if not open_df.empty:
            st.markdown("### ⏳ در دست انجام")
            for _, row in open_df.iterrows():
                c1, c2, c3 = st.columns([0.05, 0.85, 0.1])
                if c1.checkbox("", key=f"chk_{row['id']}"):
                    toggle_task(row["id"], True)
                    st.rerun()
                c2.markdown(f"""
                <div class="glass-card" style="padding:14px 20px; margin-bottom:10px;">
                    <b>{row['title']}</b> {priority_badge(row['priority'])} <span class="badge badge-lilac">{row['category']}</span>
                    <span style="float:left; font-size:12px; font-weight:600; opacity:0.8;">📅 {row['due_date']}</span>
                </div>""", unsafe_allow_html=True)
                if c3.button("🗑️", key=f"del_{row['id']}"):
                    delete_task(row["id"])
                    st.rerun()

elif menu == "🌱 عادت‌ها و سبک زندگی":
    st.markdown('<div class="section-title">🌱 توسعه فردی و روتین‌ها</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🚫 لیست نبایدها")
        with st.form("ntd_form", clear_on_submit=True):
            nt_item = st.text_input("نباید جدید")
            if st.form_submit_button("➕ افزودن") and nt_item:
                add_nottodo(nt_item)
                st.rerun()
        for _, r in get_nottodos().iterrows():
            ca, cb = st.columns([0.85, 0.15])
            ca.markdown(f"<div class='glass-card' style='border-right: 4px solid #EF4444; padding:12px; color:#991B1B !important; font-weight:bold;'>❌ {r['title']}</div>", unsafe_allow_html=True)
            if cb.button("🗑️", key=f"dntd_{r['id']}"):
                delete_nottodo(r['id'])
                st.rerun()
    with col2:
        st.markdown("### ⚡ ردیاب عادت‌ها")
        with st.form("habit_form", clear_on_submit=True):
            h_title = st.text_input("عادت جدید")
            if st.form_submit_button("➕ ثبت") and h_title:
                add_habit(h_title)
                st.rerun()
        for _, h in get_habits().iterrows():
            cx, cy = st.columns([0.8, 0.2])
            cx.markdown(f"<div class='glass-card' style='padding:12px;'><b>{h['title']}</b> <span style='float:left; color:#6D28D9 !important; font-weight:900;'>🔥 {h['streak']} روز</span></div>", unsafe_allow_html=True)
            if cy.button("➕", key=f"inc_{h['id']}"):
                increment_habit(h['id'])
                st.rerun()

elif menu == "🔔 مرکز یادآورها":
    st.markdown('<div class="section-title">🔔 یادآورهای هوشمند</div>', unsafe_allow_html=True)
    with st.form("rem_form", clear_on_submit=True):
        rt = st.text_input("عنوان یادآوری")
        c1, c2 = st.columns(2)
        rd = c1.date_input("تاریخ (میلادی)", value=date.today())
        rtm = c2.time_input("ساعت")
        if st.form_submit_button("ثبت یادآور") and rt:
            dt_str = f"{rd} {rtm}"
            add_reminder(rt, dt_str)
            st.rerun()
    rems = get_reminders()
    if not rems.empty:
        for _, r in rems.iterrows():
            c1, c2 = st.columns([0.9, 0.1])
            status = "🟢 فعال" if r['is_active'] else "🔴 غیرفعال"
            c1.markdown(f"<div class='glass-card' style='padding:14px;'><b>{r['title']}</b> - ⏳ {r['remind_datetime']} <span class='badge badge-lilac'>{status}</span></div>", unsafe_allow_html=True)
            if c2.button("🗑️", key=f"drem_{r['id']}"):
                delete_reminder(r['id'])
                st.rerun()

elif menu == "📄 مقالات و پژوهش":
    st.markdown('<div class="section-title">📄 مدیریت مقالات و پایان‌نامه</div>', unsafe_allow_html=True)
    with st.expander("➕ مقاله جدید"):
        with st.form("paper_form", clear_on_submit=True):
            t = st.text_input("عنوان مقاله")
            j = st.text_input("نام ژورنال")
            s = st.selectbox("وضعیت", ["Draft", "Submitted", "Under Review", "Revision", "Accepted", "Rejected"])
            sd = st.date_input("تاریخ سابمیت (تخمینی/واقعی)")
            n = st.text_area("یادداشت")
            if st.form_submit_button("ثبت") and t:
                add_paper(t, j, s, sd, n)
                st.rerun()
    papers = get_papers()
    if not papers.empty:
        for _, p in papers.iterrows():
            st.markdown(f"<div class='glass-card'><b>{p['title']}</b><br><span style='color:#6D28D9; font-size:14px; font-weight:bold;'>ژورنال: {p['journal']} | وضعیت: {p['status']}</span><p style='font-size:13px;'>{p['notes']}</p></div>", unsafe_allow_html=True)

elif menu == "📧 مکاتبات":
    st.markdown('<div class="section-title">📧 لاگ مکاتبات با اساتید</div>', unsafe_allow_html=True)
    with st.expander("➕ مکاتبه جدید"):
        with st.form("contact_form", clear_on_submit=True):
            p = st.text_input("نام استاد / دانشگاه")
            s = st.text_input("موضوع ایمیل")
            sd = st.date_input("تاریخ ارسال")
            fd = st.date_input("تاریخ پیگیری (Follow-up)")
            w = st.checkbox("منتظر پاسخ هستم", value=True)
            n = st.text_area("توضیحات/نتیجه")
            if st.form_submit_button("ثبت") and p:
                add_contact(p, s, sd, w, fd, n)
                st.rerun()
    contacts = get_contacts()
    if not contacts.empty:
        for _, c in contacts.iterrows():
            w_badge = "⏳ منتظر پاسخ" if c['waiting_reply'] else "✅ پایان‌یافته"
            st.markdown(f"<div class='glass-card'><b>{c['person']}</b> - {c['subject']} <span class='badge badge-mid'>{w_badge}</span><br><span style='font-size:13px; font-weight:bold; color:#4C1D95;'>ارسال: {c['sent_date']} | پیگیری: {c['followup_date']}</span></div>", unsafe_allow_html=True)

elif menu == "📝 یادداشت‌ها":
    st.markdown('<div class="section-title">📝 دفترچه یادداشت سریع</div>', unsafe_allow_html=True)
    with st.form("note_form", clear_on_submit=True):
        t = st.text_input("عنوان ایده / یادداشت")
        tg = st.text_input("برچسب (مثال: ایده مقاله، خرید)")
        c = st.text_area("متن یادداشت")
        if st.form_submit_button("ذخیره") and t:
            add_note(t, c, tg)
            st.rerun()
    notes = get_notes()
    if not notes.empty:
        for _, n in notes.iterrows():
            st.markdown(f"<div class='glass-card'><b>{n['title']}</b> <span class='badge badge-lilac'>{n['tag']}</span><p style='margin-top:10px; line-height:1.6;'>{n['content']}</p></div>", unsafe_allow_html=True)
