import streamlit as st
import os
import json
import time
import re
import urllib.request
import urllib.parse
import urllib.error
from datetime import date
from pypdf import PdfReader

# ----------------- PAGE CONFIG -----------------
st.set_page_config(
    page_title="ZENO AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ----------------- PERSISTENCE -----------------
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

def is_strong_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number (0-9)."
    if not re.search(r"[@#$%^&*!_\-+=]", password):
        return False, "Password must contain at least one special symbol."
    return True, "Strong Password!"

# ----------------- CLEAN MODERN 3D STYLING -----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800;900&family=Inter:wght@400;500;600;700&display=swap');

    .stApp {
        background: radial-gradient(circle at 50% 0%, #0d1238 0%, #060919 60%, #020308 100%);
        color: #e2e8f0;
        font-family: 'Inter', sans-serif;
    }

    .hero-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 3rem;
        font-weight: 900;
        letter-spacing: 3px;
        background: linear-gradient(90deg, #00f2fe 0%, #00ffcc 50%, #ff007f 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 35px rgba(0, 242, 254, 0.5);
        margin: 5px 0;
    }

    .hero-subtitle {
        color: #94a3b8;
        font-size: 1.1rem;
        font-weight: 500;
        letter-spacing: 1px;
        margin-bottom: 25px;
    }

    .main-box-3d {
        background: linear-gradient(145deg, rgba(16, 24, 60, 0.9), rgba(7, 12, 35, 0.95));
        border: 1.5px solid rgba(0, 242, 254, 0.4);
        border-radius: 24px;
        padding: 30px 28px;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.7), 0 0 25px rgba(0, 242, 254, 0.2);
        max-width: 850px;
        margin: 20px auto;
        text-align: left;
    }

    .feature-item {
        display: flex;
        align-items: flex-start;
        gap: 14px;
        margin-bottom: 16px;
    }

    .feature-icon-badge {
        background: rgba(0, 242, 254, 0.15);
        border: 1px solid #00f2fe;
        color: #00ffcc;
        border-radius: 12px;
        padding: 8px 12px;
        font-size: 1.2rem;
        box-shadow: 0 0 12px rgba(0, 242, 254, 0.3);
    }

    /* 3D TACTILE SEND BUTTON */
    div[data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(180deg, #00f2fe 0%, #0072ff 100%) !important;
        color: #03081a !important;
        font-family: 'Orbitron', sans-serif !important;
        font-weight: 900 !important;
        font-size: 1rem !important;
        border: 1px solid #00f2fe !important;
        border-radius: 14px !important;
        padding: 10px 22px !important;
        box-shadow: 0 6px 0 #003a80, 0 12px 20px rgba(0, 242, 254, 0.4) !important;
        transform: translateY(0) !important;
        transition: all 0.1s ease-in-out !important;
    }
    div[data-testid="stFormSubmitButton"] > button:hover {
        background: linear-gradient(180deg, #00ffcc 0%, #00f2fe 100%) !important;
        box-shadow: 0 7px 0 #003a80, 0 14px 24px rgba(0, 255, 204, 0.5) !important;
        transform: translateY(-2px) !important;
    }
    div[data-testid="stFormSubmitButton"] > button:active {
        box-shadow: 0 2px 0 #003a80, 0 4px 10px rgba(0, 242, 254, 0.3) !important;
        transform: translateY(4px) !important;
    }

    div.stButton > button {
        background: linear-gradient(135deg, #00f2fe 0%, #0072ff 100%) !important;
        color: #03081a !important;
        font-family: 'Orbitron', sans-serif !important;
        font-weight: 800 !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 10px 22px !important;
        box-shadow: 0 5px 0 #0050aa, 0 10px 20px rgba(0, 242, 254, 0.35) !important;
        transition: all 0.15s ease !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 7px 0 #0050aa, 0 14px 26px rgba(0, 255, 204, 0.5) !important;
    }

    .audio-btn-speak {
        background: linear-gradient(135deg, #00f2fe, #00ffcc);
        border: none;
        color: #03081a;
        font-weight: 700;
        padding: 6px 14px;
        border-radius: 10px;
        cursor: pointer;
        font-size: 13px;
        box-shadow: 0 2px 8px rgba(0, 255, 204, 0.4);
    }

    .audio-btn-stop {
        background: linear-gradient(135deg, #ff007f, #f43f5e);
        border: none;
        color: #ffffff;
        font-weight: 700;
        padding: 6px 14px;
        border-radius: 10px;
        cursor: pointer;
        font-size: 13px;
        box-shadow: 0 2px 8px rgba(255, 0, 127, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SESSION STATE & 2-DAY RULE -----------------
query_user = st.query_params.get("user", "")

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = query_user if query_user else None

if "guest_install_time" not in st.session_state:
    st.session_state.guest_install_time = time.time()

if "current_view" not in st.session_state:
    st.session_state.current_view = "home"

if "home_modal_shown" not in st.session_state:
    st.session_state.home_modal_shown = False

if "guest_messages" not in st.session_state:
    st.session_state.guest_messages = [
        {"role": "assistant", "content": "Welcome to Zeno AI. Ask any question in Kannada or English, or upload PDF documents from the sidebar!"}
    ]

# 2-Day Trial Rule (48 Hours)
TWO_DAYS_IN_SECONDS = 2 * 24 * 60 * 60
is_logged_in = st.session_state.logged_in_user is not None

if not is_logged_in:
    elapsed_seconds = int(time.time() - st.session_state.guest_install_time)
    trial_expired = (elapsed_seconds >= TWO_DAYS_IN_SECONDS)
else:
    trial_expired = False

# Hide Sidebar completely on Home screen
if st.session_state.current_view == "home":
    st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="collapsedControl"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

# ----------------- GROQ API CALLER -----------------
raw_key = st.secrets.get("GROQ_API_KEY", "") or os.environ.get("GROQ_API_KEY", "")
API_KEYS = [k.strip().replace('"', '').replace("'", "") for k in raw_key.split(",") if k.strip()]

def call_groq_api_robust(prompt):
    if not API_KEYS:
        return "GROQ_API_KEY Missing! Please add GROQ_API_KEY to Streamlit Secrets."

    system_instruction = (
        "You are Zeno AI, an ultra-advanced intelligent AI core. "
        "Strict Language Rules:\n"
        "1. If user asks in Kannada (Kannada script or Tanglish), respond strictly in clear Kannada.\n"
        "2. If user asks in English or any other language, respond strictly in English.\n"
        "3. Provide direct, accurate, structured, and insightful answers.\n"
        "4. When PDF text is given, thoroughly explain the document, extract key facts, summarize chapters, and give clear takeaways directly."
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
                "temperature": 0.3
            }
            body_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(chat_url, data=body_data, headers=headers, method="POST")

            try:
                with urllib.request.urlopen(req, timeout=20) as response:
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

# ----------------- SIGN IN / SIGN UP (AFTER 2 DAYS) -----------------
if not is_logged_in and trial_expired:
    st.markdown("""
    <div style="background: rgba(14, 22, 58, 0.95); border: 2px solid #ff007f; border-radius: 24px; padding: 30px 20px; text-align: center; max-width: 520px; margin: 40px auto; box-shadow: 0 15px 40px rgba(255, 0, 127, 0.4);">
        <div style="font-size: 3rem;">⚡</div>
        <div style="color: #ff007f; font-family: 'Orbitron'; font-weight: 800; font-size: 1.2rem;">2-DAY FREE TRIAL COMPLETED</div>
        <div class="hero-title" style="font-size: 2rem;">ZENO AI</div>
        <p style="color: #e0f7fa; font-size: 1rem; margin-top: 6px;">
            Your 2-day trial has concluded. Sign In or Create an Account to unlock permanent lifetime cloud sync!
        </p>
    </div>
    """, unsafe_allow_html=True)

    auth_tab1, auth_tab2 = st.tabs(["🔑 Sign In", "📝 Create Account (Sign Up)"])
    users_db = load_data(USERS_FILE, {})

    with auth_tab1:
        st.subheader("Sign In Once")
        login_id = st.text_input("Username", key="login_id")
        login_pwd = st.text_input("Password", type="password", key="login_pwd")

        if st.button("🚀 Sign In & Unlock Forever", use_container_width=True):
            user_record = users_db.get(login_id)
            if user_record and ((user_record["password"] if isinstance(user_record, dict) else user_record) == login_pwd):
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
        st.subheader("New User Registration")
        new_id = st.text_input("Choose Username", key="reg_id")
        new_pwd = st.text_input("Create Password", type="password", key="reg_pwd")
        new_pwd_confirm = st.text_input("Confirm Password", type="password", key="reg_pwd_confirm")

        if st.button("✨ Create Account & Proceed", use_container_width=True):
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

# ----------------- MAIN APP -----------------
else:
    all_histories = load_data(HISTORY_FILE, {})

    if not is_logged_in:
        current_user = "Guest"
        user_messages = st.session_state.guest_messages
    else:
        current_user = st.session_state.logged_in_user
        if current_user not in all_histories:
            all_histories[current_user] = [
                {"role": "assistant", "content": f"Hello {current_user}! Ask me anything or upload PDF files from the sidebar."}
            ]
        user_messages = all_histories[current_user]

    # ================= 1. HOME SCREEN (POP-UP MODAL INCLUDED) =================
    if st.session_state.current_view == "home":
        
        # HOME PAGE MODAL POP-UP DIALOG
        @st.dialog("⚡ Welcome to ZENO AI Core")
        def show_welcome_popup():
            st.markdown("""
            <div style="text-align: center; margin-bottom: 15px;">
                <div style="font-size: 2.5rem;">⚡</div>
                <h3 style="font-family: 'Orbitron'; color: #00ffcc; margin: 5px 0;">Next-Gen Intelligence Active</h3>
                <p style="color: #94a3b8; font-size: 0.95rem;">Experience high-speed reasoning, deep PDF comprehension, and adaptive multilingual assistance.</p>
            </div>
            <div style="background: rgba(16, 24, 60, 0.8); border: 1px solid #00f2fe; border-radius: 14px; padding: 14px; margin-bottom: 15px;">
                <p style="margin: 4px 0; color: #e2e8f0;">📄 <b>Autonomous PDF Synthesis:</b> Upload docs for instant summaries.</p>
                <p style="margin: 4px 0; color: #e2e8f0;">🌐 <b>Bilingual Core:</b> Supports English and Kannada seamlessly.</p>
                <p style="margin: 4px 0; color: #e2e8f0;">🔊 <b>Voice Output:</b> Read Aloud audio synthesizer ready.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🚀 Enter AI Chat Hub", use_container_width=True):
                st.session_state.current_view = "chat"
                st.rerun()

        if not st.session_state.home_modal_shown:
            st.session_state.home_modal_shown = True
            show_welcome_popup()

        st.markdown("""
        <div style="text-align: center; margin-top: 25px;">
            <div style="font-size: 3.8rem; filter: drop-shadow(0 0 25px #00f2fe);">⚡</div>
            <div class="hero-title">ZENO AI</div>
            <div class="hero-subtitle">NEXT-GENERATION ARTIFICIAL INTELLIGENCE CORE</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="main-box-3d">
            <h3 style="font-family: 'Orbitron'; color: #00ffcc; margin-top: 0; margin-bottom: 20px;">⚡ What Zeno AI Delivers</h3>
            <div class="feature-item">
                <div class="feature-icon-badge">📄</div>
                <div>
                    <b style="color: #38bdf8;">Autonomous PDF Synthesis</b><br/>
                    <span style="color: #94a3b8; font-size: 0.95rem;">Upload study notes, research papers, or syllabus documents for comprehensive textual extraction and summary.</span>
                </div>
            </div>
            <div class="feature-item">
                <div class="feature-icon-badge">🌐</div>
                <div>
                    <b style="color: #38bdf8;">Adaptive Bilingual Engine</b><br/>
                    <span style="color: #94a3b8; font-size: 0.95rem;">Responds accurately in Kannada when queried in Kannada, and delivers fluent responses strictly in English for all general requests.</span>
                </div>
            </div>
            <div class="feature-item">
                <div class="feature-icon-badge">🔊</div>
                <div>
                    <b style="color: #38bdf8;">Dynamic Speech Synthesizer</b><br/>
                    <span style="color: #94a3b8; font-size: 0.95rem;">Listen to AI responses hands-free with high-fidelity Read Aloud and instant Stop playback controls.</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_h1, col_h2, col_h3 = st.columns([1, 2, 1])
        with col_h2:
            if st.button("💬 Launch AI Chat Hub", use_container_width=True):
                st.session_state.current_view = "chat"
                st.rerun()

    # ================= 2. CHAT HUB =================
    else:
        with st.sidebar:
            st.markdown("""
            <div style="text-align: center; padding: 10px 0;">
                <div style="font-size: 2.2rem;">⚡</div>
                <div style="font-family: 'Orbitron'; font-size: 1.2rem; font-weight: 800; color: #00ffcc;">ZENO CHAT</div>
                <div style="font-size: 0.85rem; color: #80deea;">User: <b>{}</b></div>
            </div>
            """.format(current_user), unsafe_allow_html=True)

            if st.button("🏠 Return to Home", use_container_width=True):
                st.session_state.current_view = "home"
                st.rerun()

            st.markdown("---")
            # PDF UPLOAD HUB
            st.markdown("### 📄 PDF Document Hub")
            pdf_file = st.file_uploader(
                "Upload PDF",
                type=["pdf"],
                key="chat_pdf_uploader",
                label_visibility="collapsed"
            )

            if "last_processed_pdf" not in st.session_state:
                st.session_state.last_processed_pdf = None

            if pdf_file is not None and pdf_file.name != st.session_state.last_processed_pdf:
                st.session_state.last_processed_pdf = pdf_file.name
                
                try:
                    reader = PdfReader(pdf_file)
                    extracted_text = ""
                    for page in reader.pages[:10]:
                        extracted_text += page.extract_text() or ""
                    
                    if not extracted_text.strip():
                        extracted_text = "Note: PDF contains scanned images or no selectable text."
                except Exception as e:
                    extracted_text = f"Error reading PDF content: {str(e)}"

                pdf_prompt = (
                    f"User uploaded a PDF named '{pdf_file.name}'.\n\n"
                    f"--- EXTRACTED PDF TEXT START ---\n{extracted_text[:6000]}\n--- EXTRACTED PDF TEXT END ---\n\n"
                    "Please analyze this PDF document thoroughly based on the text above. "
                    "Provide a clear, detailed summary, explain all main topics, important key points, and takeaways directly to the user."
                )

                user_messages.append({"role": "user", "content": f"📄 [Uploaded Document: {pdf_file.name}] Please explain this PDF in detail."})

                with st.spinner("⚡ Extracting and analyzing PDF document..."):
                    pdf_reply = call_groq_api_robust(pdf_prompt)

                user_messages.append({"role": "assistant", "content": pdf_reply})

                if is_logged_in:
                    all_histories[current_user] = user_messages
                    save_data(HISTORY_FILE, all_histories)
                st.rerun()

            st.markdown("---")
            st.markdown("### 📁 Saved Threads")
            user_queries = [m["content"] for m in user_messages if m["role"] == "user"]
            if not user_queries:
                st.caption("No history yet.")
            else:
                for q in reversed(user_queries[-6:]):
                    clean_q = re.sub(r'\[.*?\]', '', q).strip()
                    preview = clean_q[:22] + "..." if len(clean_q) > 22 else clean_q
                    st.markdown(f"• {preview}")

            st.markdown("---")
            if is_logged_in:
                if st.button("🚪 Sign Out", use_container_width=True):
                    st.session_state.logged_in_user = None
                    st.query_params.clear()
                    st.session_state.guest_install_time = time.time()
                    st.session_state.current_view = "home"
                    st.rerun()

        # Top Header
        st.markdown('<div class="hero-title" style="font-size: 1.8rem; margin: 0 0 10px 0;">⚡ ZENO AI CHAT HUB</div>', unsafe_allow_html=True)

        # Chat History Display
        for msg in user_messages:
            avatar = "⚡" if msg["role"] == "assistant" else "👤"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

                # AUDIO CONTROLS
                if msg["role"] == "assistant" and len(msg["content"].strip()) > 0:
                    clean_speech = re.sub(r'[*#_`]', '', msg["content"][:280]).replace('"', '').replace("'", "").replace('\n', ' ')
                    encoded_speech = urllib.parse.quote(clean_speech)
                    tts_ui = f"""
                    <div style="margin-top: 8px; display: flex; gap: 10px;">
                        <button class="audio-btn-speak" onclick="speakText('{encoded_speech}')">🔊 Read Aloud</button>
                        <button class="audio-btn-stop" onclick="window.speechSynthesis.cancel()">⏹ Stop</button>
                    </div>
                    <script>
                        function speakText(enc) {{
                            if ('speechSynthesis' in window) {{
                                window.speechSynthesis.cancel();
                                const txt = decodeURIComponent(enc);
                                const u = new SpeechSynthesisUtterance(txt);
                                u.rate = 1.0;
                                window.speechSynthesis.speak(u);
                            }}
                        }}
                    </script>
                    """
                    st.components.v1.html(tts_ui, height=45)

        # 3D TACTILE SEND FORM WITH AUTO-CLEAR
        with st.form("chat_input_form", clear_on_submit=True):
            col_t, col_s = st.columns([4.2, 0.8])
            with col_t:
                user_input = st.text_input(
                    "Message",
                    placeholder="Ask Zeno anything...",
                    key="chat_prompt_input_field",
                    label_visibility="collapsed"
                )
            with col_s:
                send_clicked = st.form_submit_button("🚀 Send", use_container_width=True)

        if send_clicked and user_input.strip():
            user_text = user_input.strip()
            user_messages.append({"role": "user", "content": user_text})

            with st.spinner("⚡ Zeno is thinking..."):
                raw_reply = call_groq_api_robust(user_text)
            user_messages.append({"role": "assistant", "content": raw_reply})

            if is_logged_in:
                all_histories[current_user] = user_messages
                save_data(HISTORY_FILE, all_histories)
            st.rerun()
