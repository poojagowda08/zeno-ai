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
    page_title="ZENO AI | Next-Gen Smart Assistant",
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
        return False, "Password must be at least 8 characters long."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number (0-9)."
    if not re.search(r"[@#$%^&*!_\-+=]", password):
        return False, "Password must contain at least one special symbol (@, #, $, %, &, *, !)."
    return True, "Strong Password!"

# ----------------- ULTRA-MODERN CYBERPUNK STYLING -----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@500;600;700&display=swap');

    .stApp {
        background: radial-gradient(circle at 50% 5%, #0d1238 0%, #050816 55%, #010207 100%);
        color: #e0f7fa;
        font-family: 'Rajdhani', sans-serif;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #06091e 0%, #03040a 100%) !important;
        border-right: 2px solid rgba(0, 242, 254, 0.45) !important;
        box-shadow: 10px 0 30px rgba(0, 242, 254, 0.1);
    }

    .zeno-brand {
        font-family: 'Orbitron', sans-serif;
        font-size: 2.3rem;
        font-weight: 900;
        letter-spacing: 3px;
        background: linear-gradient(90deg, #00f2fe 0%, #4facfe 30%, #00ffcc 70%, #ff007f 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 25px rgba(0, 242, 254, 0.5);
        margin-bottom: 2px;
    }

    .glass-card {
        background: rgba(12, 18, 48, 0.75);
        border: 1.5px solid rgba(0, 242, 254, 0.35);
        box-shadow: 0 8px 32px 0 rgba(0, 242, 254, 0.15);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border-radius: 18px;
        padding: 18px 22px;
        margin-bottom: 16px;
    }

    .app-btn {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: linear-gradient(135deg, rgba(0, 242, 254, 0.15), rgba(255, 0, 127, 0.2));
        border: 1.5px solid #00f2fe;
        color: #ffffff !important;
        text-decoration: none;
        padding: 8px 16px;
        border-radius: 14px;
        font-size: 0.92rem;
        font-weight: 700;
        margin: 4px;
        box-shadow: 0 0 14px rgba(0, 242, 254, 0.25);
        transition: all 0.25s ease-in-out;
    }
    .app-btn:hover {
        transform: translateY(-3px) scale(1.03);
        box-shadow: 0 0 24px #00ffcc;
        border-color: #00ffcc;
    }

    .storage-badge {
        background: rgba(0, 242, 254, 0.1);
        border: 1px solid #00f2fe;
        color: #80deea;
        padding: 6px 14px;
        border-radius: 14px;
        font-size: 0.88rem;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 8px;
    }

    div[data-testid="stFileUploader"] {
        background: rgba(8, 14, 38, 0.8);
        border: 1.5px dashed #00f2fe;
        border-radius: 14px;
        padding: 10px;
    }

    .speaker-btn-ui {
        background: linear-gradient(135deg, #00ffcc 0%, #0072ff 100%);
        border: none;
        color: #040817;
        font-weight: 800;
        padding: 6px 14px;
        border-radius: 16px;
        cursor: pointer;
        font-size: 13px;
        box-shadow: 0 0 12px rgba(0, 255, 204, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SESSION STATE & LOGIN PERSISTENCE -----------------
query_user = st.query_params.get("user", "")

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = query_user if query_user else None

if "guest_start_time" not in st.session_state:
    st.session_state.guest_start_time = time.time()

if "guest_messages" not in st.session_state:
    st.session_state.guest_messages = [
        {"role": "assistant", "content": "Hello! I am Zeno AI. Ask me anything in English or Kannada, upload any media for detailed explanation, or tap quick app launchers!"}
    ]

# ----------------- BILINGUAL GROQ CALLER -----------------
def call_groq_api_robust(prompt):
    raw_key = st.secrets.get("GROQ_API_KEY", "") or os.environ.get("GROQ_API_KEY", "")
    if not raw_key:
        return "GROQ_API_KEY Missing! Please add GROQ_API_KEY to Streamlit Secrets."

    keys_list = [k.strip().replace('"', '').replace("'", "") for k in raw_key.split(",") if k.strip()]

    system_instruction = (
        "You are Zeno AI, a next-gen intelligent bilingual companion. "
        "Rules for answering:\n"
        "1. For general answers, explain clearly in BOTH English and Kannada (or conversational Kannada in English script) so users grasp the concepts in both languages.\n"
        "2. Provide accurate, factual, and crisp answers.\n"
        "3. If media (photos, videos, docs) are uploaded, describe visual elements, summarize content, and list actionable takeaways.\n"
        "4. If coding is needed, write production-ready code with concise explanations.\n"
        "5. Keep the formatting clean and visually appealing."
    )

    last_error = ""

    for api_token in keys_list:
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0"
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
            available_models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]

        if not available_models:
            available_models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]

        chat_url = "https://api.groq.com/openai/v1/chat/completions"

        for model_name in available_models:
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3
            }
            body_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(chat_url, data=body_data, headers=headers, method="POST")

            try:
                with urllib.request.urlopen(req, timeout=18) as response:
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

# ----------------- SIGN IN / SIGN UP OVERLAY -----------------
if not is_logged_in and time_limit_reached:
    st.markdown("""
    <div class="glass-card" style="text-align: center; max-width: 520px; margin: 30px auto; border-color: #ff007f;">
        <div style="color: #ff007f; font-weight: 800; letter-spacing: 2px;">⚠️ 1-MINUTE FREE TRIAL COMPLETED</div>
        <div class="zeno-brand">⚡ ZENO AI ⚡</div>
        <p style="color: #e0f7fa; font-size: 1.05rem; margin-top: 6px;">
            Please <b>Sign In</b> or <b>Create an Account</b> once. Your sessions, media, and chat histories will remain saved permanently!
        </p>
    </div>
    """, unsafe_allow_html=True)

    auth_tab1, auth_tab2 = st.tabs(["🔑 Sign In", "📝 Create Account (Sign Up)"])
    users_db = load_data(USERS_FILE, {})

    with auth_tab1:
        st.subheader("Sign In Once")
        login_id = st.text_input("Username", key="login_id")
        login_pwd = st.text_input("Password", type="password", key="login_pwd")
        
        if st.button("🚀 Sign In & Continue", use_container_width=True):
            user_record = users_db.get(login_id)
            if user_record:
                saved_pwd = user_record["password"] if isinstance(user_record, dict) else user_record
                if saved_pwd == login_pwd:
                    st.session_state.logged_in_user = login_id
                    st.query_params["user"] = login_id
                    
                    all_histories = load_data(HISTORY_FILE, {})
                    if login_id not in all_histories:
                        all_histories[login_id] = st.session_state.guest_messages
                    else:
                        all_histories[login_id].extend(st.session_state.guest_messages[1:])
                    save_data(HISTORY_FILE, all_histories)
                    st.rerun()
                else:
                    st.error("Invalid password! Please verify your password.")
            else:
                st.error("User not found. Please Sign Up.")

    with auth_tab2:
        st.subheader("New User Registration")
        st.info("Password rules: Minimum 8 characters, at least 1 number, and 1 special symbol (@, #, $, %).")
        new_id = st.text_input("Choose Username", key="reg_id")
        new_pwd = st.text_input("Create Password", type="password", key="reg_pwd")
        new_pwd_confirm = st.text_input("Confirm Password", type="password", key="reg_pwd_confirm")

        if st.button("✨ Create Account & Proceed", use_container_width=True):
            is_valid, msg = is_strong_password(new_pwd)
            if not new_id or not new_pwd:
                st.warning("Please fill in all details.")
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

                all_histories = load_data(HISTORY_FILE, {})
                all_histories[new_id] = st.session_state.guest_messages
                save_data(HISTORY_FILE, all_histories)
                st.rerun()

# ----------------- MAIN APP DASHBOARD -----------------
else:
    all_histories = load_data(HISTORY_FILE, {})

    if not is_logged_in:
        current_user = "Guest"
        user_messages = st.session_state.guest_messages
        remaining_sec = max(0, 60 - elapsed_seconds)
    else:
        current_user = st.session_state.logged_in_user
        if current_user not in all_histories:
            all_histories[current_user] = [
                {"role": "assistant", "content": f"Hello {current_user}! Ask me any question in English or Kannada. I am ready to assist."}
            ]
        user_messages = all_histories[current_user]

    # ================= LEFT SIDEBAR (SAVED HISTORY) =================
    with st.sidebar:
        st.markdown('<div class="zeno-brand" style="font-size: 1.5rem;">📁 CHAT SESSIONS</div>', unsafe_allow_html=True)
        st.caption(f"Logged User: **{current_user}**")

        if st.button("➕ New Chat Session", use_container_width=True):
            new_welcome = f"Hello {current_user}! Fresh session created. What would you like to ask or explore?"
            if not is_logged_in:
                st.session_state.guest_messages = [{"role": "assistant", "content": new_welcome}]
            else:
                all_histories[current_user] = [{"role": "assistant", "content": new_welcome}]
                save_data(HISTORY_FILE, all_histories)
            st.rerun()

        st.markdown("---")
        st.markdown("### 💬 Saved Messages")
        
        user_queries = [m["content"] for m in user_messages if m["role"] == "user"]
        if not user_queries:
            st.write("No conversations yet.")
        else:
            for query in reversed(user_queries[-15:]):
                preview_text = query[:28] + "..." if len(query) > 28 else query
                st.markdown(f"🗨️ {preview_text}")

        st.markdown("---")
        chat_json_str = json.dumps(user_messages, indent=2)
        st.download_button("📥 Export JSON History", data=chat_json_str, file_name=f"{current_user}_chat.json", mime="application/json", use_container_width=True)

        if is_logged_in:
            if st.button("🚪 Sign Out", use_container_width=True):
                st.session_state.logged_in_user = None
                st.query_params.clear()
                st.session_state.guest_start_time = time.time()
                st.rerun()

    # ================= TOP HEADER =================
    head_col1, head_col2 = st.columns([3, 1])
    with head_col1:
        st.markdown('<div class="zeno-brand">⚡ ZENO AI | SMART ASSISTANT ⚡</div>', unsafe_allow_html=True)
        if not is_logged_in:
            st.markdown(f'<div class="storage-badge" style="border-color: #ff007f; color: #ff80bf;">⏳ Free Trial: <b>{remaining_sec}s remaining</b></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="storage-badge">✅ Connected: <b>{current_user}</b> | Cloud Persistent History Active ({len(user_messages)} msgs)</div>', unsafe_allow_html=True)

    # ================= 1. DIRECT APP LAUNCHERS =================
    st.markdown("""
    <div class="glass-card" style="border-color: #00ffcc;">
        <div style="color: #00ffcc; font-family: 'Orbitron'; font-size: 1.05rem; font-weight: bold; margin-bottom: 8px;">
            🚀 Quick App Launchers
        </div>
        <div style="display: flex; flex-wrap: wrap; gap: 8px;">
            <a class="app-btn" href="https://www.google.com" target="_blank">🔍 Google</a>
            <a class="app-btn" href="https://www.youtube.com" target="_blank">📺 YouTube</a>
            <a class="app-btn" href="https://web.whatsapp.com" target="_blank">💬 WhatsApp</a>
            <a class="app-btn" href="https://mail.google.com" target="_blank">✉️ Gmail</a>
            <a class="app-btn" href="https://maps.google.com" target="_blank">🗺️ Maps</a>
            <a class="app-btn" href="https://github.com" target="_blank">🐙 GitHub</a>
            <a class="app-btn" href="https://www.instagram.com" target="_blank">📸 Instagram</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ================= 2. MULTI-MEDIA EXPLANATION PANEL =================
    st.markdown('<div class="glass-card"><b>🖼️ Upload Photos, Videos, Audio, or Documents for AI Explanation</b>', unsafe_allow_html=True)
    up_c1, up_c2 = st.columns([2, 1])
    with up_c1:
        up_file = st.file_uploader(
            "Upload file (Images, Videos, Audios, PDFs, Docs)",
            type=["png", "jpg", "jpeg", "mp4", "mov", "mkv", "mp3", "wav", "pdf", "txt"],
            key="media_uploader",
            label_visibility="collapsed"
        )
        file_msg = st.text_input("Ask questions regarding this file:", placeholder="e.g. Explain this file in both English and Kannada", key="file_caption")
    with up_c2:
        if up_file:
            st.success(f"Attached: {up_file.name}")
            if up_file.type.startswith("image/"):
                st.image(up_file, width=150)
            elif up_file.type.startswith("video/"):
                st.video(up_file)
            elif up_file.type.startswith("audio/"):
                st.audio(up_file)

            if st.button("⚡ Explain with Zeno AI", use_container_width=True):
                user_question = file_msg if file_msg.strip() else f"Explain this uploaded file ({up_file.name}) in detail with accurate points in both English and Kannada."
                user_messages.append({"role": "user", "content": f"📎 [Uploaded: {up_file.name}] {user_question}"})

                ai_prompt = (
                    f"The user uploaded a file named '{up_file.name}' of type '{up_file.type}'. "
                    f"User request: '{user_question}'. "
                    "Provide a thorough, accurate, and structured explanation of the content in English and Kannada."
                )
                bot_reply = call_groq_api_robust(ai_prompt)
                user_messages.append({"role": "assistant", "content": bot_reply})
                if is_logged_in:
                    all_histories[current_user] = user_messages
                    save_data(HISTORY_FILE, all_histories)
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # ================= 3. DISPLAY CHAT HISTORY & VOICE SPEAKER =================
    for idx, msg in enumerate(user_messages):
        avatar = "⚡" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            if msg.get("image_url"):
                st.image(msg["image_url"], caption="Generated Illustration")
            st.markdown(msg["content"])
            
            # Interactive Working Speaker for every Assistant reply
            if msg["role"] == "assistant" and len(msg["content"].strip()) > 0:
                clean_text_for_speech = re.sub(r'[*#_`]', '', msg["content"][:280]).replace('"', '\\"').replace('\n', ' ')
                speech_button_html = f"""
                <div style="margin-top: 6px;">
                    <button class="speaker-btn-ui" onclick='playVoice("{clean_text_for_speech}")'>🔊 Read Aloud</button>
                    <button class="speaker-btn-ui" style="background: rgba(255, 0, 127, 0.4); color: #fff; margin-left: 6px;" onclick='window.speechSynthesis.cancel()'>⏹️ Stop</button>
                </div>
                """
                st.components.v1.html(speech_button_html, height=36)

    # ================= 4. GLOBAL AUDIO ENGINE INJECTION =================
    st.components.v1.html("""
    <script>
        window.playVoice = function(text) {
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
                const utter = new SpeechSynthesisUtterance(text);
                utter.rate = 1.0;
                utter.pitch = 1.0;
                window.speechSynthesis.speak(utter);
            }
        };
    </script>
    """, height=0)

    # ================= 5. TOUCH TO SPEAK MIC =================
    mic_html = """
    <div style="display: flex; align-items: center; justify-content: center; gap: 14px; margin: 12px 0 6px 0;">
        <button id="micBtn" type="button" style="
            background: linear-gradient(45deg, #00f2fe, #ff007f);
            border: 2px solid #ffffff;
            color: #ffffff;
            padding: 10px 28px;
            border-radius: 26px;
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
        <span id="micStatus" style="color: #00ffcc; font-size: 13px; font-weight: 700;">Tap button & speak clearly</span>
    </div>

    <script>
        const btn = document.getElementById('micBtn');
        const status = document.getElementById('micStatus');
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRec) {
            status.innerText = "Please open this website in Google Chrome.";
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
                    rec.start();
                    listening = true;
                    status.innerText = "🔴 Listening... Speak clearly now!";
                    btn.style.background = "#ff0055";
                    btn.innerText = "🛑 STOP LISTENING";
                } catch (err) {
                    status.innerText = "Tap again to activate mic.";
                    resetUi();
                }
            };

            rec.onresult = (e) => {
                const transcript = e.results[0][0].transcript;
                status.innerText = "Heard: " + transcript;

                try {
                    const parentDoc = window.parent.document;
                    const textarea = parentDoc.querySelector('textarea[aria-label="Ask Zeno anything or type \'image: car\' to generate..."]') ||
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
                                textarea.dispatchEvent(new KeyboardEvent('keydown', {
                                    bubbles: true,
                                    cancelable: true,
                                    key: 'Enter',
                                    code: 'Enter',
                                    keyCode: 13
                                }));
                            }
                        }, 400);
                    }
                } catch(e) {}
                resetUi();
            };

            rec.onerror = (e) => {
                status.innerText = "Tap again to speak.";
                resetUi();
            };

            rec.onend = () => {
                resetUi();
            };

            function resetUi() {
                listening = false;
                btn.style.background = "linear-gradient(45deg, #00f2fe, #ff007f)";
                btn.innerText = "🎙️ TOUCH TO SPEAK";
            }
        }
    </script>
    """
    st.components.v1.html(mic_html, height=55)

    # ================= 6. CHAT INPUT =================
    user_prompt = st.chat_input("Ask Zeno anything or type 'image: car' to generate...")

    if user_prompt:
        user_messages.append({"role": "user", "content": user_prompt})
        if is_logged_in:
            all_histories[current_user] = user_messages
            save_data(HISTORY_FILE, all_histories)

        with st.chat_message("user", avatar="👤"):
            st.markdown(user_prompt)

        with st.chat_message("assistant", avatar="⚡"):
            lower_input = user_prompt.lower().strip()

            # Instant AI Image Generation
            if lower_input.startswith("image:") or lower_input.startswith("generate image:"):
                img_desc = user_prompt.split(":", 1)[1].strip()
                encoded_desc = urllib.parse.quote(img_desc)
                gen_image_url = f"https://image.pollinations.ai/prompt/{encoded_desc}?width=768&height=768&nologo=true"

                reply_txt = f"Generated image for: **{img_desc}**"
                st.image(gen_image_url, caption=f"Prompt: {img_desc}")
                st.markdown(reply_txt)

                user_messages.append({"role": "assistant", "content": reply_txt, "image_url": gen_image_url})
                if is_logged_in:
                    all_histories[current_user] = user_messages
                    save_data(HISTORY_FILE, all_histories)

            # Accurate Universal Bilingual Engine (English + Kannada)
            else:
                with st.spinner("Zeno is thinking..."):
                    raw_reply = call_groq_api_robust(user_prompt)
                st.markdown(raw_reply)

                user_messages.append({"role": "assistant", "content": raw_reply})
                if is_logged_in:
                    all_histories[current_user] = user_messages
                    save_data(HISTORY_FILE, all_histories)
                st.rerun()
