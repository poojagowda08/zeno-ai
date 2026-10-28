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
    page_title="ZENO AI | Futuristic English Coach",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
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

# ----------------- VIBRANT CYBERPUNK COLOR THEME -----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800;900&family=Rajdhani:wght@500;600;700&display=swap');

    .stApp {
        background: radial-gradient(circle at 50% 10%, #0d1238 0%, #040614 60%, #010208 100%);
        color: #e0f7fa;
        font-family: 'Rajdhani', sans-serif;
    }

    /* Top Brand Title */
    .zeno-brand {
        font-family: 'Orbitron', sans-serif;
        font-size: 2.4rem;
        font-weight: 900;
        letter-spacing: 3px;
        background: linear-gradient(90deg, #00f2fe 0%, #4facfe 35%, #00ffcc 70%, #ff007f 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 25px rgba(0, 242, 254, 0.45);
        margin-bottom: 4px;
    }

    /* Glowing Interactive Card */
    .enter-card {
        background: rgba(13, 20, 50, 0.85);
        border: 2px solid #00f2fe;
        box-shadow: 0 0 45px rgba(0, 242, 254, 0.35), inset 0 0 25px rgba(255, 0, 127, 0.25);
        border-radius: 24px;
        padding: 35px 25px;
        text-align: center;
        backdrop-filter: blur(16px);
        margin: 25px auto;
        max-width: 580px;
    }

    /* Core Orb */
    .orb-wrapper {
        display: flex;
        justify-content: center;
        margin: 14px 0;
    }
    .core-orb {
        width: 70px;
        height: 70px;
        border-radius: 50%;
        background: radial-gradient(circle, #00ffcc 10%, #0072ff 50%, #ff007f 90%);
        box-shadow: 0 0 35px #00f2fe, 0 0 65px rgba(255, 0, 127, 0.75);
        animation: pulseOrb 2s infinite alternate ease-in-out;
    }

    @keyframes pulseOrb {
        0% { transform: scale(0.92); box-shadow: 0 0 20px #00f2fe; }
        100% { transform: scale(1.1); box-shadow: 0 0 50px #00f2fe, 0 0 85px #ff007f; }
    }

    /* Daily Notification Neon Card */
    .daily-card {
        background: linear-gradient(135deg, rgba(0, 242, 254, 0.18) 0%, rgba(255, 0, 127, 0.22) 100%);
        border: 1.5px solid #00f2fe;
        border-radius: 18px;
        padding: 16px 22px;
        margin: 12px 0 16px 0;
        box-shadow: 0 0 25px rgba(0, 242, 254, 0.25);
    }

    .daily-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 1.05rem;
        color: #00ffcc;
        font-weight: 800;
        letter-spacing: 1px;
    }

    /* Badges */
    .storage-badge {
        background: rgba(0, 242, 254, 0.12);
        border: 1px solid #00f2fe;
        color: #80deea;
        padding: 6px 14px;
        border-radius: 14px;
        font-size: 0.88rem;
        display: inline-block;
        margin-bottom: 8px;
    }

    div[data-testid="stFileUploader"] {
        background: rgba(13, 20, 50, 0.7);
        border: 1px dashed #00ffcc;
        border-radius: 14px;
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SESSION STATE & PERSISTENT LOGIN -----------------
query_user = st.query_params.get("user", "")

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = query_user if query_user else None

if "guest_start_time" not in st.session_state:
    st.session_state.guest_start_time = time.time()

if "spoken_daily_topic" not in st.session_state:
    st.session_state.spoken_daily_topic = False

if "guest_messages" not in st.session_state:
    st.session_state.guest_messages = [
        {"role": "assistant", "content": "Welcome! I am Zeno, your English coach. Speak or type to practice. You have 1 minute of free interaction!"}
    ]

# ----------------- DYNAMIC LIVE MODEL GROQ API CALLER -----------------
def call_groq_api_robust(prompt):
    raw_key = st.secrets.get("GROQ_API_KEY", "") or os.environ.get("GROQ_API_KEY", "")
    if not raw_key:
        return "GROQ_API_KEY Missing! Streamlit Secrets nalli GROQ_API_KEY add maadi."

    keys_list = [k.strip().replace('"', '').replace("'", "") for k in raw_key.split(",") if k.strip()]

    system_instruction = (
        "You are Zeno, a dedicated, highly skilled English language coach and tutor. "
        "Your top priority is to teach English, improve fluency, correct grammar, and build communication confidence. "
        "Rules for responding:\n"
        "1. If the user's input has ANY grammatical error, immediately give the corrected version clearly, then explain briefly.\n"
        "2. If the user writes or asks how to say something in English, teach them the natural spoken way.\n"
        "3. Teach practical vocabulary and conversation phrases.\n"
        "4. Keep responses concise, direct, and conversational (2 to 3 sentences maximum) suitable for speech output.\n"
        "5. Never use markdown symbols like asterisks, hashes, or bullet points."
    )

    last_error = ""

    for api_token in keys_list:
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        # Auto-fetch live models available for this key
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

# ----------------- TIME & AUTH DETERMINATION -----------------
is_logged_in = st.session_state.logged_in_user is not None

if not is_logged_in:
    elapsed_seconds = int(time.time() - st.session_state.guest_start_time)
    time_limit_reached = (elapsed_seconds >= 60)
else:
    time_limit_reached = False

# ----------------- AUTHENTICATION OVERLAY (ONLY FOR GUESTS AFTER 1 MIN) -----------------
if not is_logged_in and time_limit_reached:
    st.markdown("""
    <div class="enter-card">
        <div style="color: #ff007f; font-weight: 800; letter-spacing: 2px;">⚠️ 1-MINUTE FREE TRIAL COMPLETED</div>
        <div class="zeno-brand">⚡ ZENO AI ⚡</div>
        <p style="color: #e0f7fa; font-size: 1.1rem; margin-top: 5px;">
            To continue learning and permanently save your English practice history, please <b>Sign In</b> or <b>Create an Account</b> once.
        </p>
        <div class="orb-wrapper"><div class="core-orb"></div></div>
    </div>
    """, unsafe_allow_html=True)

    auth_tab1, auth_tab2 = st.tabs(["🔑 Sign In", "📝 Create Account (Sign Up)"])
    users_db = load_data(USERS_FILE, {})

    with auth_tab1:
        st.subheader("Sign In to Continue")
        login_id = st.text_input("Username", key="login_id")
        login_pwd = st.text_input("Password", type="password", key="login_pwd")
        
        if st.button("🚀 Sign In & Resume Practice", use_container_width=True):
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
                    
                    st.success("Access Granted! Permanently logged in.")
                    st.rerun()
                else:
                    st.error("Invalid Password!")
            else:
                st.error("User not found. Please Sign Up.")

    with auth_tab2:
        st.subheader("New User Registration")
        st.info("Password rules: Minimum 8 characters, at least 1 number, and 1 special symbol (@, #, $, %).")
        new_id = st.text_input("Choose Username", key="reg_id")
        new_pwd = st.text_input("Create Password", type="password", key="reg_pwd")
        new_pwd_confirm = st.text_input("Confirm Password", type="password", key="reg_pwd_confirm")

        if st.button("✨ Create Account & Continue", use_container_width=True):
            is_valid, msg = is_strong_password(new_pwd)
            if not new_id or not new_pwd:
                st.warning("Please fill all details.")
            elif not is_valid:
                st.error(msg)
            elif new_pwd != new_pwd_confirm:
                st.error("Passwords do not match!")
            elif new_id in users_db:
                st.error("Username already registered. Please Sign In.")
            else:
                users_db[new_id] = {"password": new_pwd}
                save_data(USERS_FILE, users_db)
                st.session_state.logged_in_user = new_id
                st.query_params["user"] = new_id
                st.session_state.spoken_daily_topic = False

                all_histories = load_data(HISTORY_FILE, {})
                all_histories[new_id] = st.session_state.guest_messages
                save_data(HISTORY_FILE, all_histories)

                st.success("Account created successfully! Resuming...")
                st.rerun()

# ----------------- MAIN TUTOR DASHBOARD -----------------
else:
    all_histories = load_data(HISTORY_FILE, {})
    today_topic = get_today_topic()

    if not is_logged_in:
        current_user = "Guest (Free Trial)"
        user_messages = st.session_state.guest_messages
        remaining_sec = max(0, 60 - elapsed_seconds)
    else:
        current_user = st.session_state.logged_in_user
        if current_user not in all_histories:
            all_histories[current_user] = [
                {"role": "assistant", "content": f"Hello {current_user}! Today's English lesson is ready. Let's practice speaking together!"}
            ]
        user_messages = all_histories[current_user]

    # TOP HEADER WITH "➕ NEW CHAT" & LOGOUT
    head_col1, head_col2, head_col3 = st.columns([2.5, 0.8, 0.7])
    with head_col1:
        st.markdown('<div class="zeno-brand">⚡ ZENO AI | ENGLISH COACH ⚡</div>', unsafe_allow_html=True)
        if not is_logged_in:
            st.markdown(f"""
            <div class="storage-badge" style="border-color: #ff007f; color: #ff80bf;">
                ⏳ <b>Free Practice Time Left:</b> <code>{remaining_sec} seconds</code>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="storage-badge">
                💾 <b>History:</b> <code>{HISTORY_FILE}</code> | <b>User:</b> <code>{current_user}</code> | <b>Saved:</b> {len(user_messages)} msgs
            </div>
            """, unsafe_allow_html=True)

    with head_col2:
        if st.button("➕ New Chat", use_container_width=True):
            new_welcome = f"Hello {current_user}! Starting a fresh chat. What would you like to practice now?"
            if not is_logged_in:
                st.session_state.guest_messages = [{"role": "assistant", "content": new_welcome}]
            else:
                all_histories[current_user] = [{"role": "assistant", "content": new_welcome}]
                save_data(HISTORY_FILE, all_histories)
            st.rerun()

    with head_col3:
        if is_logged_in:
            if st.button("🚪 Sign Out", use_container_width=True):
                st.session_state.logged_in_user = None
                st.query_params.clear()
                st.session_state.guest_start_time = time.time()
                st.session_state.spoken_daily_topic = False
                st.rerun()

    # IN-APP DAILY NOTIFICATION BANNER
    st.markdown(f"""
    <div class="daily-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span class="daily-title">🔔 DAILY NOTIFICATION: {today_topic['title']}</span>
            <span style="color: #00ffcc; font-size: 0.85rem; font-weight: bold; text-shadow: 0 0 10px #00ffcc;">⭐ TODAY'S TOPIC</span>
        </div>
        <p style="color: #e0f7fa; font-size: 1.08rem; margin: 8px 0 4px 0;">
            {today_topic['lesson']}
        </p>
        <div style="color: #80deea; font-size: 0.98rem;">
            <b>💬 Practice Saying This:</b> <i>"{today_topic['phrase']}"</i>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # AUTOMATIC VOICE EXPLANATION ON LOAD
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

    # UPLOADS & INSTALL GUIDE SECTION
    with st.expander("📲 HOW TO INSTALL APP ON MOBILE & MEDIA UPLOAD", expanded=False):
        c_up1, c_up2 = st.columns([1.5, 1.5])
        with c_up1:
            st.markdown("""
            ### 📱 Install Zeno AI as Mobile App:
            1. Website na **Chrome Browser** nalli open maadi.
            2. Top right corner nalli **3 dots menu (⋮)** click maadi.
            3. **"Install app"** athava **"Add to Home screen"** select maadi.
            4. Done! Home screen inda real app thara open aaguththe.
            """)
            st.markdown("---")
            up_file = st.file_uploader(
                "Choose Photo, Audio or Document",
                type=["png", "jpg", "jpeg", "mp3", "wav", "pdf", "txt"],
                key="direct_file_uploader"
            )
            file_caption = st.text_input("Add a message with this file:", placeholder="e.g. Please check my grammar on this note", key="file_msg")
            
            if up_file:
                st.info(f"Selected: **{up_file.name}** ({up_file.type})")
                if up_file.type.startswith("image/"):
                    st.image(up_file, width=220)
                elif up_file.type.startswith("audio/"):
                    st.audio(up_file)
                
                if st.button("📤 Send Uploaded File to Zeno", use_container_width=True):
                    user_text = file_caption if file_caption.strip() else f"I have uploaded {up_file.name}. Please teach and correct me."
                    user_messages.append({"role": "user", "content": f"📎 [Attached: {up_file.name}] {user_text}"})
                    
                    prompt_for_ai = f"The user uploaded file '{up_file.name}'. Message: '{user_text}'. Respond as an English coach teaching them."
                    bot_reply = call_groq_api_robust(prompt_for_ai)
                    bot_reply = bot_reply.replace("*", "").replace("#", "").replace('"', '').replace("'", "").strip()
                    
                    user_messages.append({"role": "assistant", "content": bot_reply})
                    if is_logged_in:
                        all_histories[current_user] = user_messages
                        save_data(HISTORY_FILE, all_histories)
                    st.rerun()

        with c_up2:
            st.write("### 🗄️ Storage Details")
            st.markdown(f"- **Active User:** `{current_user}`")
            st.markdown(f"- **Saved Records:** `{len(user_messages)} msgs`")
            
            chat_json_str = json.dumps(user_messages, indent=2)
            st.download_button("📥 Export My Chat (.JSON)", data=chat_json_str, file_name=f"{current_user}_chat_history.json", mime="application/json", use_container_width=True)

            if st.button("🗑️ Reset Chat History", use_container_width=True):
                if not is_logged_in:
                    st.session_state.guest_messages = [
                        {"role": "assistant", "content": "Memory refreshed. Ready to practice speaking!"}
                    ]
                else:
                    all_histories[current_user] = [
                        {"role": "assistant", "content": "Memory refreshed. Ready to practice speaking!"}
                    ]
                    save_data(HISTORY_FILE, all_histories)
                st.rerun()

    # DISPLAY CHAT HISTORY
    for msg in user_messages:
        avatar = "🎓" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            if msg.get("image_url"):
                st.image(msg["image_url"], caption="Generated Illustration")
            st.markdown(msg["content"])

    # DOCKED MIC BUTTON (TOUCH TO SPEAK)
    mic_html = """
    <div style="display: flex; align-items: center; justify-content: center; gap: 14px; margin: 10px 0 5px 0;">
        <button id="micBtn" style="
            background: linear-gradient(45deg, #00f2fe, #ff007f);
            border: none;
            color: #ffffff;
            padding: 10px 24px;
            border-radius: 24px;
            font-weight: 800;
            font-size: 14px;
            cursor: pointer;
            box-shadow: 0 0 20px rgba(0, 242, 254, 0.55);
            letter-spacing: 1px;
            outline: none;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        ">🎙️ TOUCH TO SPEAK</button>
        <span id="status" style="color: #00ffcc; font-size: 13px; font-weight: 700;">Tap to speak or auto-listen</span>
    </div>

    <script>
        const micBtn = document.getElementById('micBtn');
        const status = document.getElementById('status');
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        let isHandsFreeActive = false;
        let recognition = null;

        if (!SpeechRecognition) {
            status.innerText = "Speech requires Google Chrome browser.";
        } else {
            recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-US';

            function startListeningNow() {
                try {
                    if (window.parent.speechSynthesis && window.parent.speechSynthesis.speaking) {
                        return;
                    }
                    recognition.start();
                    status.innerText = "🔴 Listening... Speak clearly now";
                    micBtn.style.background = "#ff0055";
                    micBtn.innerText = "🛑 STOP LISTENING";
                } catch(e) {}
            }

            micBtn.onclick = async () => {
                if (isHandsFreeActive) {
                    isHandsFreeActive = false;
                    recognition.stop();
                    sessionStorage.setItem('zeno_handsfree', 'false');
                    status.innerText = "Paused. Tap to speak.";
                    micBtn.style.background = "linear-gradient(45deg, #00f2fe, #ff007f)";
                    micBtn.innerText = "🎙️ TOUCH TO SPEAK";
                    return;
                }

                try {
                    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                        await navigator.mediaDevices.getUserMedia({ audio: true });
                    }
                    isHandsFreeActive = true;
                    sessionStorage.setItem('zeno_handsfree', 'true');
                    startListeningNow();
                } catch (e) {
                    status.innerText = "Mic blocked. Allow permissions in Chrome.";
                }
            };

            recognition.onresult = (event) => {
                const text = event.results[0][0].transcript;
                status.innerText = "Heard: " + text;

                const parentDoc = window.parent.document;
                const textarea = parentDoc.querySelector('textarea[aria-label="Ask Zeno or type \'image: car\' to generate..."]') ||
                                 parentDoc.querySelector('textarea[data-testid="stChatInputTextArea"]');

                if (textarea) {
                    const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
                    nativeSetter.call(textarea, text);
                    textarea.dispatchEvent(new Event('input', { bubbles: true }));

                    setTimeout(() => {
                        const sendBtn = parentDoc.querySelector('button[data-testid="stChatInputSubmitButton"]') ||
                                        parentDoc.querySelector('button[kind="secondaryFormSubmit"]');
                        if (sendBtn) {
                            sendBtn.click();
                        } else {
                            const enterEvent = new KeyboardEvent('keydown', {
                                bubbles: true,
                                cancelable: true,
                                key: 'Enter',
                                code: 'Enter',
                                keyCode: 13
                            });
                            textarea.dispatchEvent(enterEvent);
                        }
                    }, 400);
                }
            };

            recognition.onerror = (e) => {
                if (isHandsFreeActive && e.error !== 'not-allowed') {
                    setTimeout(() => {
                        if (isHandsFreeActive) startListeningNow();
                    }, 1000);
                } else {
                    micBtn.style.background = "linear-gradient(45deg, #00f2fe, #ff007f)";
                    micBtn.innerText = "🎙️ TOUCH TO SPEAK";
                }
            };

            recognition.onend = () => {};

            window.parent.addEventListener('zeno_speech_ended', () => {
                if (sessionStorage.getItem('zeno_handsfree') === 'true') {
                    isHandsFreeActive = true;
                    setTimeout(startListeningNow, 500);
                }
            });

            if (sessionStorage.getItem('zeno_handsfree') === 'true') {
                isHandsFreeActive = true;
                micBtn.style.background = "#ff0055";
                micBtn.innerText = "🛑 STOP LISTENING";
                status.innerText = "Zeno talking... mic will auto open.";
            }
        }
    </script>
    """
    st.components.v1.html(mic_html, height=48)

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
            
            # 1. INSTANT AI IMAGE GENERATION
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
                        const ut = new SpeechSynthesisUtterance("Here is the visual generated for you.");
                        ut.onend = () => {
                            window.dispatchEvent(new CustomEvent('zeno_speech_ended'));
                        };
                        window.speechSynthesis.speak(ut);
                    }
                </script>
                """
                st.components.v1.html(tts_script, height=0)

            # 2. CORE ROBUST ENGLISH TEACHING ENGINE
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
                            
                            utterance.onend = () => {{
                                window.dispatchEvent(new CustomEvent('zeno_speech_ended'));
                            }};
                            
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
