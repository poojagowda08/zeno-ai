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
    page_title="ZENO AI | Smart Super Assistant",
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

    .app-box {
        background: rgba(10, 25, 55, 0.85);
        border: 1.5px solid #00ffcc;
        border-radius: 16px;
        padding: 14px 18px;
        margin-bottom: 12px;
        box-shadow: 0 0 20px rgba(0, 255, 204, 0.2);
    }

    .visible-box {
        background: rgba(15, 23, 58, 0.85);
        border: 1px solid #00f2fe;
        border-radius: 14px;
        padding: 14px;
        margin-bottom: 12px;
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

    .app-btn {
        display: inline-block;
        background: linear-gradient(135deg, rgba(0, 242, 254, 0.2), rgba(255, 0, 127, 0.2));
        border: 1px solid #00f2fe;
        color: #ffffff !important;
        text-decoration: none;
        padding: 8px 14px;
        border-radius: 12px;
        font-size: 0.9rem;
        font-weight: 700;
        margin: 4px;
        box-shadow: 0 0 10px rgba(0, 242, 254, 0.3);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .app-btn:hover {
        transform: scale(1.05);
        box-shadow: 0 0 20px #00ffcc;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SESSION STATE & PERSISTENT LOGIN -----------------
query_user = st.query_params.get("user", "")

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = query_user if query_user else None

if "guest_start_time" not in st.session_state:
    st.session_state.guest_start_time = time.time()

if "guest_messages" not in st.session_state:
    st.session_state.guest_messages = [
        {"role": "assistant", "content": "Namaskara! Naanu Zeno AI. En prashne kelidru accurate aagi uthira kodtheeni. Photo, video athava files upload maadi explain madalu heli, athava apps open maadi!"}
    ]

# ----------------- ALL-PURPOSE ACCURATE GROQ CALLER -----------------
def call_groq_api_robust(prompt):
    raw_key = st.secrets.get("GROQ_API_KEY", "") or os.environ.get("GROQ_API_KEY", "")
    if not raw_key:
        return "GROQ_API_KEY Missing! Streamlit Secrets nalli GROQ_API_KEY add maadi."

    keys_list = [k.strip().replace('"', '').replace("'", "") for k in raw_key.split(",") if k.strip()]

    system_instruction = (
        "You are Zeno AI, an ultra-smart, highly accurate, general-purpose AI assistant. "
        "You help users with everything: answering questions with high factual accuracy, solving code, explaining uploaded photos/videos/documents, summarizing data, and everyday tasks. "
        "Rules for responding:\n"
        "1. Give direct, highly accurate, and helpful answers.\n"
        "2. If an image, video, audio, or document is provided or described, thoroughly explain its content, key details, and implications.\n"
        "3. Understand Kannada, English, and Tanglish naturally. Respond clearly based on user preferences.\n"
        "4. If the user asks for code, provide clean, executable code with brief explanation.\n"
        "5. Keep responses structured, neat, and engaging."
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

# ----------------- SIGN IN / SIGN UP (GUEST AFTER 1 MIN) -----------------
if not is_logged_in and time_limit_reached:
    st.markdown("""
    <div class="enter-card">
        <div style="color: #ff007f; font-weight: 800; letter-spacing: 2px;">⚠️ 1-MINUTE TRIAL COMPLETED</div>
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

                all_histories = load_data(HISTORY_FILE, {})
                all_histories[new_id] = st.session_state.guest_messages
                save_data(HISTORY_FILE, all_histories)
                st.rerun()

# ----------------- MAIN SMART DASHBOARD -----------------
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
                {"role": "assistant", "content": f"Hello {current_user}! En prashne idru keli, accurate uthira kodo engine ready ide."}
            ]
        user_messages = all_histories[current_user]

    # ================= LEFT SIDEBAR (SAVED CHAT HISTORY) =================
    with st.sidebar:
        st.markdown('<div class="zeno-brand" style="font-size: 1.5rem;">📁 CHAT HISTORY</div>', unsafe_allow_html=True)
        st.caption(f"User: **{current_user}**")

        if st.button("➕ New Chat Session", use_container_width=True):
            new_welcome = f"Hello {current_user}! Fresh conversation started. En kelbeku iga?"
            if not is_logged_in:
                st.session_state.guest_messages = [{"role": "assistant", "content": new_welcome}]
            else:
                all_histories[current_user] = [{"role": "assistant", "content": new_welcome}]
                save_data(HISTORY_FILE, all_histories)
            st.rerun()

        st.markdown("---")
        st.markdown("### 💬 Saved Conversations")
        
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

    # ================= MAIN CONTENT HEADER =================
    head_col1, head_col2 = st.columns([3, 1])
    with head_col1:
        st.markdown('<div class="zeno-brand">⚡ ZENO AI | SMART ASSISTANT ⚡</div>', unsafe_allow_html=True)
        if not is_logged_in:
            st.markdown(f'<div class="storage-badge" style="border-color: #ff007f; color: #ff80bf;">⏳ Free Trial: <b>{remaining_sec}s left</b></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="storage-badge">✅ Permanent Login: <b>{current_user}</b> | Left Sidebar History Active ({len(user_messages)} msgs)</div>', unsafe_allow_html=True)

    # ================= 1. DIRECT APP LAUNCHERS (ONE-TAP SHORTCUTS) =================
    st.markdown("""
    <div class="app-box">
        <div style="color: #00ffcc; font-family: 'Orbitron'; font-size: 1.05rem; font-weight: bold; margin-bottom: 8px;">
            🚀 Quick App Launcher Shortcuts
        </div>
        <div style="display: flex; flex-wrap: wrap; gap: 8px;">
            <a class="app-btn" href="https://www.google.com" target="_blank">🔍 Google Search</a>
            <a class="app-btn" href="https://www.youtube.com" target="_blank">📺 YouTube</a>
            <a class="app-btn" href="https://web.whatsapp.com" target="_blank">💬 WhatsApp</a>
            <a class="app-btn" href="https://mail.google.com" target="_blank">✉️ Gmail</a>
            <a class="app-btn" href="https://maps.google.com" target="_blank">🗺️ Google Maps</a>
            <a class="app-btn" href="https://github.com" target="_blank">🐙 GitHub</a>
            <a class="app-btn" href="https://www.instagram.com" target="_blank">📸 Instagram</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ================= 2. DIRECT MULTI-MEDIA EXPLANATION PANEL =================
    st.markdown('<div class="visible-box"><b>🖼️ Upload Photos, Videos, Audio, or Documents for AI Explanation</b></div>', unsafe_allow_html=True)
    up_c1, up_c2 = st.columns([2, 1])
    with up_c1:
        up_file = st.file_uploader(
            "Upload file (Images, Videos, Audios, PDFs, Docs)",
            type=["png", "jpg", "jpeg", "mp4", "mov", "mkv", "mp3", "wav", "pdf", "txt"],
            key="media_uploader",
            label_visibility="collapsed"
        )
        file_msg = st.text_input("Ask anything about this file:", placeholder="e.g. Explain this image/video details or solve questions in it", key="file_caption")
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
                user_question = file_msg if file_msg.strip() else f"Explain this uploaded file ({up_file.name}) in detail with accurate points."
                user_messages.append({"role": "user", "content": f"📎 [Uploaded: {up_file.name}] {user_question}"})

                ai_prompt = (
                    f"The user has uploaded a file named '{up_file.name}' of type '{up_file.type}'. "
                    f"User request: '{user_question}'. "
                    "Provide a thorough, highly accurate, and clear explanation of the content, key takeaways, and answer any questions asked."
                )
                bot_reply = call_groq_api_robust(ai_prompt)
                user_messages.append({"role": "assistant", "content": bot_reply})
                if is_logged_in:
                    all_histories[current_user] = user_messages
                    save_data(HISTORY_FILE, all_histories)
                st.rerun()

    # ================= 3. DISPLAY CHAT HISTORY =================
    for msg in user_messages:
        avatar = "⚡" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            if msg.get("image_url"):
                st.image(msg["image_url"], caption="Generated Illustration")
            st.markdown(msg["content"])

    # ================= 4. CLASSIC TOUCH TO SPEAK MIC BUTTON =================
    mic_html = """
    <div style="display: flex; align-items: center; justify-content: center; gap: 14px; margin: 10px 0 6px 0;">
        <button id="micBtn" type="button" style="
            background: linear-gradient(45deg, #00f2fe, #ff007f);
            border: 2px solid #ffffff;
            color: #ffffff;
            padding: 10px 26px;
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
            status.innerText = "Please open this site in Google Chrome.";
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

    # ================= 5. CHAT INPUT (ANSWERS & IMAGE GEN) =================
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

            # Accurate Universal AI Answer Engine
            else:
                with st.spinner("Zeno is thinking..."):
                    raw_reply = call_groq_api_robust(user_prompt)
                st.markdown(raw_reply)

                user_messages.append({"role": "assistant", "content": raw_reply})
                if is_logged_in:
                    all_histories[current_user] = user_messages
                    save_data(HISTORY_FILE, all_histories)

                # Optional Clean Voice Playback for short replies
                if len(raw_reply) < 300:
                    clean_spoken = raw_reply.replace("*", "").replace("#", "").replace('"', '').replace("'", "")
                    tts_js = f"""
                    <script>
                        if ('speechSynthesis' in window) {{
                            window.speechSynthesis.cancel();
                            const utter = new SpeechSynthesisUtterance("{clean_spoken}");
                            window.speechSynthesis.speak(utter);
                        }}
                    </script>
                    """
                    st.components.v1.html(tts_js, height=0)
