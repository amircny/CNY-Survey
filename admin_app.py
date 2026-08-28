# admin_app.py — robust admin panel (Streamlit >= 1.30)
import os
import requests
import streamlit as st
API = os.getenv("SURVEY_API", "http://localhost:8000")
# API = "http://127.0.0.1:8000"  # آدرس بک‌اند FastAPI شما

st.set_page_config(
    page_title="CNY Survey Admin",
    page_icon="🛠",
    layout="wide"
)

st.markdown("""
<style>

body {
    background:#f5f8ff;
}

.admin-title {
    font-size:34px;
    font-weight:800;
    color:#0b1f55;
    margin-bottom:20px;:
}

.admin-card {

    background:white;

    padding:25px;

    border-radius:20px;

    border:1px solid #dbe7ff;

    box-shadow:
    0 10px 30px rgba(21,87,255,0.10);

    margin-bottom:20px;

}

.question-card {

    background:white;
    padding:20px;
    border-radius:18px;
    border:1px solid #dbe7ff;
    box-shadow:0 8px 25px rgba(0,0,0,0.08);
    margin-bottom:20px;

}


.question-title {

    font-size:20px;
    font-weight:800;
    color:#0b1f55;

}


.option-item {

    padding:5px 0;
    color:#475569;

}

.stButton button {

    border-radius:12px !important;

    font-weight:700 !important;

}


</style>
""", unsafe_allow_html=True)


st.markdown(
"""
<div class="admin-title">
🛠 CNY Survey Admin Panel
</div>
""",
unsafe_allow_html=True
)




# ---------- Password Source (secrets -> ENV -> default) ----------
def get_admin_password() -> str:
    # 1) secrets.toml  (.streamlit/secrets.toml یا مسیر کاربر)
    try:
        val = st.secrets.get("ADMIN_PASSWORD", None)
        if val:
            return str(val)
    except Exception:
        pass
    # 2) متغیّر محیطی
    env_val = os.getenv("ADMIN_PASSWORD")
    if env_val:
        return env_val
    # 3) پیش‌فرض (فقط برای توسعه/لوکال)
    return "AmirStrongPass2025"


ADMIN_PASSWORD = get_admin_password()


# ---------- Session & Auth ----------
if "auth" not in st.session_state:
    st.session_state.auth = False

if "delete_confirm" not in st.session_state:
    st.session_state.delete_confirm = None

with st.form("login_form", clear_on_submit=False):
    pwd = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Login")
    if submitted:
        if pwd == ADMIN_PASSWORD:
            st.session_state.auth = True
            st.success("Logged in.")
            st.rerun()
        else:
            st.error("Wrong password. (Using secrets/env/default fallback)")


if not st.session_state.auth:
    st.stop()

# اختیاری: دکمه‌ی خروج
st.markdown("### Export")
st.link_button(
    "⬇️ Download Complete Data",
    f"{API}/export_complete.xlsx"
)

with st.sidebar:
    if st.button("Logout"):
        st.session_state.auth = False
        st.rerun()

st.success("Logged in.")

#.........................................
st.markdown("### Database Management")

if "clear_confirm" not in st.session_state:
    st.session_state.clear_confirm = False


if st.button("🗑 Clear Survey Data"):

    st.session_state.clear_confirm = True


if st.session_state.clear_confirm:

    st.warning(
        "⚠️ Are you sure? All responses and tracking data will be deleted. Questions will remain."
    )

    c1, c2 = st.columns(2)

    with c1:
        if st.button("Yes, Delete All Data"):

            try:
                r = requests.delete(
                    f"{API}/clear_data",
                    timeout=10
                )

                r.raise_for_status()

                st.success("All survey data deleted.")

                st.session_state.clear_confirm = False

            except Exception as e:
                st.error(f"Delete failed: {e}")


    with c2:
        if st.button("Cancel"):

            st.session_state.clear_confirm = False
# ---------- API helpers ----------
@st.cache_data(ttl=3)
def get_questions():
    r = requests.get(f"{API}/questions", timeout=6)
    r.raise_for_status()
    return r.json().get("questions", [])


def create_question(payload: dict):
    r = requests.post(f"{API}/question", json=payload, timeout=8)
    r.raise_for_status()
    return r.json()


def update_question(qid: int, payload: dict):
    r = requests.put(f"{API}/question/{qid}", json=payload, timeout=8)
    r.raise_for_status()
    return r.json()


def delete_question(qid: int):
    r = requests.delete(f"{API}/question/{qid}", timeout=8)
    r.raise_for_status()
    return r.json()


# ---------- Create new question ----------
# ---------- Create New Question (Improved UI) ----------

st.markdown(
"""
<div class="admin-card">
<h2>➕ Create New Question</h2>
<p>Create survey questions easily.</p>
</div>
""",
unsafe_allow_html=True
)


new_text = st.text_input(
    "Question",
    placeholder="Example: What is your preferred transport mode?"
)


col1, col2 = st.columns(2)

with col1:
    new_type = st.selectbox(
        "Question Type",
        [
            "single",
            "multi",
            "text"
        ]
    )

with col2:
    new_order = st.number_input(
        "Question Order",
        min_value=1,
        value=1,
        step=1
    )


new_options = []


# فقط برای سوال‌های دارای گزینه
if new_type != "text":

    option_number = st.number_input(
        "Number of options",
        min_value=2,
        max_value=10,
        value=4,
        step=1
    )


    st.markdown("### Options")


    for i in range(int(option_number)):

        option_text = st.text_input(
            f"Option {i+1}",
            key=f"new_option_{i}"
        )


        if option_text.strip():

            new_options.append(
                {
                    "code": f"option_{i+1}",
                    "label": option_text.strip(),
                    "oorder": i
                }
            )


if st.button(
    "💾 Save Question",
    use_container_width=True
):

    try:

        res = create_question(
            {
                "text": new_text,
                "qtype": new_type,
                "qorder": int(new_order),
                "options": new_options
            }
        )


        st.success(
            f"Question saved successfully (ID: {res.get('id')})"
        )

        get_questions.clear()


    except Exception as e:

        st.error(
            f"Save failed: {e}"
        )

st.divider()


# ---------- Existing questions ----------
st.markdown(
"""
<div class="admin-card">
<h2>📝 Question Management</h2>
<p>View, update and manage survey questions.</p>
</div>
""",
unsafe_allow_html=True
)
try:
    qs = get_questions()
except Exception as e:
    st.error(f"Load questions failed: {e}")
    qs = []

if not qs:
    st.info("No questions.")
else:
    for q in qs:
        with st.expander(f"[{q['id']}] {q['text']}"):
            t = st.text_input("Text", value=q["text"], key=f"t_{q['id']}")
            tp = st.selectbox(
                "Type", ["single", "multi", "text"],
                index=["single", "multi", "text"].index(q["type"]),
                key=f"type_{q['id']}"
            )
            ordr = st.number_input("Order", value=q.get("order", 0), step=1, key=f"ord_{q['id']}")

            cur = ", ".join([f"{o['code']}:{o['label']}" for o in q.get("options", [])])
            raw2 = st.text_area("Options (code:Label, comma separated)", value=cur, key=f"opts_{q['id']}")

            newopts = []
            if tp != "text" and raw2.strip():
                for i, chunk in enumerate([x.strip() for x in raw2.split(",") if x.strip()]):
                    if ":" in chunk:
                        code, label = chunk.split(":", 1)
                        newopts.append({"code": code.strip(), "label": label.strip(), "oorder": i})

            c1, c2 = st.columns(2)
            with c1:
                if st.button("Update", key=f"upd_{q['id']}"):
                    try:
                        update_question(
                            q["id"],
                            {
                                "text": t,
                                "qtype": tp,
                                "qorder": int(ordr),
                                "options": newopts
                            }
                        )
                        st.success("Updated.")
                        get_questions.clear()

                    except Exception as e:
                        st.error(f"Update failed: {e}")


            with c2:

                if st.button(
                    "🗑 Delete",
                    key=f"del_{q['id']}"
                ):
                    st.session_state.delete_confirm = q["id"]


                if st.session_state.delete_confirm == q["id"]:

                    st.warning(
                        "⚠️ Are you sure you want to delete this question?"
                    )

                    confirm_col, cancel_col = st.columns(2)


                    with confirm_col:

                        if st.button(
                            "Yes, Delete",
                            key=f"yes_del_{q['id']}"
                        ):

                            try:
                                delete_question(q["id"])

                                st.success(
                                    "Question deleted."
                                )

                                st.session_state.delete_confirm = None
                                get_questions.clear()
                                st.rerun()

                            except Exception as e:
                                st.error(
                                    f"Delete failed: {e}"
                                )


                    with cancel_col:

                        if st.button(
                            "Cancel",
                            key=f"cancel_del_{q['id']}"
                        ):

                            st.session_state.delete_confirm = None
                            st.rerun()