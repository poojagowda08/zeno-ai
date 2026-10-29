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
    page_title="ZENO AI",
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
        return False, "Password nalli ondhu special symbol erbeku."
    return True, "Strong Password!"

# ----------------- PERPLEXITY STYLE MINIMAL CLEAN CSS -----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Orbitron:wght@700;900&display=swap');

    .stApp {
        background-color: #0b0f17;
        color: #e2e8f0;
        font-family: 'Inter', sans-serif;
    }

    [data-testid="stSidebar"] {
        background-color: #080c14 !important;
        border-right: 1px solid #1e293b !important;
    }

    .zeno-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 2.2rem;
        font-weight: 900;
        letter-spacing: 1.5px;
        background: linear-gradient(90deg, #00f2fe 0%, #4facfe 50%, #00ffcc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-top: 10px;
        margin-bottom: 4px;
    }

    .zeno-subtitle {
        text-align: center;
        color: #94a3b8;
        font-size: 0.95rem;
        margin-bottom: 25px;
    }

    .perplexity-card {
        background: #111827;
        border: 1px solid #1f293d;
        border-radius: 14px;
        padding: 16px 20px;
        margin-bottom: 14px;
    }

    .quick-link {
        display: inline-block;
        background: #1e293b;
        color: #38bdf8 !important;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
        text-decoration: none;
        margin: 3px;
        border: 1px solid #334155;
        transition: all 0.2s ease;
    }
    .quick-link:hover {
        background: #0284c7;
        color: #ffffff !important;
        border-color: #38bdf8;
    }

    .speaker-btn {
        background: #1e293b;
        color: #38bdf8;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 4px 10px;
        font-size: 12px;
        font-weight: 600;
        cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SESSION STATE & LOGIN -----------------
query_user = st.query_params.get("user", "")

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = query_user if query_user else None

if "guest_start_time" not in st.session_state:
    st.session_state.guest_start_time = time.time()

if "guest_messages" not in st.session_state:
    st.session_state.guest_messages = [
        {"role": "assistant", "content": "Hello! I am Zeno AI. Ask me anything, or upload any file/camera snap from the left sidebar to get instant automatic explanation."}
    ]

# ----------------- GROQ API CALLER -----------------
raw_key = st.secrets.get("GROQ_API_KEY", "") or os.environ.get("GROQ_API_KEY", "")
API_KEYS = [k.strip().replace('"', '').replace("'", "") for k in raw_key.split(",") if k.strip()]

def call_groq_api_robust(prompt):
    if not API_KEYS:
        return "GROQ_API_KEY Missing! Streamlit Secrets nalli GROQ_API_KEY add maadi."

    system_instruction = (
        "You are Zeno AI, a clean, highly accurate, Perplexity-style intelligence engine. "
        "Language Rules:\n"
        "1. If user asks in Kannada (or Tanglish), respond strictly in clear Kannada.\n"
        "2. If user asks in English or any other language, respond strictly in English.\n"
        "3. Provide direct, factual, structured, and comprehensive answers without unnecessary fillers.\n"
        "4. When an image, file, or camera snap is uploaded, immediately describe all visual details, what it is, context, meaning, and key points thoroughly without waiting for extra questions."
    )

    last_error = ""

    for api_token in API_KEYS:
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0"
        }

        available_models = []
        try:
            req_models = urllib.request.Request("https://api.groq.com/openai/v1/models", headers=headers, method="GET")
            with urllib.request.urlopen(req_models, timeout=8) as m_resp:
                m_data = json.loads(m_resp.read().decode("utf-8"))
                for m in m_data.get("data", []):
                    m_id = m.get("id", "")
                    if not any(x in m_id.lower() for x in ["whisper", "guard", "vision", "orpheus"]):
                        available_models.append(m_id)
        except Exception:
            available_models = ["llama-3.3-70b-versatile", "llama3-8b-8192", "gemma2-9b-it"]

        if not available_models:
            available_models = ["llama-3.3-70b-versatile", "llama3-8b-8192"]

        chat_url = "https://api.groq.com/openai/v1/chat/completions"

        for model_name in available_models:
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2
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

# ----------------- TIME & AUTH CHECK -----------------
is_logged_in = st.session_state.logged_in_user is not None

if not is_logged_in:
    elapsed_seconds = int(time.time() - st.session_state.guest_start_time)
    time_limit_reached = (elapsed_seconds >= 60)
else:
    time_limit_reached = False

# ----------------- SIGN IN / SIGN UP (ONE TIME) -----------------
if not is_logged_in and time_limit_reached:
    st.markdown("""
    <div class="perplexity-card" style="max-width: 460px; margin: 40px auto; text-align: center;">
        <div style="color: #38bdf8; font-weight: 700; font-size: 0.9rem; letter-spacing: 1px;">AUTHENTICATION REQUIRED</div>
        <div class="zeno-title" style="font-size: 1.8rem;">⚡ ZENO AI ⚡</div>
        <p style="color: #94a3b8; font-size: 0.9rem;">Sign in once to keep your history persistent permanently.</p>
    </div>
    """, unsafe_allow_html=True)

    auth_tab1, auth_tab2 = st.tabs(["Sign In", "Create Account"])
    users_db = load_data(USERS_FILE, {})

    with auth_tab1:
        login_id = st.text_input("Username", key="login_id")
        login_pwd = st.text_input("Password", type="password", key="login_pwd")
        if st.button("Sign In & Continue", use_container_width=True):
            user_record = users_db.get(login_id)
            if user_record and (user_record.get("password") == login_pwd if isinstance(user_record, dict) else user_record == login_pwd):
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
                st.error("Invalid credentials!")

    with auth_tab2:
        new_id = st.text_input("Choose Username", key="reg_id")
        new_pwd = st.text_input("Create Password", type="password", key="reg_pwd")
        new_pwd_confirm = st.text_input("Confirm Password", type="password", key="reg_pwd_confirm")
        if st.button("Register & Enter", use_container_width=True):
            is_valid, msg = is_strong_password(new_pwd)
            if not new_id or not new_pwd:
                st.warning("Please fill all details.")
            elif not is_valid:
                st.error(msg)
            elif new_pwd != new_pwd_confirm:
                st.error("Passwords do not match!")
            elif new_id in users_db:
                st.error("Username already registered.")
            else:
                users_db[new_id] = {"password": new_pwd}
                save_data(USERS_FILE, users_db)
                st.session_state.logged_in_user = new_id
                st.query_params["user"] = new_id

                all_histories = load_data(HISTORY_FILE, {})
                all_histories[new_id] = st.session_state.guest_messages
                save_data(HISTORY_FILE, all_histories)
                st.rerun()

# ----------------- MAIN PERPLEXITY-STYLE DASHBOARD -----------------
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
                {"role": "assistant", "content": f"Hello {current_user}! Where knowledge begins. Ask anything or upload files from the sidebar for instant explanation."}
            ]
        user_messages = all_histories[current_user]

    # ================= LEFT SIDEBAR (UPLOAD HUB + CHATS) =================
    with st.sidebar:
        st.markdown('<div style="font-family: Orbitron; font-weight: 800; font-size: 1.3rem; color: #38bdf8;">⚡ ZENO AI</div>', unsafe_allow_html=True)
        st.caption(f"Session: **{current_user}**")

        if st.button("➕ New Thread", use_container_width=True):
            new_welcome = f"Hello {current_user}! What would you like to explore today?"
            if not is_logged_in:
                st.session_state.guest_messages = [{"role": "assistant", "content": new_welcome}]
            else:
                all_histories[current_user] = [{"role": "assistant", "content": new_welcome}]
                save_data(HISTORY_FILE, all_histories)
            st.rerun()

        st.markdown("---")
        st.markdown("### 📎 Media & Upload Hub")
        st.caption("Upload maadi athava Snap thegiri, Zeno adanne auto explain maaduththe!")

        side_file = st.file_uploader(
            "Upload Image, Video, PDF, Docs",
            type=["png", "jpg", "jpeg", "mp4", "mov", "mkv", "mp3", "wav", "pdf", "txt"],
            key="sidebar_auto_file",
            label_visibility="collapsed"
        )

        with st.popover("📷 Take Camera Snap", use_container_width=True):
            side_cam = st.camera_input("Snap a photo", key="sidebar_camera_input")

        # AUTO-SEND LOGIC FOR UPLOAD / CAMERA (Zero-click automatic explain)
        if "last_processed_file" not in st.session_state:
            st.session_state.last_processed_file = None

        current_file_token = None
        if side_file:
            current_file_token = f"file_{side_file.name}_{side_file.size}"
        elif side_cam:
            current_file_token = f"cam_{side_cam.size}"

        if current_file_token and current_file_token != st.session_state.last_processed_file:
            st.session_state.last_processed_file = current_file_token
            if side_file:
                auto_msg = f"📎 [Uploaded File: {side_file.name}] Please thoroughly examine and explain this uploaded file in detail. Describe all contents, meaning, and key takeaways."
            else:
                auto_msg = "📷 [Live Camera Snap] Please examine this captured photo and describe everything visible in detail."

            user_messages.append({"role": "user", "content": auto_msg})
            with st.spinner("Zeno is analyzing visual data..."):
                auto_reply = call_groq_api_robust(auto_msg)
            user_messages.append({"role": "assistant", "content": auto_reply})
            if is_logged_in:
                all_histories[current_user] = user_messages
                save_data(HISTORY_FILE, all_histories)
            st.rerun()

        st.markdown("---")
        st.markdown("### 💬 History")
        user_queries = [m["content"] for m in user_messages if m["role"] == "user"]
        if not user_queries:
            st.caption("No history yet.")
        else:
            for q in reversed(user_queries[-10:]):
                clean_q = re.sub(r'\[.*?\]', '', q).strip()
                preview = clean_q[:24] + "..." if len(clean_q) > 24 else clean_q
                st.markdown(f"• {preview}")

        st.markdown("---")
        if is_logged_in:
            if st.button("Sign Out", use_container_width=True):
                st.session_state.logged_in_user = None
                st.query_params.clear()
                st.session_state.guest_start_time = time.time()
                st.rerun()

    # ================= TOP MINIMAL HEADER & APP LAUNCHERS =================
    st.markdown('<div class="zeno-title">⚡ ZENO AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="zeno-subtitle">Where knowledge begins · Clean, accurate & fast intelligence</div>', unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align: center; margin-bottom: 25px;">
        <a class="quick-link" href="https://www.google.com" target="_blank">Google</a>
        <a class="quick-link" href="https://www.youtube.com" target="_blank">YouTube</a>
        <a class="quick-link" href="https://web.whatsapp.com" target="_blank">WhatsApp</a>
        <a class="quick-link" href="https://mail.google.com" target="_blank">Gmail</a>
        <a class="quick-link" href="https://maps.google.com" target="_blank">Maps</a>
        <a class="quick-link" href="https://github.com" target="_blank">GitHub</a>
        <a class="quick-link" href="https://www.instagram.com" target="_blank">Instagram</a>
    </div>
    """, unsafe_allow_html=True)

    # ================= CHAT DISPLAY =================
    for msg in user_messages:
        role_label = "Zeno" if msg["role"] == "assistant" else "You"
        avatar = "⚡" if msg["role"] == "assistant" else "👤"

        with st.chat_message(msg["role"], avatar=avatar):
            if msg.get("image_url"):
                st.image(msg["image_url"], caption="Generated Visual")
            st.markdown(msg["content"])

            if msg["role"] == "assistant" and len(msg["content"].strip()) > 0:
                clean_speech = re.sub(r'[*#_`]', '', msg["content"][:280]).replace('"', '').replace("'", "").replace('\n', ' ')
                encoded_speech = urllib.parse.quote(clean_speech)
                tts_ui = f"""
                <div style="margin-top: 5px;">
                    <button class="speaker-btn" onclick="speakText('{encoded_speech}')">🔊 Read</button>
                    <button class="speaker-btn" style="color: #f43f5e;" onclick="window.speechSynthesis.cancel()">⏹ Stop</button>
                </div>
                <script>
                    function speakText(enc) {{
                        if ('speechSynthesis' in window) {{
                            window.speechSynthesis.cancel();
                            const txt = decodeURIComponent(enc);
                            const u = new SpeechSynthesisUtterance(txt);
                            window.speechSynthesis.speak(u);
                        }}
                    }}
                </script>
                """
                st.components.v1.html(tts_ui, height=35)

    # ================= BOTTOM PERPLEXITY-STYLE SEARCH INPUT =================
    user_prompt = st.chat_input("Ask anything, search topics, or type 'image: sunset' to generate...")

    if user_prompt:
        user_messages.append({"role": "user", "content": user_prompt})
        if is_logged_in:
            all_histories[current_user] = user_messages
            save_data(HISTORY_FILE, all_histories)

        with st.chat_message("user", avatar="👤"):
            st.markdown(user_prompt)

        with st.chat_message("assistant", avatar="⚡"):
            lower_input = user_prompt.lower().strip()

            if lower_input.startswith("image:") or lower_input.startswith("generate image:"):
                img_desc = user_prompt.split(":", 1)[1].strip()
                encoded_desc = urllib.parse.quote(img_desc)
                gen_image_url = f"https://image.pollinations.ai/prompt/{encoded_desc}?width=768&height=768&nologo=true"

                reply_txt = f"Generated visual for: **{img_desc}**"
                st.image(gen_image_url, caption=f"Prompt: {img_desc}")
                st.markdown(reply_txt)

                user_messages.append({"role": "assistant", "content": reply_txt, "image_url": gen_image_url})
                if is_logged_in:
                    all_histories[current_user] = user_messages
                    save_data(HISTORY_FILE, all_histories)
            else:
                with st.spinner("Searching and synthesizing..."):
                    raw_reply = call_groq_api_robust(user_prompt)
                st.markdown(raw_reply)

                user_messages.append({"role": "assistant", "content": raw_reply})
                if is_logged_in:
                    all_histories[current_user] = user_messages
                    save_data(HISTORY_FILE, all_histories)
            st.rerun()
