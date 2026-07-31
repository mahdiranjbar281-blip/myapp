# -*- coding: utf-8 -*-
"""
اپلیکیشن شخصی برنامه‌ریزی پژوهشی
ساخته‌شده با Streamlit + SQLite
نویسنده: مهدی (سفارشی‌سازی‌شده برای کارهای پژوهشی، مقالات و پیگیری اساتید)

نحوه‌ی اجرا:
    pip install streamlit pandas
    streamlit run research_planner_app.py

برای دسترسی از گوشی (وقتی روی همون وای‌فای هستی):
    streamlit run research_planner_app.py --server.address 0.0.0.0
    بعد توی گوشی برو به: http://IP-KAMPYUTER:8501
    (IP کامپیوترت رو با دستور ipconfig یا ifconfig پیدا کن)
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime, timedelta

DB_PATH = "research_planner.db"

# ---------------------------------------------------------------
# اتصال به دیتابیس و ساخت جدول‌ها
# ---------------------------------------------------------------
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT,
        priority TEXT,
        due_date TEXT,
        done INTEGER DEFAULT 0,
        notes TEXT,
        created_at TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS papers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        journal TEXT,
        status TEXT,
        submit_date TEXT,
        last_update TEXT,
        notes TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS contacts_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        person TEXT NOT NULL,
        subject TEXT,
        sent_date TEXT,
        waiting_reply INTEGER DEFAULT 1,
        followup_date TEXT,
        notes TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


# ---------------------------------------------------------------
# توابع کمکی برای هر جدول
# ---------------------------------------------------------------
def add_task(title, category, priority, due_date, notes):
    conn = get_conn()
    conn.execute(
        "INSERT INTO tasks (title, category, priority, due_date, done, notes, created_at) VALUES (?,?,?,?,0,?,?)",
        (title, category, priority, str(due_date), notes, str(datetime.now())),
    )
    conn.commit()
    conn.close()


def toggle_task(task_id, done_value):
    conn = get_conn()
    conn.execute("UPDATE tasks SET done=? WHERE id=?", (int(done_value), task_id))
    conn.commit()
    conn.close()


def delete_task(task_id):
    conn = get_conn()
    conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()


def get_tasks():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM tasks ORDER BY done ASC, due_date ASC", conn)
    conn.close()
    return df


def add_paper(title, journal, status, submit_date, notes):
    conn = get_conn()
    conn.execute(
        "INSERT INTO papers (title, journal, status, submit_date, last_update, notes) VALUES (?,?,?,?,?,?)",
        (title, journal, status, str(submit_date), str(date.today()), notes),
    )
    conn.commit()
    conn.close()


def update_paper_status(paper_id, status):
    conn = get_conn()
    conn.execute(
        "UPDATE papers SET status=?, last_update=? WHERE id=?",
        (status, str(date.today()), paper_id),
    )
    conn.commit()
    conn.close()


def delete_paper(paper_id):
    conn = get_conn()
    conn.execute("DELETE FROM papers WHERE id=?", (paper_id,))
    conn.commit()
    conn.close()


def get_papers():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM papers ORDER BY last_update DESC", conn)
    conn.close()
    return df


def add_contact_log(person, subject, sent_date, waiting_reply, followup_date, notes):
    conn = get_conn()
    conn.execute(
        "INSERT INTO contacts_log (person, subject, sent_date, waiting_reply, followup_date, notes) VALUES (?,?,?,?,?,?)",
        (person, subject, str(sent_date), int(waiting_reply), str(followup_date), notes),
    )
    conn.commit()
    conn.close()


def mark_reply_received(log_id):
    conn = get_conn()
    conn.execute("UPDATE contacts_log SET waiting_reply=0 WHERE id=?", (log_id,))
    conn.commit()
    conn.close()


def delete_contact_log(log_id):
    conn = get_conn()
    conn.execute("DELETE FROM contacts_log WHERE id=?", (log_id,))
    conn.commit()
    conn.close()


def get_contacts_log():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM contacts_log ORDER BY waiting_reply DESC, followup_date ASC", conn)
    conn.close()
    return df


def add_note(title, content):
    conn = get_conn()
    conn.execute(
        "INSERT INTO notes (title, content, created_at) VALUES (?,?,?)",
        (title, content, str(datetime.now())),
    )
    conn.commit()
    conn.close()


def delete_note(note_id):
    conn = get_conn()
    conn.execute("DELETE FROM notes WHERE id=?", (note_id,))
    conn.commit()
    conn.close()


def get_notes():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM notes ORDER BY created_at DESC", conn)
    conn.close()
    return df


# ---------------------------------------------------------------
# تنظیمات صفحه
# ---------------------------------------------------------------
st.set_page_config(page_title="برنامه‌ریز پژوهشی من", page_icon="📚", layout="centered")
init_db()

st.markdown(
    """
    <style>
    * { direction: rtl; text-align: right; }
    .stButton>button { width: 100%; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📚 برنامه‌ریز پژوهشی من")

menu = st.sidebar.radio(
    "بخش‌ها",
    ["🏠 داشبورد", "✅ وظایف", "📄 مقالات", "📧 پیگیری ایمیل/اساتید", "📝 یادداشت‌ها"],
)

TASK_CATEGORIES = ["مقاله", "درس", "مکاتبه", "داده/آمار", "پایان‌نامه", "سایر"]
TASK_PRIORITIES = ["زیاد", "متوسط", "کم"]
PAPER_STATUSES = ["در حال نوشتن", "ارسال شده", "در حال داوری", "نیاز به بازنگری", "پذیرفته شده", "رد شده"]

# ---------------------------------------------------------------
# داشبورد
# ---------------------------------------------------------------
if menu == "🏠 داشبورد":
    tasks = get_tasks()
    papers = get_papers()
    contacts = get_contacts_log()

    col1, col2, col3 = st.columns(3)
    col1.metric("وظایف باز", int((tasks["done"] == 0).sum()) if not tasks.empty else 0)
    col2.metric("مقالات فعال", len(papers) if not papers.empty else 0)
    col3.metric("منتظر پاسخ", int((contacts["waiting_reply"] == 1).sum()) if not contacts.empty else 0)

    st.subheader("⏰ ددلاین‌های نزدیک (۷ روز آینده)")
    if not tasks.empty:
        upcoming = tasks[tasks["done"] == 0].copy()
        upcoming["due_date_parsed"] = pd.to_datetime(upcoming["due_date"], errors="coerce")
        soon = upcoming[
            (upcoming["due_date_parsed"] >= pd.Timestamp(date.today()))
            & (upcoming["due_date_parsed"] <= pd.Timestamp(date.today() + timedelta(days=7)))
        ].sort_values("due_date_parsed")
        if soon.empty:
            st.info("ددلاین نزدیکی نداری 🎉")
        else:
            for _, row in soon.iterrows():
                st.warning(f"**{row['title']}** — {row['due_date']} ({row['category']})")
    else:
        st.info("هنوز وظیفه‌ای ثبت نکردی.")

    st.subheader("📧 نیاز به پیگیری")
    if not contacts.empty:
        waiting = contacts[contacts["waiting_reply"] == 1]
        if waiting.empty:
            st.info("همه ایمیل‌ها پاسخ داده شدن ✅")
        else:
            for _, row in waiting.iterrows():
                st.write(f"🔸 **{row['person']}** — {row['subject']} (پیگیری: {row['followup_date']})")

# ---------------------------------------------------------------
# وظایف
# ---------------------------------------------------------------
elif menu == "✅ وظایف":
    st.subheader("افزودن وظیفه جدید")
    with st.form("task_form", clear_on_submit=True):
        title = st.text_input("عنوان وظیفه")
        c1, c2 = st.columns(2)
        category = c1.selectbox("دسته", TASK_CATEGORIES)
        priority = c2.selectbox("اولویت", TASK_PRIORITIES)
        due = st.date_input("تاریخ سررسید", value=date.today())
        notes = st.text_area("توضیحات (اختیاری)")
        submitted = st.form_submit_button("➕ افزودن")
        if submitted and title:
            add_task(title, category, priority, due, notes)
            st.success("وظیفه اضافه شد.")
            st.rerun()

    st.subheader("لیست وظایف")
    tasks = get_tasks()
    if tasks.empty:
        st.info("هنوز وظیفه‌ای نداری.")
    else:
        for _, row in tasks.iterrows():
            c1, c2, c3 = st.columns([0.1, 0.75, 0.15])
            done = c1.checkbox("", value=bool(row["done"]), key=f"task_{row['id']}")
            if done != bool(row["done"]):
                toggle_task(row["id"], done)
                st.rerun()
            label = f"~~{row['title']}~~" if done else f"**{row['title']}**"
            c2.markdown(f"{label} — {row['category']} | اولویت: {row['priority']} | سررسید: {row['due_date']}")
            if c3.button("🗑️", key=f"del_task_{row['id']}"):
                delete_task(row["id"])
                st.rerun()

# ---------------------------------------------------------------
# مقالات
# ---------------------------------------------------------------
elif menu == "📄 مقالات":
    st.subheader("افزودن مقاله جدید")
    with st.form("paper_form", clear_on_submit=True):
        title = st.text_input("عنوان مقاله")
        journal = st.text_input("ژورنال هدف")
        status = st.selectbox("وضعیت", PAPER_STATUSES)
        submit_date = st.date_input("تاریخ ارسال", value=date.today())
        notes = st.text_area("یادداشت")
        submitted = st.form_submit_button("➕ افزودن مقاله")
        if submitted and title:
            add_paper(title, journal, status, submit_date, notes)
            st.success("مقاله اضافه شد.")
            st.rerun()

    st.subheader("لیست مقالات")
    papers = get_papers()
    if papers.empty:
        st.info("هنوز مقاله‌ای ثبت نکردی.")
    else:
        for _, row in papers.iterrows():
            with st.expander(f"{row['title']}  —  {row['status']}"):
                st.write(f"ژورنال: {row['journal']}")
                st.write(f"تاریخ ارسال: {row['submit_date']}")
                st.write(f"آخرین به‌روزرسانی: {row['last_update']}")
                if row["notes"]:
                    st.write(f"یادداشت: {row['notes']}")
                new_status = st.selectbox(
                    "تغییر وضعیت", PAPER_STATUSES,
                    index=PAPER_STATUSES.index(row["status"]) if row["status"] in PAPER_STATUSES else 0,
                    key=f"status_{row['id']}",
                )
                cc1, cc2 = st.columns(2)
                if cc1.button("💾 ذخیره وضعیت", key=f"save_{row['id']}"):
                    update_paper_status(row["id"], new_status)
                    st.rerun()
                if cc2.button("🗑️ حذف مقاله", key=f"delpaper_{row['id']}"):
                    delete_paper(row["id"])
                    st.rerun()

# ---------------------------------------------------------------
# پیگیری ایمیل / اساتید
# ---------------------------------------------------------------
elif menu == "📧 پیگیری ایمیل/اساتید":
    st.subheader("ثبت ایمیل/مکاتبه جدید")
    with st.form("contact_form", clear_on_submit=True):
        person = st.text_input("گیرنده (مثلاً دکتر ولی‌زاده)")
        subject = st.text_input("موضوع")
        sent_date = st.date_input("تاریخ ارسال", value=date.today())
        followup_date = st.date_input("تاریخ پیگیری بعدی", value=date.today() + timedelta(days=5))
        waiting = st.checkbox("منتظر پاسخ هستم", value=True)
        notes = st.text_area("یادداشت")
        submitted = st.form_submit_button("➕ ثبت")
        if submitted and person:
            add_contact_log(person, subject, sent_date, waiting, followup_date, notes)
            st.success("ثبت شد.")
            st.rerun()

    st.subheader("لیست پیگیری‌ها")
    contacts = get_contacts_log()
    if contacts.empty:
        st.info("هنوز مکاتبه‌ای ثبت نکردی.")
    else:
        for _, row in contacts.iterrows():
            status_icon = "🔸 منتظر پاسخ" if row["waiting_reply"] else "✅ پاسخ گرفته شد"
            with st.expander(f"{row['person']} — {row['subject']}  ({status_icon})"):
                st.write(f"تاریخ ارسال: {row['sent_date']}")
                st.write(f"پیگیری بعدی: {row['followup_date']}")
                if row["notes"]:
                    st.write(f"یادداشت: {row['notes']}")
                cc1, cc2 = st.columns(2)
                if row["waiting_reply"] and cc1.button("✅ پاسخ گرفتم", key=f"reply_{row['id']}"):
                    mark_reply_received(row["id"])
                    st.rerun()
                if cc2.button("🗑️ حذف", key=f"delcontact_{row['id']}"):
                    delete_contact_log(row["id"])
                    st.rerun()

# ---------------------------------------------------------------
# یادداشت‌ها
# ---------------------------------------------------------------
elif menu == "📝 یادداشت‌ها":
    st.subheader("یادداشت جدید")
    with st.form("note_form", clear_on_submit=True):
        title = st.text_input("عنوان")
        content = st.text_area("متن یادداشت", height=150)
        submitted = st.form_submit_button("➕ ذخیره")
        if submitted and title:
            add_note(title, content)
            st.success("یادداشت ذخیره شد.")
            st.rerun()

    st.subheader("یادداشت‌های من")
    notes = get_notes()
    if notes.empty:
        st.info("هنوز یادداشتی ذخیره نکردی.")
    else:
        for _, row in notes.iterrows():
            with st.expander(f"{row['title']} — {row['created_at'][:16]}"):
                st.write(row["content"])
                if st.button("🗑️ حذف یادداشت", key=f"delnote_{row['id']}"):
                    delete_note(row["id"])
                    st.rerun()