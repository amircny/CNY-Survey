# survey_app.py — final (syntax-checked)
import os, json, requests, streamlit as st
from pathlib import Path
import streamlit.components.v1 as components
import time
import os
API = os.getenv("SURVEY_API", "http://localhost:8000")

#st.set_page_config(page_title="Project Survey", page_icon="📋", layout="centered")
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
    direction: ltr;
    text-align: left;
}

h1, h2, h3, h4, h5, h6, p, label, span, div {
    direction: ltr;
    text-align: left;
}

/* دکمه‌ها و ورودی‌ها */
button, [data-testid="stTextInput"], [data-testid="stTextArea"] {
    direction: ltr !important;
    text-align: left !important;
}

/* شماره سؤال در سمت راست */
.q-index {
    left: 0 !important;
    right: auto !important;
}
header[data-testid="stHeader"] {
    display: none;
}

.block-container {
    padding-top: 0rem !important;
}

#MainMenu {
    display: none;
}

footer {
    display: none;
}
</style>
""", unsafe_allow_html=True)

# CSS
CSS_PATH = os.path.join("assets", "style.css")
if os.path.exists(CSS_PATH):
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Hero banner
ASSETS = Path(__file__).parent / "assets"

def find_img(name_candidates):
    for n in name_candidates:
        p = ASSETS / n
        if p.exists(): return str(p)
    return None

banner = find_img(["header.png","header.jpg","header.jpeg"])
# tighter spacing + not full screen

left, center, right = st.columns([1,8,1])
with center:
    st.markdown('<div class="header-wrap">', unsafe_allow_html=True)
    if banner:
     st.image(banner, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

if not banner:
    st.caption(f"Put image in: {ASSETS} (header.png/jpg)")

if "survey_start_time" not in st.session_state:
    st.session_state.survey_start_time = time.time()

if "tracking_clicks" not in st.session_state:
    st.session_state.tracking_clicks = 0

if "first_click_time" not in st.session_state:
    st.session_state.first_click_time = None

#......................................................................
components.html(
"""
<script>
console.log("TRACKING LOADED");
let mouseClicks = 0;
let touchEvents = 0;

let firstMouseClick = null;
let firstTouch = null;
let surveyStart = Date.now();

function sendEvent(type, x, y){

    let now = (Date.now() - surveyStart) / 1000;


    if(type === "click"){

        mouseClicks++;

        if(firstMouseClick === null){
            firstMouseClick = now;
        }

    }


    if(type === "touch"){

        touchEvents++;

        if(firstTouch === null){
            firstTouch = now;
        }

    }


    fetch("http://localhost:8000/tracking_event", {

        method:"POST",

        headers:{
            "Content-Type":"application/json"
        },

        body:JSON.stringify({

            event:type,

            mouse_clicks:mouseClicks,

            touch_events:touchEvents,

            first_mouse_click:firstMouseClick,

            first_touch:firstTouch,

            x:x,

            y:y,

            device:navigator.userAgent

        })

    });

}



// Mouse
window.parent.document.addEventListener(
"click",
function(event){

sendEvent(
"click",
event.clientX,
event.clientY
);

});



// Touch
window.parent.document.addEventListener(
"touchstart",
function(event){

sendEvent(
"touch",
event.touches[0].clientX,
event.touches[0].clientY
);

});


</script>
""",
height=1,
)
#------------------------------------------------------------------

@st.cache_data(ttl=5)
def fetch_questions():
    r = requests.get(f"{API}/questions", timeout=8)
    r.raise_for_status()
    data = r.json().get("questions", [])
    data.sort(key=lambda q: (q.get("order", 0), q.get("id", 0)))
    return data

def submit_answers(payload: dict):
    r = requests.post(f"{API}/submit", json=payload, timeout=12)
    r.raise_for_status()
    return r.json()

def get_tracking_buffer():
    r = requests.get(f"{API}/tracking_buffer", timeout=8)
    r.raise_for_status()
    return r.json()

def send_tracking(payload: dict):
    r = requests.post(f"{API}/tracking", json=payload, timeout=8)
    r.raise_for_status()
    return r.json()

# Load questions
try:
    questions = fetch_questions()
except Exception as e:
    st.error(f"Could not load questions from backend: {e}")
    st.stop()

if not questions:
    st.info("No questions available yet.")
    st.stop()


# Session
if "answers" not in st.session_state:
    st.session_state.answers = {}
# HERE PUT PROGRESS CODE
# Meta row
st.markdown(
    f"""
<div class="meta-row">
  <span class="badge">Questions: {len(questions)}</span>
</div>
""",
    unsafe_allow_html=True,
)

# Form (styled via CSS on [data-testid="stForm"])
with st.form("survey_form"):
    for idx, q in enumerate(questions, start=1):
        qid   = q["id"]
        qtext = q["text"]
        qtype = q.get("type", "single")
        opts  = q.get("options", [])
        key_base = f"q_{qid}"

        # --- فقط یک بار سربرگ سؤال ---
        st.markdown(
            f"""
        <div class="question">
          <div class="q-index">{idx:02d}</div>
          <div class="q-text">{qtext}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # --- ویجت مطابق نوع سؤال ---
        if qtype == "single":
            labels = [o["label"] for o in opts]
            label_to_code = {o["label"]: o["code"] for o in opts}
            choice = st.radio(
                label="", options=labels if labels else ["(no options)"],
                key=key_base, horizontal=False, label_visibility="collapsed",
            )
            st.session_state.answers[qid] = label_to_code.get(choice, "")

        elif qtype == "multi":
            selected_codes = []
            for o in opts:          # ترتیب گزینه‌ها = بک‌اند
                code, label = o["code"], o["label"]
                chk = st.checkbox(label, key=f"{key_base}_{code}")
                if chk:
                    selected_codes.append(code)
            st.session_state[key_base] = selected_codes
            st.session_state.answers[qid] = selected_codes

        else:  # text
            txt = st.text_area(
                label="Your answer", key=f"{key_base}_text",
                height=110, label_visibility="collapsed",
            )
            st.session_state.answers[qid] = (txt or "").strip()

        # جداکننده‌ی بین سؤالات
        st.markdown('<div class="separator"></div>', unsafe_allow_html=True)

    # دکمه‌ها باید داخل همین فرم باشند
    col_left, col_right = st.columns([1, 1])
    with col_left:
        reset = st.form_submit_button("Reset", type="secondary")
    with col_right:
        submitted = st.form_submit_button("Submit", use_container_width=True)


# Actions

if "reset" in locals() and reset:
    st.session_state.answers = {}
    st.rerun()

if "submitted" in locals() and submitted:
    missing = []
    for q in questions:
        ans = st.session_state.answers.get(q["id"])
        ok = (isinstance(ans, list) and len(ans) > 0) if q.get("type") == "multi" else bool(ans)
        if not ok:
            missing.append(q["text"])
   
    if missing:
        st.warning("Please answer all required questions:\n\n- " + "\n- ".join(missing))
    else:
        try:
            payload = {"answers": st.session_state.answers}
            survey_end_time = time.time()
            survey_duration = survey_end_time - st.session_state.survey_start_time
            tracking_data = get_tracking_buffer()
            clicks = tracking_data.get("mouse_clicks", 0)
            first_click = tracking_data.get("first_mouse_click")

            touch_events = tracking_data.get("touch_events", 0)
            first_touch = tracking_data.get("first_touch")

            device = tracking_data.get("device", "unknown")
            tracking_payload = {
                "Recording": "CNY_Survey",
                "Participant": "anonymous",
                "TOI": "Survey",
                "Interval": "Full Survey",
                "AOI": "Survey Page",
                "Duration_of_interval": survey_duration,
                "Total_duration_of_fixations": None,
                "Average_duration_of_fixations": None,
                "Minimum_duration_of_fixations": None,
                "Maximum_duration_of_fixations": None,
                "Number_of_fixations": 0,
                "Number_of_mouse_clicks": clicks,
                "Time_to_first_mouse_click": first_click,
                "Number_of_touch_events": touch_events,
                "Time_to_first_touch": first_touch,
                "Device_type": device
            }
            res = submit_answers(payload)

            if res.get("response_id"):
                tracking_payload["response_id"] = res["response_id"]

            send_tracking(tracking_payload)
            if res.get("ok"):
                
                st.markdown(
                    
                    """
                    
<div class="success-banner">
  ✅ Thank you! Your responses have been submitted.
</div>
""",
                    unsafe_allow_html=True,
                )
                st.session_state.answers = {}
            else:
                st.error(f"Backend did not confirm success: {json.dumps(res)}")
        except Exception as e:
            st.error(f"Submit failed: {e}")
