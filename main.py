# -*- coding: utf-8 -*-
"""
برنامه‌ریز پژوهشی حرفه‌ای — نسخه‌ی ۲
ساخته‌شده با Streamlit + SQLite + Plotly

نصب پیش‌نیازها:
    pip install streamlit pandas plotly

اجرا:
    streamlit run research_planner_app.py

دسترسی از گوشی (روی همون وای‌فای):
    streamlit run research_planner_app.py --server.address 0.0.0.0
    بعد توی گوشی برو به: http://IP-KAMPYUTER:8501
"""

import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, datetime, timedelta

DB_PATH = "research_planner.db"

# =================================================================
# دیتابیس
# =================================================================
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, category TEXT, priority TEXT,
        due_date TEXT, done INTEGER DEFAULT 0, notes TEXT, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS papers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, journal TEXT, status TEXT,
        submit_date TEXT, last_update TEXT, notes TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS contacts_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        person TEXT NOT NULL, subject TEXT, sent_date TEXT,
        waiting_reply INTEGER DEFAULT 1, followup_date TEXT, notes TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT, content TEXT, tag TEXT, created_at TEXT)""")
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


# ---------- Tasks ----------
def add_task(title, category, priority, due_date, notes):
    run_write("INSERT INTO tasks (title,category,priority,due_date,done,notes,created_at) VALUES (?,?,?,?,0,?,?)",
               (title, category, priority, str(due_date), notes, str(datetime.now())))

def toggle_task(tid, val):
    run_write("UPDATE tasks SET done=? WHERE id=?", (int(val), tid))

def delete_task(tid):
    run_write("DELETE FROM tasks WHERE id=?", (tid,))

def get_tasks():
    return run_read("SELECT * FROM tasks ORDER BY done ASC, due_date ASC")


# ---------- Papers ----------
def add_paper(title, journal, status, submit_date, notes):
    run_write("INSERT INTO papers (title,journal,status,submit_date,last_update,notes) VALUES (?,?,?,?,?,?)",
               (title, journal, status, str(submit_date), str(date.today()), notes))

def update_paper(pid, status, notes=None):
    if notes is None:
        run_write("UPDATE papers SET status=?, last_update=? WHERE id=?", (status, str(date.today()), pid))
    else:
        run_write("UPDATE papers SET status=?, notes=?, last_update=? WHERE id=?",
                   (status, notes, str(date.today()), pid))

def delete_paper(pid):
    run_write("DELETE FROM papers WHERE id=?", (pid,))

def get_papers():
    return run_read("SELECT * FROM papers ORDER BY last_update DESC")


# ---------- Contacts ----------
def add_contact(person, subject, sent_date, waiting, followup_date, notes):
    run_write("""INSERT INTO contacts_log (person,subject,sent_date,waiting_reply,followup_date,notes)
                 VALUES (?,?,?,?,?,?)""",
              (person, subject, str(sent_date), int(waiting), str(followup_date), notes))

def mark_replied(cid):
    run_write("UPDATE contacts_log SET waiting_reply=0 WHERE id=?", (cid,))

def delete_contact(cid):
    run_write("DELETE FROM contacts_log WHERE id=?", (cid,))

def get_contacts():
    return run_read("SELECT * FROM contacts_log ORDER BY waiting_reply DESC, followup_date ASC")


# ---------- Notes ----------
def add_note(title, content, tag):
    run_write("INSERT INTO notes (title,content,tag,created_at) VALUES (?,?,?,?)",
               (title, content, tag, str(datetime.now())))

def delete_note(nid):
    run_write("DELETE FROM notes WHERE id=?", (nid,))

def get_notes():
    return run_read("SELECT * FROM notes ORDER BY created_at DESC")


# =================================================================
# تنظیمات ظاهری
# =================================================================
st.set_page_config(page_title="برنامه‌ریز پژوهشی", page_icon="🎓", layout="wide")
init_db()

# --- پالت رنگی: گرم، کرم و ترکوتا (حس لوکس و آرام) ---
BG = "#F7F3EC"            # کرم روشن
BG_SOFT = "#F0E9DD"        # کرم تیره‌تر برای سایدبار
CARD_BG = "#FFFEFC"        # سفید شیری برای کارت‌ها
INK = "#2B2620"            # قهوه‌ای تیره برای متن اصلی
INK_SOFT = "#7A7266"        # قهوه‌ای روشن برای متن فرعی
BORDER = "#E4DACB"         # حاشیه‌ی طلایی‌کمرنگ

PRIMARY = "#C1662F"        # ترکوتا/زنگاری - رنگ اصلی برند
PRIMARY_DARK = "#A34F21"
GOLD = "#B08D57"           # طلایی تیره برای لمسِ لوکس
SAGE = "#8A9A5B"           # سبز زیتونی برای موفقیت
DANGER = "#B5533C"         # قرمز آجری ملایم
WARNING = "#C99A3D"        # کهربایی

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;500;600;700;800&family=Noto+Serif:ital,wght@0,600;0,700;1,600&display=swap');

html, body, [class*="css"] {{
    font-family: 'Vazirmatn', sans-serif !important;
    direction: rtl;
}}

.stApp {{
    background: {BG};
    background-image:
        radial-gradient(circle at 15% 8%, rgba(193,102,47,0.05) 0%, transparent 45%),
        radial-gradient(circle at 90% 85%, rgba(176,141,87,0.06) 0%, transparent 40%);
    color: {INK};
}}

section[data-testid="stSidebar"] {{
    background: {BG_SOFT};
    border-left: 1px solid {BORDER};
}}
section[data-testid="stSidebar"] * {{ color: {INK} !important; }}
section[data-testid="stSidebar"] .stRadio label {{
    font-size: 15px; padding: 4px 0;
}}

h1, h2, h3, h4 {{
    font-family: 'Noto Serif', 'Vazirmatn', serif !important;
    color: {INK} !important;
    letter-spacing: 0.2px;
}}

.metric-card {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 18px;
    padding: 22px 18px;
    text-align: center;
    box-shadow: 0 2px 3px rgba(43,38,32,0.04), 0 10px 24px rgba(43,38,32,0.06);
    transition: all 0.25s ease;
    border-top: 3px solid {PRIMARY};
}}
.metric-card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 4px 6px rgba(43,38,32,0.05), 0 16px 30px rgba(43,38,32,0.09);
}}
.metric-value {{
    font-family: 'Noto Serif', serif;
    font-size: 36px; font-weight: 700; margin: 8px 0 2px 0;
}}
.metric-label {{ font-size: 13px; color: {INK_SOFT}; letter-spacing: 0.3px; }}

.info-card {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 16px;
    padding: 16px 20px;
    margin-bottom: 12px;
    box-shadow: 0 1px 2px rgba(43,38,32,0.04), 0 6px 16px rgba(43,38,32,0.05);
    border-right: 3px solid {PRIMARY};
}}

.badge {{
    display: inline-block; padding: 3px 13px; border-radius: 999px;
    font-size: 11.5px; font-weight: 700; margin-left: 6px; letter-spacing: 0.2px;
}}
.badge-high {{ background: rgba(181,83,60,0.10); color: {DANGER}; border:1px solid rgba(181,83,60,0.35); }}
.badge-mid {{ background: rgba(201,154,61,0.12); color: {WARNING}; border:1px solid rgba(201,154,61,0.4); }}
.badge-low {{ background: rgba(138,154,91,0.12); color: {SAGE}; border:1px solid rgba(138,154,91,0.4); }}
.badge-neutral {{ background: rgba(176,141,87,0.14); color: {GOLD}; border:1px solid rgba(176,141,87,0.4); }}
.badge-done {{ background: rgba(138,154,91,0.12); color: {SAGE}; border:1px solid rgba(138,154,91,0.4); }}
.badge-wait {{ background: rgba(181,83,60,0.10); color: {DANGER}; border:1px solid rgba(181,83,60,0.35); }}

.section-title {{
    font-family: 'Noto Serif', serif;
    font-size: 23px; font-weight: 700; margin: 6px 0 16px 0;
    border-right: 4px solid {PRIMARY}; padding-right: 14px; color: {INK};
}}

.stButton>button {{
    background: {PRIMARY};
    color: #FFF8F0; border: none; border-radius: 10px;
    padding: 8px 18px; font-weight: 700; transition: 0.2s;
    box-shadow: 0 3px 10px rgba(193,102,47,0.25);
}}
.stButton>button:hover {{
    background: {PRIMARY_DARK};
    transform: translateY(-1px);
    box-shadow: 0 5px 14px rgba(193,102,47,0.35);
}}

.kanban-col {{
    background: rgba(255,255,255,0.5);
    border-radius: 16px; padding: 12px; min-height: 200px;
    border: 1px solid {BORDER};
}}
.kanban-title {{ font-weight: 800; font-size: 14px; margin-bottom: 10px; text-align:center; }}

hr {{ border-color: {BORDER}; }}

div[data-testid="stExpander"] {{
    background: {CARD_BG}; border-radius: 14px; border: 1px solid {BORDER};
    box-shadow: 0 1px 2px rgba(43,38,32,0.03);
}}
div[data-testid="stExpander"] summary {{ color: {INK} !important; font-weight: 600; }}

.stTextInput>div>div>input, .stTextArea textarea, .stDateInput input, .stSelectbox div[data-baseweb="select"] {{
    background-color: #FFFFFF !important; color: {INK} !important;
    border-radius: 10px !important; border: 1px solid {BORDER} !important;
}}
.stTextInput label, .stTextArea label, .stDateInput label, .stSelectbox label, .stCheckbox label p {{
    color: {INK} !important; font-weight: 600 !important;
}}
[data-testid="stMetricValue"], [data-testid="stCaptionContainer"] {{ color: {INK} !important; }}

/* اسکرول‌بار ظریف */
::-webkit-scrollbar {{ width: 8px; }}
::-webkit-scrollbar-thumb {{ background: {BORDER}; border-radius: 8px; }}
</style>
""", unsafe_allow_html=True)


def priority_badge(p):
    cls = {"زیاد": "badge-high", "متوسط": "badge-mid", "کم": "badge-low"}.get(p, "badge-neutral")
    return f'<span class="badge {cls}">{p}</span>'


def status_badge(s):
    colors = {
        "در حال نوشتن": "badge-neutral", "ارسال شده": "badge-mid",
        "در حال داوری": "badge-mid", "نیاز به بازنگری": "badge-high",
        "پذیرفته شده": "badge-done", "رد شده": "badge-wait",
    }
    cls = colors.get(s, "badge-neutral")
    return f'<span class="badge {cls}">{s}</span>'

# پالت هماهنگ برای نمودارها
CHART_COLORS = [PRIMARY, GOLD, WARNING, SAGE, DANGER, "#8C7A63"]


# =================================================================
# سایدبار
# =================================================================
st.sidebar.markdown("## 🎓 برنامه‌ریز پژوهشی")
st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "بخش‌ها",
    ["🏠 داشبورد", "✅ وظایف", "📄 مقالات", "📧 پیگیری ایمیل/اساتید", "📝 یادداشت‌ها", "⚙️ خروجی و پشتیبان"],
    label_visibility="collapsed",
)
st.sidebar.markdown("---")
st.sidebar.caption("ساخته‌شده برای مدیریت کارهای پژوهشی، مقالات و مکاتبات علمی 🌙")

TASK_CATEGORIES = ["مقاله", "درس", "مکاتبه", "داده/آمار", "پایان‌نامه", "سایر"]
TASK_PRIORITIES = ["زیاد", "متوسط", "کم"]
PAPER_STATUSES = ["در حال نوشتن", "ارسال شده", "در حال داوری", "نیاز به بازنگری", "پذیرفته شده", "رد شده"]

# =================================================================
# داشبورد
# =================================================================
if menu == "🏠 داشبورد":
    tasks = get_tasks()
    papers = get_papers()
    contacts = get_contacts()
    notes = get_notes()

    st.markdown('<div class="section-title">نمای کلی</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    open_tasks = int((tasks["done"] == 0).sum()) if not tasks.empty else 0
    active_papers = len(papers) if not papers.empty else 0
    waiting = int((contacts["waiting_reply"] == 1).sum()) if not contacts.empty else 0
    total_notes = len(notes) if not notes.empty else 0

    for col, val, label, color in [
        (c1, open_tasks, "وظایف باز", PRIMARY),
        (c2, active_papers, "مقالات فعال", GOLD),
        (c3, waiting, "منتظر پاسخ ایمیل", DANGER),
        (c4, total_notes, "یادداشت‌ها", SAGE),
    ]:
        col.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value" style="color:{color}">{val}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    colA, colB = st.columns([1, 1])

    with colA:
        st.markdown('<div class="section-title" style="font-size:18px;">📊 وضعیت مقالات</div>', unsafe_allow_html=True)
        if not papers.empty:
            status_counts = papers["status"].value_counts().reset_index()
            status_counts.columns = ["status", "count"]
            fig = px.pie(status_counts, names="status", values="count", hole=0.55,
                         color_discrete_sequence=CHART_COLORS)
            fig.update_traces(textinfo="percent+label", textfont_size=12,
                               marker=dict(line=dict(color=BG, width=2)))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color=INK, font_family="Vazirmatn",
                showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=320,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("هنوز مقاله‌ای ثبت نشده.")

    with colB:
        st.markdown('<div class="section-title" style="font-size:18px;">✅ پیشرفت وظایف</div>', unsafe_allow_html=True)
        if not tasks.empty:
            done_count = int(tasks["done"].sum())
            total = len(tasks)
            pct = round(done_count / total * 100) if total else 0
            fig = go.Figure(go.Indicator(
                mode="gauge+number", value=pct,
                number={'suffix': "%", 'font': {'size': 40, 'color': INK}},
                gauge={
                    'axis': {'range': [0, 100], 'tickcolor': INK_SOFT},
                    'bar': {'color': PRIMARY},
                    'bgcolor': "rgba(193,102,47,0.06)",
                    'bordercolor': BORDER,
                    'borderwidth': 1,
                },
            ))
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color=INK, font_family="Vazirmatn",
                               margin=dict(t=20, b=10, l=20, r=20), height=320)
            st.plotly_chart(fig, use_container_width=True)
            st.caption(f"{done_count} از {total} وظیفه انجام شده")
        else:
            st.info("هنوز وظیفه‌ای ثبت نشده.")

    st.markdown("<br>", unsafe_allow_html=True)
    colC, colD = st.columns(2)

    with colC:
        st.markdown('<div class="section-title" style="font-size:18px;">⏰ ددلاین‌های نزدیک</div>', unsafe_allow_html=True)
        if not tasks.empty:
            up = tasks[tasks["done"] == 0].copy()
            up["d"] = pd.to_datetime(up["due_date"], errors="coerce")
            soon = up[(up["d"] >= pd.Timestamp(date.today())) &
                      (up["d"] <= pd.Timestamp(date.today() + timedelta(days=7)))].sort_values("d")
            if soon.empty:
                st.markdown('<div class="info-card">ددلاین نزدیکی نداری 🎉</div>', unsafe_allow_html=True)
            else:
                for _, r in soon.iterrows():
                    st.markdown(f"""
                    <div class="info-card">
                        <b>{r['title']}</b> {priority_badge(r['priority'])}<br>
                        <span style="color:#7A7266;">📅 {r['due_date']} · {r['category']}</span>
                    </div>""", unsafe_allow_html=True)
        else:
            st.info("هنوز وظیفه‌ای ثبت نشده.")

    with colD:
        st.markdown('<div class="section-title" style="font-size:18px;">📧 نیاز به پیگیری</div>', unsafe_allow_html=True)
        if not contacts.empty:
            w = contacts[contacts["waiting_reply"] == 1]
            if w.empty:
                st.markdown('<div class="info-card">همه ایمیل‌ها پاسخ داده شدن ✅</div>', unsafe_allow_html=True)
            else:
                for _, r in w.iterrows():
                    st.markdown(f"""
                    <div class="info-card">
                        <b>{r['person']}</b><br>
                        <span style="color:#7A7266;">{r['subject']} · پیگیری: {r['followup_date']}</span>
                    </div>""", unsafe_allow_html=True)
        else:
            st.info("هنوز مکاتبه‌ای ثبت نشده.")

# =================================================================
# وظایف
# =================================================================
elif menu == "✅ وظایف":
    st.markdown('<div class="section-title">✅ مدیریت وظایف</div>', unsafe_allow_html=True)

    with st.expander("➕ افزودن وظیفه جدید", expanded=False):
        with st.form("task_form", clear_on_submit=True):
            title = st.text_input("عنوان وظیفه")
            c1, c2, c3 = st.columns(3)
            category = c1.selectbox("دسته", TASK_CATEGORIES)
            priority = c2.selectbox("اولویت", TASK_PRIORITIES)
            due = c3.date_input("سررسید", value=date.today())
            notes = st.text_area("توضیحات (اختیاری)")
            if st.form_submit_button("➕ افزودن") and title:
                add_task(title, category, priority, due, notes)
                st.success("اضافه شد.")
                st.rerun()

    tasks = get_tasks()

    if not tasks.empty:
        fc1, fc2, fc3, fc4 = st.columns([2, 1, 1, 1])
        search = fc1.text_input("🔍 جستجو در وظایف")
        f_cat = fc2.selectbox("دسته", ["همه"] + TASK_CATEGORIES)
        f_pri = fc3.selectbox("اولویت", ["همه"] + TASK_PRIORITIES)
        f_status = fc4.selectbox("وضعیت", ["همه", "باز", "انجام‌شده"])

        filtered = tasks.copy()
        if search:
            filtered = filtered[filtered["title"].str.contains(search, case=False, na=False) |
                                 filtered["notes"].str.contains(search, case=False, na=False)]
        if f_cat != "همه":
            filtered = filtered[filtered["category"] == f_cat]
        if f_pri != "همه":
            filtered = filtered[filtered["priority"] == f_pri]
        if f_status == "باز":
            filtered = filtered[filtered["done"] == 0]
        elif f_status == "انجام‌شده":
            filtered = filtered[filtered["done"] == 1]

        st.caption(f"نمایش {len(filtered)} از {len(tasks)} وظیفه")

        PAGE_SIZE = 15
        total_pages = max(1, -(-len(filtered) // PAGE_SIZE))
        page = st.number_input("صفحه", min_value=1, max_value=total_pages, value=1, step=1) if total_pages > 1 else 1
        start = (page - 1) * PAGE_SIZE
        page_df = filtered.iloc[start:start + PAGE_SIZE]

        for _, row in page_df.iterrows():
            c1, c2, c3 = st.columns([0.06, 0.82, 0.12])
            done = c1.checkbox("", value=bool(row["done"]), key=f"task_{row['id']}")
            if done != bool(row["done"]):
                toggle_task(row["id"], done)
                st.rerun()
            title_html = f"<s>{row['title']}</s>" if done else f"<b>{row['title']}</b>"
            c2.markdown(f"""
            <div class="info-card">
                {title_html} {priority_badge(row['priority'])}
                <span class="badge badge-neutral">{row['category']}</span>
                <br><span style="color:#7A7266;">📅 {row['due_date']}</span>
                {f"<br><span style='color:#9A9080;font-size:13px;'>{row['notes']}</span>" if row['notes'] else ""}
            </div>""", unsafe_allow_html=True)
            if c3.button("🗑️", key=f"del_task_{row['id']}"):
                delete_task(row["id"])
                st.rerun()
    else:
        st.info("هنوز وظیفه‌ای ثبت نکردی.")

# =================================================================
# مقالات — بورد کانبان
# =================================================================
elif menu == "📄 مقالات":
    st.markdown('<div class="section-title">📄 پیگیری مقالات</div>', unsafe_allow_html=True)

    with st.expander("➕ افزودن مقاله جدید", expanded=False):
        with st.form("paper_form", clear_on_submit=True):
            title = st.text_input("عنوان مقاله")
            c1, c2 = st.columns(2)
            journal = c1.text_input("ژورنال هدف")
            status = c2.selectbox("وضعیت", PAPER_STATUSES)
            submit_date = st.date_input("تاریخ ارسال", value=date.today())
            notes = st.text_area("یادداشت")
            if st.form_submit_button("➕ افزودن مقاله") and title:
                add_paper(title, journal, status, submit_date, notes)
                st.success("اضافه شد.")
                st.rerun()

    papers = get_papers()

    if not papers.empty:
        search = st.text_input("🔍 جستجو در عنوان یا ژورنال")
        if search:
            papers = papers[papers["title"].str.contains(search, case=False, na=False) |
                             papers["journal"].str.contains(search, case=False, na=False)]

        st.markdown("<br>", unsafe_allow_html=True)
        cols = st.columns(len(PAPER_STATUSES))
        for i, status in enumerate(PAPER_STATUSES):
            with cols[i]:
                st.markdown(f'<div class="kanban-col"><div class="kanban-title">{status_badge(status)}</div>',
                             unsafe_allow_html=True)
                subset = papers[papers["status"] == status]
                for _, row in subset.iterrows():
                    with st.expander(row["title"][:28] + ("..." if len(row["title"]) > 28 else "")):
                        st.write(f"**ژورنال:** {row['journal']}")
                        st.write(f"**ارسال:** {row['submit_date']}")
                        st.write(f"**آخرین به‌روزرسانی:** {row['last_update']}")
                        if row["notes"]:
                            st.write(f"**یادداشت:** {row['notes']}")
                        new_status = st.selectbox("تغییر وضعیت", PAPER_STATUSES,
                                                   index=PAPER_STATUSES.index(status),
                                                   key=f"mv_{row['id']}")
                        new_notes = st.text_area("ویرایش یادداشت", value=row["notes"] or "", key=f"nt_{row['id']}")
                        b1, b2 = st.columns(2)
                        if b1.button("💾 ذخیره", key=f"save_{row['id']}"):
                            update_paper(row["id"], new_status, new_notes)
                            st.rerun()
                        if b2.button("🗑️ حذف", key=f"delp_{row['id']}"):
                            delete_paper(row["id"])
                            st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("هنوز مقاله‌ای ثبت نکردی.")

# =================================================================
# پیگیری ایمیل / اساتید
# =================================================================
elif menu == "📧 پیگیری ایمیل/اساتید":
    st.markdown('<div class="section-title">📧 پیگیری ایمیل و مکاتبات</div>', unsafe_allow_html=True)

    with st.expander("➕ ثبت مکاتبه جدید", expanded=False):
        with st.form("contact_form", clear_on_submit=True):
            person = st.text_input("گیرنده (مثلاً دکتر ولی‌زاده)")
            subject = st.text_input("موضوع")
            c1, c2 = st.columns(2)
            sent_date = c1.date_input("تاریخ ارسال", value=date.today())
            followup_date = c2.date_input("پیگیری بعدی", value=date.today() + timedelta(days=5))
            waiting = st.checkbox("منتظر پاسخ هستم", value=True)
            notes = st.text_area("یادداشت")
            if st.form_submit_button("➕ ثبت") and person:
                add_contact(person, subject, sent_date, waiting, followup_date, notes)
                st.success("ثبت شد.")
                st.rerun()

    contacts = get_contacts()
    if not contacts.empty:
        fc1, fc2 = st.columns([3, 1])
        search = fc1.text_input("🔍 جستجو بر اساس گیرنده یا موضوع")
        f_status = fc2.selectbox("وضعیت", ["همه", "منتظر پاسخ", "پاسخ گرفته"])

        filtered = contacts.copy()
        if search:
            filtered = filtered[filtered["person"].str.contains(search, case=False, na=False) |
                                 filtered["subject"].str.contains(search, case=False, na=False)]
        if f_status == "منتظر پاسخ":
            filtered = filtered[filtered["waiting_reply"] == 1]
        elif f_status == "پاسخ گرفته":
            filtered = filtered[filtered["waiting_reply"] == 0]

        st.caption(f"نمایش {len(filtered)} از {len(contacts)} مورد")

        for _, row in filtered.iterrows():
            badge = '<span class="badge badge-wait">منتظر پاسخ</span>' if row["waiting_reply"] else '<span class="badge badge-done">پاسخ گرفته شد</span>'
            st.markdown(f"""
            <div class="info-card">
                <b>{row['person']}</b> {badge}<br>
                <span style="color:#7A7266;">{row['subject']}</span><br>
                <span style="color:#9A9080;font-size:13px;">📤 ارسال: {row['sent_date']} · 🔁 پیگیری: {row['followup_date']}</span>
                {f"<br><span style='color:#9A9080;font-size:13px;'>{row['notes']}</span>" if row['notes'] else ""}
            </div>""", unsafe_allow_html=True)
            b1, b2 = st.columns([1, 1])
            if row["waiting_reply"] and b1.button("✅ پاسخ گرفتم", key=f"reply_{row['id']}"):
                mark_replied(row["id"])
                st.rerun()
            if b2.button("🗑️ حذف", key=f"delc_{row['id']}"):
                delete_contact(row["id"])
                st.rerun()
    else:
        st.info("هنوز مکاتبه‌ای ثبت نکردی.")

# =================================================================
# یادداشت‌ها
# =================================================================
elif menu == "📝 یادداشت‌ها":
    st.markdown('<div class="section-title">📝 یادداشت‌ها</div>', unsafe_allow_html=True)

    with st.expander("➕ یادداشت جدید", expanded=False):
        with st.form("note_form", clear_on_submit=True):
            title = st.text_input("عنوان")
            tag = st.text_input("برچسب (مثلاً مقاله لامبل، پایان‌نامه...)")
            content = st.text_area("متن یادداشت", height=150)
            if st.form_submit_button("➕ ذخیره") and title:
                add_note(title, content, tag)
                st.success("ذخیره شد.")
                st.rerun()

    notes = get_notes()
    if not notes.empty:
        search = st.text_input("🔍 جستجو در یادداشت‌ها")
        filtered = notes.copy()
        if search:
            filtered = filtered[filtered["title"].str.contains(search, case=False, na=False) |
                                 filtered["content"].str.contains(search, case=False, na=False)]

        grid = st.columns(3)
        for i, (_, row) in enumerate(filtered.iterrows()):
            with grid[i % 3]:
                tag_html = f'<span class="badge badge-neutral">{row["tag"]}</span>' if row["tag"] else ""
                content_preview = (row['content'] or '')[:120]
                ellipsis = "..." if row['content'] and len(row['content']) > 120 else ""
                st.markdown(f"""
                <div class="info-card">
                    <b>{row['title']}</b> {tag_html}<br>
                    <span style="color:#7A7266;font-size:13px;">{content_preview}{ellipsis}</span><br>
                    <span style="color:#9A9080;font-size:11px;">{row['created_at'][:16]}</span>
                </div>""", unsafe_allow_html=True)
                if st.button("🗑️ حذف", key=f"deln_{row['id']}"):
                    delete_note(row["id"])
                    st.rerun()
    else:
        st.info("هنوز یادداشتی ذخیره نکردی.")

# =================================================================
# خروجی و پشتیبان
# =================================================================
elif menu == "⚙️ خروجی و پشتیبان":
    st.markdown('<div class="section-title">⚙️ خروجی داده‌ها و پشتیبان‌گیری</div>', unsafe_allow_html=True)
    st.caption("همه‌ی دیتای شما داخل فایل research_planner.db به‌صورت محلی ذخیره می‌شود. از این بخش می‌توانید خروجی CSV هر بخش را بگیرید.")

    tabs = st.tabs(["وظایف", "مقالات", "مکاتبات", "یادداشت‌ها"])
    datasets = {"وظایف": get_tasks(), "مقالات": get_papers(), "مکاتبات": get_contacts(), "یادداشت‌ها": get_notes()}

    for tab, (name, df) in zip(tabs, datasets.items()):
        with tab:
            if df.empty:
                st.info("داده‌ای برای نمایش نیست.")
            else:
                st.dataframe(df, use_container_width=True, height=350)
                csv = df.to_csv(index=False).encode("utf-8-sig")
                st.download_button(f"⬇️ دانلود CSV — {name}", data=csv,
                                    file_name=f"{name}.csv", mime="text/csv", key=f"dl_{name}")
