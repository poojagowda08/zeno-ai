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
        return False, "Password must be at least 8 characters long."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number (0-9)."
    if not re.search(r"[@#$%^&*!_\-+=]", password):
        return False, "Password must contain at least one special symbol (@, #, $, %, &, *, !)."
    return True, "Strong Password!"

# ----------------- ULTRA-MODERN NEAT CYBERPUNK STYLING -----------------
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
        padding: 16px 20px;
        margin-bottom: 14px;
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

    .speaker-btn-ui {
        background: linear-gradient(135deg, #00ffcc 0%, #0072ff 100%);
        border: none;
        color: #040817;
        font-weight: 800;
        padding: 7px 16px;
        border-radius: 16px;
        cursor: pointer;
        font-size: 13px;
        box-shadow: 0 0 12px rgba(0, 255, 204, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SESSION STATE & 100% PERSISTENT LOGIN -----------------
query_user = st.query_params.get("user", "")

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = query_user if query_user else None

if "guest_start_time" not in st.session_state:
    st.session_state.guest_start_time = time.time()

if "guest_messages" not in st.session_state:
    st.session_state.guest_messages = [
        {"role": "assistant", "content": "Hello! I am Zeno AI. Ask me anything, attach files/images, take camera snaps, or use the app shortcuts above!"}
    ]

# ----------------- DYNAMIC MODEL GROQ CALLER -----------------
raw_key = st.secrets.get("GROQ_API_KEY", "") or os.environ.get("GROQ_API_KEY", "")
API_KEYS = [k.strip().replace('"', '').replace("'", "") for k in raw_key.split(",") if k.strip()]

def call_groq_api_robust(prompt):
    if not API_KEYS:
        return "GROQ_API_KEY Missing! Please add GROQ_API_KEY to Streamlit Secrets."

    system_instruction = (
        "You are Zeno AI, an ultra-smart, helpful AI assistant. "
        "Strict Language Rules:\n"
        "1. If the user asks in Kannada (Kannada script or Tanglish/Kannada written in English alphabet), respond strictly in clear Kannada.\n"
        "2. If the user asks in English or any other language, respond strictly in English. Never reply in Kannada unless asked in Kannada.\n"
        "3. Provide direct, accurate, and concise answers.\n"
        "4. If images, camera snaps, or documents are uploaded, explain their details clearly."
    )

    last_error = ""

    for api_token in API_KEYS:
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0"
        }

        # Dynamic model fetch to avoid model_not_found errors
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
            available_models = ["llama-3.3-70b-versatile", "llama3-8b-8192", "gemma2-9b-it", "mixtral-8x7b-32768"]

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
            Please <b>Sign In</b> or <b>Create an Account</b> once. After this, your chat is permanently saved and login is never asked again!
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
                    st.error("Invalid password!")
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
                {"role": "assistant", "content": f"Hello {current_user}! Ask me anything. Upload files, capture camera snaps, or type below."}
            ]
        user_messages = all_histories[current_user]

    # ================= LEFT SIDEBAR =================
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
            st.markdown(f'<div class="storage-badge">✅ Connected: <b>{current_user}</b> | Persistent Account Active ({len(user_messages)} msgs)</div>', unsafe_allow_html=True)

    # ================= QUICK APP LAUNCHERS =================
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

    # ================= CHAT DISPLAY & SPEAKER =================
    for idx, msg in enumerate(user_messages):
        avatar = "⚡" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            if msg.get("image_url"):
                st.image(msg["image_url"], caption="Generated Illustration")
            st.markdown(msg["content"])

            if msg["role"] == "assistant" and len(msg["content"].strip()) > 0:
                clean_text = re.sub(r'[*#_`]', '', msg["content"][:300]).replace('"', '').replace("'", "").replace('\n', ' ')
                encoded_text = urllib.parse.quote(clean_text)

                tts_component = f"""
                <div style="margin-top: 6px; display: flex; gap: 8px;">
                    <button style="background: linear-gradient(135deg, #00ffcc, #0072ff); border: none; color: #040817; font-weight: 800; padding: 6px 14px; border-radius: 14px; cursor: pointer;" onclick="speakNow()">🔊 Read Aloud</button>
                    <button style="background: rgba(255, 0, 127, 0.4); border: 1px solid #ff007f; color: #fff; font-weight: 800; padding: 6px 14px; border-radius: 14px; cursor: pointer;" onclick="stopVoice()">⏹️ Stop</button>
                </div>
                <script>
                    function speakNow() {{
                        if ('speechSynthesis' in window) {{
                            window.speechSynthesis.cancel();
                            const raw = decodeURIComponent("{encoded_text}");
                            const utter = new SpeechSynthesisUtterance(raw);
                            utter.rate = 1.0;
                            utter.pitch = 1.0;
                            window.speechSynthesis.speak(utter);
                        }}
                    }}
                    function stopVoice() {{
                        if ('speechSynthesis' in window) {{
                            window.speechSynthesis.cancel();
                        }}
                    }}
                </script>
                """
                st.components.v1.html(tts_component, height=45)

    # ================= BOTTOM SEND AREA: ATTACHMENTS + TOGGLE CAMERA + CHAT =================
    st.markdown('<div class="glass-card" style="border-color: #00f2fe; margin-top: 15px;">', unsafe_allow_html=True)

    col_file, col_cam_btn = st.columns([2, 1])
    with col_file:
        up_file = st.file_uploader(
            "📁 Attach Photo / Video / PDF / Audio",
            type=["png", "jpg", "jpeg", "mp4", "mov", "mkv", "mp3", "wav", "pdf", "txt"],
            key="bottom_file_uploader",
            label_visibility="collapsed"
        )
    with col_cam_btn:
        with st.popover("📷 Open Camera Snap", use_container_width=True):
            cam_snap = st.camera_input("Capture Photo", key="popup_cam_input")

    if up_file:
        st.info(f"Attached File: **{up_file.name}**")
        if up_file.type.startswith("image/"):
            st.image(up_file, width=120)
    if cam_snap:
        st.info("Photo Captured via Camera!")
        st.image(cam_snap, width=120)

    col_input, col_send = st.columns([4.2, 0.8])
    with col_input:
        user_prompt = st.text_input(
            "Message",
            placeholder="Type your message, image prompt, or ask about attached file/snap...",
            key="bottom_chat_text",
            label_visibility="collapsed"
        )
    with col_send:
        send_btn = st.button("🚀 Send", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ================= SUBMIT & SEND LOGIC =================
    if send_btn:
        has_file = (up_file is not None)
        has_cam = (cam_snap is not None)
        has_text = bool(user_prompt.strip())

        if has_file or has_cam or has_text:
            final_user_msg = user_prompt.strip()

            if has_file:
                prefix = f"📎 [Attached: {up_file.name}] "
                final_user_msg = prefix + (final_user_msg if final_user_msg else f"Please explain this uploaded {up_file.name} in detail.")

            if has_cam:
                prefix = "📷 [Live Camera Snap] "
                final_user_msg = prefix + (final_user_msg if final_user_msg else "Please explain this captured camera photo in detail.")

            user_messages.append({"role": "user", "content": final_user_msg})

            lower_input = final_user_msg.lower().strip()
            if lower_input.startswith("image:") or lower_input.startswith("generate image:"):
                img_desc = final_user_msg.split(":", 1)[1].strip()
                encoded_desc = urllib.parse.quote(img_desc)
                gen_image_url = f"https://image.pollinations.ai/prompt/{encoded_desc}?width=768&height=768&nologo=true"

                reply_txt = f"Generated image for: **{img_desc}**"
                user_messages.append({"role": "assistant", "content": reply_txt, "image_url": gen_image_url})
            else:
                with st.spinner("⚡ Zeno is thinking..."):
                    raw_reply = call_groq_api_robust(final_user_msg)
                user_messages.append({"role": "assistant", "content": raw_reply})

            if is_logged_in:
                all_histories[current_user] = user_messages
                save_data(HISTORY_FILE, all_histories)
            st.rerun()
