import streamlit as st
import os
import json
import time
import re
import urllib.request
import urllib.parse
import urllib.error
from datetime import date
from PIL import Image

# ----------------- PAGE CONFIG -----------------
st.set_page_config(
    page_title="ZENO AI | English Coach Core",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- DATABASE / PERSISTENCE -----------------
USERS_FILE = "users_db.json"
HISTORY_FILE = "chat_history_data.json"

def load_data(filename, default_val):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return default_val

def save_data(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ----------------- PASSWORD STRENGTH CHECK -----------------
def is_strong_password(password):
    if len(password) < 8:
        return False, "Password minimum 8 characters erbeku."
    if not re.search(r"\d", password):
        return False, "Password nalli ondhu number (0-9) erbeku."
    if not re.search(r"[@#$%^&*!_\-+=]", password):
        return False, "Password nalli ondhu special symbol (@, #, $, %, &, *, !) erbeku."
    return True, "Strong Password!"

# ----------------- ROTATING DAILY TOPICS -----------------
DAILY_TOPICS = [
    {
        "title": "Polite Workplace Requests",
        "lesson": "Instead of saying 'Give me that file', say 'Could you please share that file with me?'. It creates immediate respect.",
        "phrase": "Could you please help me with this task?"
    },
    {
        "title": "Natural Daily Routine",
        "lesson": "Avoid saying 'Today morning I came'. Always say 'This morning I came'. It sounds fluent and natural.",
        "phrase": "This morning I started my project practice."
    },
    {
        "title": "Food & Cafe Ordering",
        "lesson": "Don't say 'Give me coffee'. Use 'Can I please get a cup of coffee?' or 'I would like to order a tea'.",
        "phrase": "Can I get a hot coffee with less sugar?"
    },
    {
        "title": "Handling Mistakes Gracefully",
        "lesson": "When a mistake happens, don't say sorry repeatedly. Say: 'My apologies, allow me to clarify that.'",
        "phrase": "Pardon me, let me rephrase that."
    },
    {
        "title": "Expressing Opinions Confidently",
        "lesson": "Instead of repeatedly saying 'I think', use 'From my perspective' or 'In my view'.",
        "phrase": "From my perspective, this approach is faster."
    }
]

def get_today_topic():
    day_idx = date.today().timetuple().tm_yday % len(DAILY_TOPICS)
    return DAILY_TOPICS[day_idx]

# ----------------- NEON CYBERPUNK STYLING -----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800;900&family=Rajdhani:wght@500;600;700&display=swap');

    .stApp {
        background: radial-gradient(circle at 50% 10%, #0d1238 0%, #040614 60%, #010208 100%);
        color: #e0f7fa;
        font-family: 'Rajdhani', sans-serif;
    }

    [data-testid="stSidebar"] {
        background-color: #080c24 !important;
        border-right: 1.5px solid #00f2fe;
    }

    .zeno-brand {
        font-family: 'Orbitron', sans-serif;
        font-size: 2.2rem;
        font-weight: 900;
        letter-spacing: 2px;
        background: linear-gradient(90deg, #00f2fe 0%, #00ffcc 50%, #ff007f 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 20px rgba(0, 242, 254, 0.4);
        margin-bottom: 2px;
    }

    .enter-card {
        background: rgba(13, 20, 50, 0.9);
        border: 2px solid #00f2fe;
        box-shadow: 0 0 35px rgba(0, 242, 254, 0.35);
        border-radius: 20px;
        padding: 30px 20px;
        text-align: center;
        backdrop-filter: blur(12px);
        margin: 20px auto;
        max-width: 550px;
    }

    .daily-card {
        background: linear-gradient(135deg, rgba(0, 242, 254, 0.16) 0%, rgba(255, 0, 127, 0.2) 100%);
        border: 1.5px solid #00f2fe;
        border-radius: 16px;
        padding: 14px 18px;
        margin: 10px 0 14px 0;
        box-shadow: 0 0 20px rgba(0, 242, 254, 0.2);
    }

    .install-card {
        background: rgba(10, 25, 55, 0.9);
        border: 1.5px solid #00ffcc;
        border-radius: 16px;
        padding: 16px 20px;
        margin-bottom: 14px;
        box-shadow: 0 0 20px rgba(0, 255, 204, 0.25);
    }

    .visible-box {
        background: rgba(15, 23, 58, 0.85);
        border: 1px solid #00ffcc;
        border-radius: 14px;
        padding: 14px;
        margin-bottom: 12px;
        box-shadow: 0 0 15px rgba(0, 255, 204, 0.15);
    }

    .storage-badge {
        background: rgba(0, 242, 254, 0.12);
        border: 1px solid #00f2fe;
        color: #80deea;
        padding: 5px 12px;
        border-radius: 12px;
        font-size: 0.85rem;
        display: inline-block;
        margin-bottom: 6px;
    }

    div[data-testid="stFileUploader"] {
        background: rgba(10, 16, 42, 0.8);
        border: 1px dashed #00f2fe;
        border-radius: 12px;
        padding: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SESSION STATE & LOGIN PERSISTENCE -----------------
query_user = st.query_params.get("user", "")

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = query_user if query_user else None

if "guest_start_time" not in st.session_state:
    st.session_state.guest_start_time = time.time()

if "spoken_daily_topic" not in st.session_state:
    st.session_state.spoken_daily_topic = False

if "guest_messages" not in st.session_state:
    st.session_state.guest_messages = [
        {"role": "assistant", "content": "Welcome! I am Zeno, your English coach. Speak or type to practice!"}
    ]

# ----------------- GROQ API CALLER -----------------
def call_groq_api_robust(prompt):
    raw_key = st.secrets.get("GROQ_API_KEY", "") or os.environ.get("GROQ_API_KEY", "")
    if not raw_key:
        return "GROQ_API_KEY Missing! Streamlit Secrets nalli GROQ_API_KEY add maadi."

    keys_list = [k.strip().replace('"', '').replace("'", "") for k in raw_key.split(",") if k.strip()]

    system_instruction = (
        "You are Zeno, a dedicated, highly skilled English language coach and tutor. "
        "Your top priority is to teach English, improve fluency, correct grammar, explain uploaded files or images clearly, "
        "and build communication confidence. "
        "Rules for responding:\n"
        "1. If an image or file is uploaded, explain what it is, its meaning, vocabulary related to it, and how to talk about it in fluent English.\n"
        "2. If the user's input has ANY grammatical error, immediately give the corrected version clearly, then explain briefly.\n"
        "3. If the user writes or asks how to say something in English, teach them the natural spoken way.\n"
        "4. Teach practical vocabulary and conversation phrases.\n"
        "5. Keep responses concise, direct, and conversational (2 to 4 sentences maximum) suitable for speech output.\n"
        "6. Never use markdown symbols like asterisks, hashes, or bullet points."
    )

    last_error = ""

    for api_token in keys_list:
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        models_url = "https://api.groq.com/openai/v1/models"
        available_models = []
        try:
            req_models = urllib.request.Request(models_url, headers=headers, method="GET")
            with urllib.request.urlopen(req_models, timeout=8) as m_resp:
                m_data = json.loads(m_resp.read().decode("utf-8"))
                for m in m_data.get("data", []):
                    m_id = m.get("id", "")
                    if not any(x in m_id.lower() for x in ["whisper", "guard", "vision", "orpheus"]):
                        available_models.append(m_id)
        except Exception:
            available_models = ["llama-3.1-8b-instant", "llama3-8b-8192", "gemma2-9b-it"]

        if not available_models:
            available_models = ["llama-3.1-8b-instant", "llama3-8b-8192"]

        chat_url = "https://api.groq.com/openai/v1/chat/completions"

        for model_name in available_models:
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.5
            }
            body_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(chat_url, data=body_data, headers=headers, method="POST")

            try:
                with urllib.request.urlopen(req, timeout=15) as response:
                    res = json.loads(response.read().decode("utf-8"))
                    return res["choices"][0]["message"]["content"]
            except urllib.error.HTTPError as e:
                err_text = e.read().decode("utf-8")
                last_error = f"Groq ({model_name}): {err_text}"
                continue
            except Exception as e:
                last_error = f"Error: {str(e)}"
                continue

    return f"API Issue: {last_error}"

# ----------------- TIME & AUTH RULES -----------------
is_logged_in = st.session_state.logged_in_user is not None

if not is_logged_in:
    elapsed_seconds = int(time.time() - st.session_state.guest_start_time)
    time_limit_reached = (elapsed_seconds >= 60)
else:
    time_limit_reached = False

# ----------------- SIGN IN / SIGN UP (ONLY FOR GUEST AFTER 1 MIN) -----------------
if not is_logged_in and time_limit_reached:
    st.markdown("""
    <div class="enter-card">
        <div style="color: #ff007f; font-weight: 800; letter-spacing: 2px;">⚠️ 1-MINUTE FREE TRIAL COMPLETED</div>
        <div class="zeno-brand">⚡ ZENO AI ⚡</div>
        <p style="color: #e0f7fa; font-size: 1.05rem; margin-top: 5px;">
            Ondu sala <b>Sign In</b> athava <b>Sign Up</b> maadi. Admele yavathoo login kelalla, permanent aagi chat save aagirathe!
        </p>
    </div>
    """, unsafe_allow_html=True)

    auth_tab1, auth_tab2 = st.tabs(["🔑 Sign In", "📝 Create Account (Sign Up)"])
    users_db = load_data(USERS_FILE, {})

    with auth_tab1:
        st.subheader("Sign In Once")
        login_id = st.text_input("Username", key="login_id")
        login_pwd = st.text_input("Password", type="password", key="login_pwd")
        
        if st.button("🚀 Sign In & Continue Forever", use_container_width=True):
            user_record = users_db.get(login_id)
            if user_record:
                saved_pwd = user_record["password"] if isinstance(user_record, dict) else user_record
                if saved_pwd == login_pwd:
                    st.session_state.logged_in_user = login_id
                    st.query_params["user"] = login_id
                    st.session_state.spoken_daily_topic = False
                    
                    all_histories = load_data(HISTORY_FILE, {})
                    if login_id not in all_histories:
                        all_histories[login_id] = st.session_state.guest_messages
                    else:
                        all_histories[login_id].extend(st.session_state.guest_messages[1:])
                    save_data(HISTORY_FILE, all_histories)
                    st.rerun()
                else:
                    st.error("Invalid Password!")
            else:
                st.error("User not found. Sign Up maadi.")

    with auth_tab2:
        st.subheader("New User Registration")
        st.info("Password rule: Minimum 8 characters, 1 number, mathu 1 special symbol (@, #, $, %).")
        new_id = st.text_input("Choose Username", key="reg_id")
        new_pwd = st.text_input("Create Password", type="password", key="reg_pwd")
        new_pwd_confirm = st.text_input("Confirm Password", type="password", key="reg_pwd_confirm")

        if st.button("✨ Create Account & Enter", use_container_width=True):
            is_valid, msg = is_strong_password(new_pwd)
            if not new_id or not new_pwd:
                st.warning("Ella details fill maadi.")
            elif not is_valid:
                st.error(msg)
            elif new_pwd != new_pwd_confirm:
                st.error("Passwords match aagthilla!")
            elif new_id in users_db:
                st.error("Username already registered ide. Sign In maadi.")
            else:
                users_db[new_id] = {"password": new_pwd}
                save_data(USERS_FILE, users_db)
                st.session_state.logged_in_user = new_id
                st.query_params["user"] = new_id
                st.session_state.spoken_daily_topic = False

                all_histories = load_data(HISTORY_FILE, {})
                all_histories[new_id] = st.session_state.guest_messages
                save_data(HISTORY_FILE, all_histories)
                st.rerun()

# ----------------- MAIN TUTOR SCREEN (WITH LEFT SIDEBAR HISTORY) -----------------
else:
    all_histories = load_data(HISTORY_FILE, {})
    today_topic = get_today_topic()

    if not is_logged_in:
        current_user = "Guest"
        user_messages = st.session_state.guest_messages
        remaining_sec = max(0, 60 - elapsed_seconds)
    else:
        current_user = st.session_state.logged_in_user
        if current_user not in all_histories:
            all_histories[current_user] = [
                {"role": "assistant", "content": f"Hello {current_user}! Today's English lesson is ready. Let's practice speaking together!"}
            ]
        user_messages = all_histories[current_user]

    # ================= LEFT SIDEBAR (SAVED CHAT HISTORY) =================
    with st.sidebar:
        st.markdown('<div class="zeno-brand" style="font-size: 1.5rem;">📁 CHAT HISTORY</div>', unsafe_allow_html=True)
        st.caption(f"User: **{current_user}**")

        if st.button("➕ New Chat Session", use_container_width=True):
            new_welcome = f"Hello {current_user}! Fresh conversation started. What would you like to practice now?"
            if not is_logged_in:
                st.session_state.guest_messages = [{"role": "assistant", "content": new_welcome}]
            else:
                all_histories[current_user] = [{"role": "assistant", "content": new_welcome}]
                save_data(HISTORY_FILE, all_histories)
            st.rerun()

        st.markdown("---")
        st.markdown("### 💬 Saved Conversations")
        
        if len(user_messages) <= 1:
            st.write("No previous conversations yet.")
        else:
            user_queries = [m["content"] for m in user_messages if m["role"] == "user"]
            for query in reversed(user_queries[-15:]):
                preview_text = query[:28] + "..." if len(query) > 28 else query
                st.markdown(f"🗨️ **{preview_text}**")

        st.markdown("---")
        chat_json_str = json.dumps(user_messages, indent=2)
        st.download_button("📥 Export JSON History", data=chat_json_str, file_name=f"{current_user}_chat.json", mime="application/json", use_container_width=True)

        if is_logged_in:
            if st.button("🚪 Sign Out", use_container_width=True):
                st.session_state.logged_in_user = None
                st.query_params.clear()
                st.session_state.guest_start_time = time.time()
                st.session_state.spoken_daily_topic = False
                st.rerun()

    # ================= MAIN CONTENT HEADER =================
    head_col1, head_col2 = st.columns([3, 1])
    with head_col1:
        st.markdown('<div class="zeno-brand">⚡ ZENO AI | ENGLISH COACH ⚡</div>', unsafe_allow_html=True)
        if not is_logged_in:
            st.markdown(f'<div class="storage-badge" style="border-color: #ff007f; color: #ff80bf;">⏳ Free Trial: <b>{remaining_sec}s left</b></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="storage-badge">✅ Permanent Login: <b>{current_user}</b> | Left Sidebar History Active ({len(user_messages)} msgs)</div>', unsafe_allow_html=True)

    # ================= 1. HOW TO DOWNLOAD & INSTALL APP (IN ENGLISH) =================
    st.markdown("""
    <div class="install-card">
        <div style="color: #00ffcc; font-family: 'Orbitron'; font-size: 1.15rem; font-weight: bold; margin-bottom: 6px;">
            📲 How to Download & Install Zeno AI App
        </div>
        <div style="color: #e0f7fa; font-size: 1rem; line-height: 1.6;">
            <b>For Android & PC (Google Chrome):</b><br/>
            1. Open this website in your <b>Chrome Browser</b>.<br/>
            2. Tap the <b>3 dots menu (⋮)</b> in the top right corner.<br/>
            3. Tap <b>"Install app"</b> or <b>"Add to Home screen"</b>.<br/>
            4. Click <b>"Install"</b>. The Zeno AI icon will appear directly on your home screen or desktop like a native app.<br/>
            <br/>
            <b>For iPhone (Safari):</b><br/>
            1. Tap the <b>Share Button</b> at the bottom of the screen.<br/>
            2. Scroll down and tap <b>"Add to Home Screen"</b>.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ================= 2. DIRECT IMAGE & FILE EXPLANATION PANEL =================
    st.markdown('<div class="visible-box"><b>🖼️ Send Image or File to Zeno for Instant English Explanation</b></div>', unsafe_allow_html=True)
    up_c1, up_c2 = st.columns([2, 1])
    with up_c1:
        up_file = st.file_uploader("Upload Image, Document, or Audio", type=["png", "jpg", "jpeg", "mp3", "wav", "pdf", "txt"], key="main_visible_uploader", label_visibility="collapsed")
        file_msg = st.text_input("Ask Zeno about this file (Optional):", placeholder="e.g. Explain this image in simple English and teach me new words", key="direct_file_caption")
    with up_c2:
        if up_file:
            st.success(f"Attached: {up_file.name}")
            if up_file.type.startswith("image/"):
                st.image(up_file, width=150)
            elif up_file.type.startswith("audio/"):
                st.audio(up_file)
            if st.button("📤 Explain this with Zeno AI", use_container_width=True):
                user_question = file_msg if file_msg.strip() else f"Please explain this uploaded image or file named {up_file.name}. Describe what you see and teach me how to talk about it in fluent English."
                user_messages.append({"role": "user", "content": f"📎 [Uploaded: {up_file.name}] {user_question}"})
                
                ai_prompt = (
                    f"The user has uploaded a file named '{up_file.name}' of type '{up_file.type}'. "
                    f"The user prompt is: '{user_question}'. "
                    "As an expert English tutor, explain the topic clearly, describe key visual/content points in simple sentences, "
                    "provide 2 useful vocabulary words related to it, and give a natural English phrase they can practice speaking."
                )
                bot_reply = call_groq_api_robust(ai_prompt)
                clean_r = bot_reply.replace("*", "").replace("#", "").replace('"', '').replace("'", "").strip()
                user_messages.append({"role": "assistant", "content": clean_r})
                if is_logged_in:
                    all_histories[current_user] = user_messages
                    save_data(HISTORY_FILE, all_histories)
                st.rerun()

    # DAILY NOTIFICATION BANNER
    st.markdown(f"""
    <div class="daily-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="color: #00ffcc; font-weight: 800; font-family: 'Orbitron'; font-size: 1rem;">🔔 DAILY TOPIC: {today_topic['title']}</span>
            <span style="color: #ff007f; font-weight: bold; font-size: 0.85rem;">⭐ TODAY'S LESSON</span>
        </div>
        <p style="color: #e0f7fa; font-size: 1.05rem; margin: 6px 0 2px 0;">{today_topic['lesson']}</p>
        <div style="color: #80deea; font-size: 0.95rem;"><b>💬 Practice Saying:</b> <i>"{today_topic['phrase']}"</i></div>
    </div>
    """, unsafe_allow_html=True)

    # AUTO VOICE WELCOME
    if not st.session_state.spoken_daily_topic:
        st.session_state.spoken_daily_topic = True
        greeting_name = "there" if not is_logged_in else current_user
        spoken_daily = f"Hello {greeting_name}! Today's English topic is {today_topic['title']}. {today_topic['lesson']} Try repeating after me: {today_topic['phrase']}"
        st.components.v1.html(f"""
        <script>
            if ('speechSynthesis' in window) {{
                window.speechSynthesis.cancel();
                const utter = new SpeechSynthesisUtterance("{spoken_daily}");
                utter.rate = 1.0;
                utter.onend = () => {{
                    window.dispatchEvent(new CustomEvent('zeno_speech_ended'));
                }};
                window.speechSynthesis.speak(utter);
            }}
        </script>
        """, height=0)

    # DISPLAY CHAT HISTORY
    for msg in user_messages:
        avatar = "🎓" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            if msg.get("image_url"):
                st.image(msg["image_url"], caption="Generated Illustration")
            st.markdown(msg["content"])

    # ================= 3. DIRECT FUNCTIONING MIC COMPONENT =================
    mic_html = """
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin: 10px 0;">
        <div style="display: flex; align-items: center; gap: 14px;">
            <button id="micBtn" type="button" style="
                background: linear-gradient(45deg, #00f2fe, #ff007f);
                border: 2px solid #ffffff;
                color: #ffffff;
                padding: 12px 30px;
                border-radius: 28px;
                font-weight: 800;
                font-size: 15px;
                cursor: pointer;
                box-shadow: 0 0 22px rgba(0, 242, 254, 0.6);
                letter-spacing: 1px;
                outline: none;
                display: inline-flex;
                align-items: center;
                gap: 8px;
            ">🎙️ TOUCH TO SPEAK (MICROPHONE)</button>
            <span id="micStatus" style="color: #00ffcc; font-size: 14px; font-weight: 700;">Tap button & speak clearly</span>
        </div>
        <div id="heardBox" style="color: #ff80bf; font-size: 13px; margin-top: 5px; font-weight: bold;"></div>
    </div>

    <script>
        const btn = document.getElementById('micBtn');
        const status = document.getElementById('micStatus');
        const heardBox = document.getElementById('heardBox');
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRec) {
            status.innerText = "Please open this site in Google Chrome on PC or Android.";
        } else {
            const rec = new SpeechRec();
            rec.continuous = false;
            rec.interimResults = false;
            rec.lang = 'en-US';

            let listening = false;

            btn.onclick = async () => {
                if (listening) {
                    rec.stop();
                    return;
                }
                try {
                    // Direct media stream check to force Chrome permission popup
                    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                        stream.getTracks().forEach(t => t.stop());
                    }
                    rec.start();
                    listening = true;
                    status.innerText = "🔴 Listening... Speak in English now!";
                    btn.style.background = "#ff0055";
                    btn.innerText = "🛑 STOP LISTENING";
                    heardBox.innerText = "";
                } catch (err) {
                    status.innerText = "Permission Denied! Click lock icon (🔒) near URL to Allow Mic.";
                    resetUi();
                }
            };

            rec.onresult = (e) => {
                const transcript = e.results[0][0].transcript;
                status.innerText = "Processing: " + transcript;
                heardBox.innerText = "Zeno heard: '" + transcript + "'";

                const parentDoc = window.parent.document;
                const textarea = parentDoc.querySelector('textarea[aria-label="Ask Zeno or type \'image: car\' to generate..."]') ||
                                 parentDoc.querySelector('textarea[data-testid="stChatInputTextArea"]');

                if (textarea) {
                    const proto = window.HTMLTextAreaElement.prototype;
                    const nativeSet = Object.getOwnPropertyDescriptor(proto, "value").set;
                    nativeSet.call(textarea, transcript);
                    textarea.dispatchEvent(new Event('input', { bubbles: true }));

                    setTimeout(() => {
                        const submitBtn = parentDoc.querySelector('button[data-testid="stChatInputSubmitButton"]') ||
                                          parentDoc.querySelector('button[kind="secondaryFormSubmit"]');
                        if (submitBtn) {
                            submitBtn.click();
                        } else {
                            const enterEvt = new KeyboardEvent('keydown', {
                                bubbles: true,
                                cancelable: true,
                                key: 'Enter',
                                code: 'Enter',
                                keyCode: 13
                            });
                            textarea.dispatchEvent(enterEvt);
                        }
                    }, 400);
                }
                resetUi();
            };

            rec.onerror = (e) => {
                if (e.error === 'not-allowed') {
                    status.innerText = "Microphone blocked in Chrome. Please allow it in Site settings.";
                } else if (e.error === 'no-speech') {
                    status.innerText = "No speech detected. Tap and speak again.";
                } else {
                    status.innerText = "Error: " + e.error + ". Tap to retry.";
                }
                resetUi();
            };

            rec.onend = () => {
                resetUi();
            };

            function resetUi() {
                listening = false;
                btn.style.background = "linear-gradient(45deg, #00f2fe, #ff007f)";
                btn.innerText = "🎙️ TOUCH TO SPEAK (MICROPHONE)";
            }
        }
    </script>
    """
    st.components.v1.html(mic_html, height=72)

    # CHAT INPUT BOX
    user_prompt = st.chat_input("Ask Zeno or type 'image: car' to generate...")

    if user_prompt:
        user_messages.append({"role": "user", "content": user_prompt})
        if is_logged_in:
            all_histories[current_user] = user_messages
            save_data(HISTORY_FILE, all_histories)

        with st.chat_message("user", avatar="👤"):
            st.markdown(user_prompt)

        with st.chat_message("assistant", avatar="🎓"):
            lower_input = user_prompt.lower().strip()
            
            # AI Image Generation
            if lower_input.startswith("image:") or lower_input.startswith("generate image:"):
                img_desc = user_prompt.split(":", 1)[1].strip()
                encoded_desc = urllib.parse.quote(img_desc)
                gen_image_url = f"https://image.pollinations.ai/prompt/{encoded_desc}?width=768&height=768&nologo=true"
                
                reply_txt = f"Here is the generated image for: {img_desc}"
                st.image(gen_image_url, caption=f"Prompt: {img_desc}")
                st.markdown(reply_txt)

                user_messages.append({"role": "assistant", "content": reply_txt, "image_url": gen_image_url})
                if is_logged_in:
                    all_histories[current_user] = user_messages
                    save_data(HISTORY_FILE, all_histories)

                tts_script = """
                <script>
                    if ('speechSynthesis' in window) {
                        window.speechSynthesis.cancel();
                        window.speechSynthesis.speak(new SpeechSynthesisUtterance("Here is the visual generated for you."));
                    }
                </script>
                """
                st.components.v1.html(tts_script, height=0)

            # English Tutor Response
            else:
                raw_reply = call_groq_api_robust(user_prompt)
                clean_reply = raw_reply.replace("*", "").replace("#", "").replace('"', '').replace("'", "").strip()
                st.markdown(clean_reply)

                user_messages.append({"role": "assistant", "content": clean_reply})
                if is_logged_in:
                    all_histories[current_user] = user_messages
                    save_data(HISTORY_FILE, all_histories)

                spoken_text = clean_reply[:250].replace("\\", "")
                tts_js = f"""
                <script>
                    if ('speechSynthesis' in window) {{
                        window.speechSynthesis.cancel();
                        const speakNow = () => {{
                            const voices = window.speechSynthesis.getVoices();
                            const utterance = new SpeechSynthesisUtterance("{spoken_text}");
                            const targetVoice = voices.find(v => (v.name.includes('Google') || v.name.includes('Natural') || v.name.includes('Female')) && v.lang.startsWith('en')) || voices.find(v => v.lang.startsWith('en'));
                            if (targetVoice) utterance.voice = targetVoice;
                            utterance.pitch = 1.0;
                            utterance.rate = 1.0;
                            window.speechSynthesis.speak(utterance);
                        }};
                        if (window.speechSynthesis.getVoices().length > 0) {{
                            speakNow();
                        }} else {{
                            window.speechSynthesis.onvoiceschanged = speakNow;
                        }}
                    }}
                </script>
                """
                st.components.v1.html(tts_js, height=0)
