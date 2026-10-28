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
    page_title="ZENO AI | English Coach & Smart Auth",
    page_icon="🎓",
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
    # Min 8 chars, at least 1 digit, at least 1 special char
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number (0-9)."
    if not re.search(r"[@#$%^&*!_\-+=]", password):
        return False, "Password must contain at least one special symbol (@, #, $, %, &, *, !)."
    return True, "Strong Password!"

# ----------------- ROTATING DAILY TOPICS -----------------
DAILY_TOPICS = [
    {
        "title": "Making Polite Requests",
        "lesson": "Instead of saying 'I want water', say 'Could I please have some water?'. It sounds polite and confident in office or restaurants.",
        "phrase": "Could you please help me with this?"
    },
    {
        "title": "Daily Routine Fluency",
        "lesson": "Don't say 'Today morning I woke up'. The natural English phrase is 'This morning I woke up'.",
        "phrase": "This morning I started my work early."
    },
    {
        "title": "Ordering Food & Coffee",
        "lesson": "Use 'I would like to order...' or 'Can I get a cup of tea, please?' instead of demanding directly.",
        "phrase": "Can I get a hot coffee with less sugar?"
    },
    {
        "title": "Handling Mistakes Gracefully",
        "lesson": "When you make a mistake, simply say: 'My apologies, let me rephrase that.'",
        "phrase": "Excuse me, could you repeat that once?"
    },
    {
        "title": "Expressing Opinions Confidently",
        "lesson": "To share ideas at work, use 'In my opinion' or 'From my perspective' rather than just 'I think'.",
        "phrase": "From my perspective, this solution will save time."
    }
]

def get_today_topic():
    day_idx = date.today().timetuple().tm_yday % len(DAILY_TOPICS)
    return DAILY_TOPICS[day_idx]

# ----------------- CYBERPUNK STYLING -----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800;900&family=Rajdhani:wght@500;600;700&display=swap');

    .stApp {
        background: radial-gradient(circle at 50% 15%, #090e23 0%, #03050c 100%);
        color: #e0f7fa;
        font-family: 'Rajdhani', sans-serif;
    }

    .enter-card {
        background: rgba(10, 16, 38, 0.92);
        border: 2px solid rgba(0, 242, 254, 0.45);
        box-shadow: 0 0 35px rgba(0, 242, 254, 0.25);
        border-radius: 22px;
        padding: 30px 22px;
        text-align: center;
        backdrop-filter: blur(12px);
        margin: 20px auto;
        max-width: 550px;
    }

    .zeno-brand {
        font-family: 'Orbitron', sans-serif;
        font-size: 2.2rem;
        font-weight: 900;
        letter-spacing: 2px;
        background: linear-gradient(90deg, #00f2fe 0%, #4facfe 50%, #b388ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 6px;
    }

    .core-orb {
        width: 55px;
        height: 55px;
        border-radius: 50%;
        background: radial-gradient(circle, #00f2fe 10%, #7f00ff 70%, #03050c 100%);
        box-shadow: 0 0 25px #00f2fe, 0 0 50px rgba(127, 0, 255, 0.6);
        animation: pulseOrb 2.2s infinite alternate ease-in-out;
        margin: 10px auto;
    }

    @keyframes pulseOrb {
        0% { transform: scale(0.95); box-shadow: 0 0 15px #00f2fe; }
        100% { transform: scale(1.08); box-shadow: 0 0 35px #00f2fe, 0 0 70px #7f00ff; }
    }

    .daily-card {
        background: linear-gradient(135deg, rgba(0, 242, 254, 0.15) 0%, rgba(127, 0, 255, 0.2) 100%);
        border: 1px solid #00f2fe;
        border-radius: 16px;
        padding: 14px 18px;
        margin: 10px 0 14px 0;
        box-shadow: 0 0 20px rgba(0, 242, 254, 0.18);
    }

    .daily-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 1rem;
        color: #00f2fe;
        font-weight: bold;
    }

    .storage-badge {
        background: rgba(0, 242, 254, 0.1);
        border: 1px solid #00f2fe;
        color: #80deea;
        padding: 6px 14px;
        border-radius: 12px;
        font-size: 0.85rem;
        margin-bottom: 10px;
        display: inline-block;
    }

    div[data-testid="stFileUploader"] {
        background: rgba(10, 16, 38, 0.65);
        border: 1px dashed #00f2fe;
        border-radius: 12px;
        padding: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SESSION STATE SETUP -----------------
if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

if "guest_start_time" not in st.session_state:
    st.session_state.guest_start_time = time.time()

if "spoken_daily_topic" not in st.session_state:
    st.session_state.spoken_daily_topic = False

if "guest_messages" not in st.session_state:
    st.session_state.guest_messages = [
        {"role": "assistant", "content": "Welcome! I am Zeno, your English coach. Speak or type to practice. You have 1 minute of free interaction!"}
    ]

# ----------------- GROQ API HELPER (ENGLISH COACH) -----------------
groq_key = st.secrets.get("GROQ_API_KEY", "") or os.environ.get("GROQ_API_KEY", "")

def call_groq_api(prompt, api_token):
    clean_token = api_token.strip().replace('"', '').replace("'", "")
    models_url = "https://api.groq.com/openai/v1/models"
    headers = {
        "Authorization": f"Bearer {clean_token}",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        req_models = urllib.request.Request(models_url, headers=headers, method="GET")
        with urllib.request.urlopen(req_models, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            available_models = [
                m["id"] for m in data.get("data", [])
                if not any(x in m["id"] for x in ["whisper", "guard", "orpheus"])
            ]
    except Exception:
        available_models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]

    chat_url = "https://api.groq.com/openai/v1/chat/completions"
    headers["Content-Type"] = "application/json"

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

    for selected_model in available_models:
        payload = {
            "model": selected_model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.5
        }

        body_data = json.dumps(payload).encode("utf-8")
        req_chat = urllib.request.Request(chat_url, data=body_data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req_chat, timeout=20) as chat_resp:
                res = json.loads(chat_resp.read().decode("utf-8"))
                return res["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8")
            if any(k in err_msg for k in ["model_decommissioned", "model_not_found", "model_terms_required"]):
                continue
            return f"Groq Error ({e.code}): {err_msg}"
        except Exception as e:
            return f"Request Error: {str(e)}"

    return "Service busy. Please try again."

# ----------------- 1-MINUTE TIME CALCULATION -----------------
elapsed_seconds = int(time.time() - st.session_state.guest_start_time)
is_guest = st.session_state.logged_in_user is None
time_limit_reached = is_guest and (elapsed_seconds >= 60)

# ----------------- AUTHENTICATION OVERLAY (WHEN 1 MINUTE EXPIRES) -----------------
if time_limit_reached:
    st.markdown("""
    <div class="enter-card">
        <div style="color: #ff5252; font-weight: bold; letter-spacing: 2px;">⚠️ 1-MINUTE FREE TRIAL COMPLETED</div>
        <div class="zeno-brand">⚡ ZENO AI ⚡</div>
        <p style="color: #e0f7fa; font-size: 1.05rem; margin-top: 5px;">
            To continue learning and save your English practice history, please <b>Sign In</b> or <b>Create an Account</b>.
        </p>
        <div class="core-orb"></div>
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
                    st.session_state.spoken_daily_topic = False
                    
                    # Merge guest chat into permanent user chat
                    all_histories = load_data(HISTORY_FILE, {})
                    if login_id not in all_histories:
                        all_histories[login_id] = st.session_state.guest_messages
                    else:
                        all_histories[login_id].extend(st.session_state.guest_messages[1:])
                    save_data(HISTORY_FILE, all_histories)
                    
                    st.success("Access Granted! Welcome back...")
                    st.rerun()
                else:
                    st.error("Invalid Password!")
            else:
                st.error("User not found. Please Sign Up.")

    with auth_tab2:
        st.subheader("New User Registration")
        st.info("Password rules: Minimum 8 characters, at least 1 number, and 1 special symbol (e.g. @, #, $, %).")
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
                st.session_state.spoken_daily_topic = False

                # Save guest chat into new user history
                all_histories = load_data(HISTORY_FILE, {})
                all_histories[new_id] = st.session_state.guest_messages
                save_data(HISTORY_FILE, all_histories)

                st.success("Account created successfully! Resuming...")
                st.rerun()

# ----------------- MAIN TUTOR DASHBOARD (ACTIVE DURING TRIAL & AFTER LOGIN) -----------------
else:
    all_histories = load_data(HISTORY_FILE, {})
    today_topic = get_today_topic()

    if is_guest:
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

    # TOP HEADER
    head_col1, head_col2 = st.columns([3, 1])
    with head_col1:
        st.markdown('<div class="zeno-brand" style="font-size: 1.8rem;">⚡ ZENO AI | ENGLISH COACH ⚡</div>', unsafe_allow_html=True)
        if is_guest:
            st.markdown(f"""
            <div class="storage-badge" style="border-color: #ff9800; color: #ffb74d;">
                ⏳ <b>Free Practice Time Left:</b> <code>{remaining_sec} seconds</code> (Sign In after 1 min)
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="storage-badge">
                💾 <b>History:</b> <code>{HISTORY_FILE}</code> | <b>User:</b> <code>{current_user}</code> | <b>Saved:</b> {len(user_messages)} msgs
            </div>
            """, unsafe_allow_html=True)
    with head_col2:
        if not is_guest:
            if st.button("🚪 Sign Out", use_container_width=True):
                st.session_state.logged_in_user = None
                st.session_state.guest_start_time = time.time()
                st.session_state.spoken_daily_topic = False
                st.rerun()

    # IN-APP DAILY NOTIFICATION BANNER
    st.markdown(f"""
    <div class="daily-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span class="daily-title">🔔 DAILY NOTIFICATION: {today_topic['title']}</span>
            <span style="color: #ffeb3b; font-size: 0.85rem; font-weight: bold;">⭐ TODAY'S TOPIC</span>
        </div>
        <p style="color: #e0f7fa; font-size: 1.05rem; margin: 8px 0 4px 0;">
            {today_topic['lesson']}
        </p>
        <div style="color: #80deea; font-size: 0.95rem;">
            <b>💬 Practice Saying This:</b> <i>"{today_topic['phrase']}"</i>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # AUTOMATIC VOICE EXPLANATION ON LOAD
    if not st.session_state.spoken_daily_topic:
        st.session_state.spoken_daily_topic = True
        greeting_name = "there" if is_guest else current_user
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

    # UPLOADS SECTION
    with st.expander("📂 UPLOAD PHOTOS / AUDIO / FILES & EXPORT", expanded=False):
        c_up1, c_up2 = st.columns([1.5, 1.5])
        with c_up1:
            up_file = st.file_uploader(
                "Choose Photo, Audio or Document",
                type=["png", "jpg", "jpeg", "mp3", "wav", "pdf", "txt"],
                key="direct_file_uploader"
            )
            file_caption = st.text_input("Add a message with this file:", placeholder="e.g. Please check my grammar on this note", key="file_msg")
            
            if up_file:
                st.info(f"Selected: **{up_file.name}** ({up_file.type})")
                if up_file.type.startswith("image/"):
                    st.image(up_file, width=200)
                elif up_file.type.startswith("audio/"):
                    st.audio(up_file)
                
                if st.button("📤 Send Uploaded File to Zeno", use_container_width=True):
                    user_text = file_caption if file_caption.strip() else f"I have uploaded {up_file.name}. Please teach and correct me."
                    user_messages.append({"role": "user", "content": f"📎 [Attached: {up_file.name}] {user_text}"})
                    
                    prompt_for_ai = f"The user uploaded file '{up_file.name}'. Message: '{user_text}'. Respond as an English coach teaching them."
                    bot_reply = call_groq_api(prompt_for_ai, groq_key)
                    bot_reply = bot_reply.replace("*", "").replace("#", "").replace('"', '').replace("'", "").strip()
                    
                    user_messages.append({"role": "assistant", "content": bot_reply})
                    if not is_guest:
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
                if is_guest:
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
    <div style="display: flex; align-items: center; justify-content: center; gap: 12px; margin: 10px 0 5px 0;">
        <button id="micBtn" style="
            background: linear-gradient(45deg, #00f2fe, #4facfe);
            border: none;
            color: #04091a;
            padding: 10px 24px;
            border-radius: 22px;
            font-weight: 800;
            font-size: 14px;
            cursor: pointer;
            box-shadow: 0 0 16px rgba(0, 242, 254, 0.45);
            letter-spacing: 1px;
            outline: none;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        ">🎙️ TOUCH TO SPEAK</button>
        <span id="status" style="color: #80deea; font-size: 12px; font-weight: 600;">Tap to speak or auto-listen</span>
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
                    micBtn.style.background = "#ff1744";
                    micBtn.innerText = "🛑 STOP LISTENING";
                } catch(e) {}
            }

            micBtn.onclick = async () => {
                if (isHandsFreeActive) {
                    isHandsFreeActive = false;
                    recognition.stop();
                    sessionStorage.setItem('zeno_handsfree', 'false');
                    status.innerText = "Paused. Tap to speak.";
                    micBtn.style.background = "linear-gradient(45deg, #00f2fe, #4facfe)";
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
                    micBtn.style.background = "linear-gradient(45deg, #00f2fe, #4facfe)";
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
                micBtn.style.background = "#ff1744";
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
        if not is_guest:
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
                if not is_guest:
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

            # 2. CORE ENGLISH TEACHING & COACHING ENGINE
            else:
                if not groq_key:
                    st.error("GROQ_API_KEY Missing! Streamlit Secrets nalli GROQ_API_KEY add maadi.")
                else:
                    raw_reply = call_groq_api(user_prompt, groq_key)
                    clean_reply = raw_reply.replace("*", "").replace("#", "").replace('"', '').replace("'", "").strip()
                    st.markdown(clean_reply)

                    user_messages.append({"role": "assistant", "content": clean_reply})
                    if not is_guest:
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
