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
        return False, "Password minimum 8 characters erbeku."
    if not re.search(r"\d", password):
        return False, "Password nalli ondhu number (0-9) erbeku."
    if not re.search(r"[@#$%^&*!_\-+=]", password):
        return False, "Password nalli ondhu special symbol erbeku."
    return True, "Strong Password!"

# ----------------- STYLING -----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800;900&family=Rajdhani:wght@500;600;700&display=swap');

    .stApp {
        background: radial-gradient(circle at 50% 0%, #0d1238 0%, #060919 60%, #020308 100%);
        color: #e0f7fa;
        font-family: 'Rajdhani', sans-serif;
    }

    .hero-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 2.8rem;
        font-weight: 900;
        letter-spacing: 3px;
        background: linear-gradient(90deg, #00f2fe 0%, #00ffcc 50%, #ff007f 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 30px rgba(0, 242, 254, 0.5);
        margin: 5px 0;
    }

    .main-box-3d {
        background: linear-gradient(145deg, rgba(16, 24, 60, 0.9), rgba(7, 12, 35, 0.95));
        border: 2px solid rgba(0, 242, 254, 0.5);
        border-radius: 24px;
        padding: 30px 25px;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.7), 0 0 25px rgba(0, 242, 254, 0.25);
        max-width: 800px;
        margin: 20px auto;
        text-align: left;
    }

    div.stButton > button {
        background: linear-gradient(135deg, #00f2fe 0%, #0072ff 100%) !important;
        color: #03081a !important;
        font-family: 'Orbitron', sans-serif !important;
        font-weight: 800 !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 10px 22px !important;
        box-shadow: 0 6px 0 #0050aa, 0 12px 25px rgba(0, 242, 254, 0.4) !important;
        transition: all 0.15s ease !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 0 #0050aa, 0 16px 30px rgba(0, 255, 204, 0.6) !important;
    }

    .speaker-btn-3d {
        background: linear-gradient(135deg, #00ffcc, #0072ff);
        border: none;
        color: #03081a;
        font-weight: 800;
        padding: 6px 14px;
        border-radius: 12px;
        cursor: pointer;
        font-size: 13px;
        box-shadow: 0 3px 0 #004ba0, 0 6px 15px rgba(0, 255, 204, 0.3);
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

if "guest_messages" not in st.session_state:
    st.session_state.guest_messages = [
        {"role": "assistant", "content": "Welcome to Zeno AI. Ask any question in Kannada or English, upload PDF documents, or generate images!"}
    ]

# 2-Day Trial
TWO_DAYS_IN_SECONDS = 2 * 24 * 60 * 60
is_logged_in = st.session_state.logged_in_user is not None

if not is_logged_in:
    elapsed_seconds = int(time.time() - st.session_state.guest_install_time)
    trial_expired = (elapsed_seconds >= TWO_DAYS_IN_SECONDS)
else:
    trial_expired = False

# Hide Sidebar on Home Screen via CSS
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
        return "GROQ_API_KEY Missing! Streamlit Secrets nalli GROQ_API_KEY add maadi."

    system_instruction = (
        "You are Zeno AI, an ultra-advanced intelligent AI core. "
        "Strict Language Rules:\n"
        "1. If user asks in Kannada (Kannada script or Tanglish), respond strictly in clear Kannada.\n"
        "2. If user asks in English or any other language, respond strictly in English.\n"
        "3. Provide direct, accurate, structured, and insightful answers.\n"
        "4. When PDF text is given, thoroughly explain the document, extract key facts, summarize chapters, and give clear takeaways directly without saying you cannot read it."
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
            Nimma 2 dinada free trial mugidide. Sign In athava Sign Up maadi lifelong access unlock maadi!
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
                st.warning("Details fill maadi.")
            elif not is_valid:
                st.error(msg)
            elif new_pwd != new_pwd_confirm:
                st.error("Passwords match aagthilla!")
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
                {"role": "assistant", "content": f"Hello {current_user}! Ask me anything or upload PDF files from sidebar."}
            ]
        user_messages = all_histories[current_user]

    # ================= 1. HOME SCREEN (SIDEBAR COMPLETE OFF) =================
    if st.session_state.current_view == "home":
        st.markdown("""
        <div style="text-align: center; margin-top: 25px;">
            <div style="font-size: 3.8rem; filter: drop-shadow(0 0 25px #00f2fe);">⚡</div>
            <div class="hero-title">ZENO AI</div>
            <div style="font-size: 1.1rem; color: #80deea; font-weight: 600;">SMART MULTI-PURPOSE INTELLIGENCE</div>
        </div>
        """, unsafe_allow_html=True)

        # Single Box Explaining Everything Zeno Does
        st.markdown("""
        <div class="main-box-3d">
            <h3 style="font-family: 'Orbitron'; color: #00ffcc; margin-top: 0;">⚡ Zeno AI Enella Maaduththe?</h3>
            <ul style="font-size: 1.05rem; line-height: 1.8; color: #e0f7fa;">
                <li><b>📄 Direct PDF Analysis:</b> Yaavude PDF notes, syllabus, athava documents upload maadidre poorthi scan maadi extract maaduththe[span_2](start_span)[span_2](end_span).</li>
                <li><b>🗣️ Bilingual Intelligence:</b> User Kannada dalli kelidre Kannada dalli, English nalli kelidre English nalli clear factual uthira koduththe.</li>
                <li><b>🎨 Instant Image Generator:</b> <code>image: your prompt</code> antha type maadidaga real-time HD AI visuals generate maaduththe.</li>
                <li><b>🔊 Voice Read Aloud:</b> AI kotto answer na hands-free aagi keloke Read Aloud audio support ide.</li>
                <li><b>⚡ Zero Clutter:</b> Camera athava unnecessary features illade, fast mathu accurate search engine.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        col_h1, col_h2, col_h3 = st.columns([1, 2, 1])
        with col_h2:
            if st.button("💬 Go to Chat with AI", use_container_width=True):
                st.session_state.current_view = "chat"
                st.rerun()

    # ================= 2. CHAT HUB (SIDEBAR ON + GO TO HOME BUTTON) =================
    else:
        # Sidebar mathra Chat view nalli open iraththe
        with st.sidebar:
            st.markdown("""
            <div style="text-align: center; padding: 10px 0;">
                <div style="font-size: 2.2rem;">⚡</div>
                <div style="font-family: 'Orbitron'; font-size: 1.2rem; font-weight: 800; color: #00ffcc;">ZENO CHAT</div>
                <div style="font-size: 0.85rem; color: #80deea;">User: <b>{}</b></div>
            </div>
            """.format(current_user), unsafe_allow_html=True)

            # GO TO HOME PAGE BUTTON
            if st.button("🏠 Go to Home Page", use_container_width=True):
                st.session_state.current_view = "home"
                st.rerun()

            st.markdown("---")
            # PDF UPLOAD HUB (Direct Text Extraction)
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
                
                # PDF inda text direct extract maaduvudu
                try:
                    reader = PdfReader(pdf_file)
                    extracted_text = ""
                    for page in reader.pages[:10]:  # First 10 pages for speed
                        extracted_text += page.extract_text() or ""
                    
                    if not extracted_text.strip():
                        extracted_text = "Note: PDF appears to contain scanned images or no direct selectable text."
                except Exception as e:
                    extracted_text = f"Error reading PDF content: {str(e)}"

                pdf_prompt = (
                    f"User uploaded a PDF named '{pdf_file.name}'.\n\n"
                    f"--- EXTRACTED PDF TEXT START ---\n{extracted_text[:6000]}\n--- EXTRACTED PDF TEXT END ---\n\n"
                    "Please analyze this PDF document thoroughly based on the text above. "
                    "Provide a clear, detailed summary, explain all main topics, important key points, and takeaways directly to the user."
                )

                user_messages.append({"role": "user", "content": f"📄 [Uploaded Document: {pdf_file.name}] Please explain this PDF in detail."})

                with st.spinner("⚡ Zeno is extracting and reading the PDF text..."):
                    pdf_reply = call_groq_api_robust(pdf_prompt)

                user_messages.append({"role": "assistant", "content": pdf_reply})

                if is_logged_in:
                    all_histories[current_user] = user_messages
                    save_data(HISTORY_FILE, all_histories)
                st.rerun()

            st.markdown("---")
            st.markdown("### 📁 Saved Chats")
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

        # Top Header in Chat
        c_head1, c_head2 = st.columns([3, 1])
        with c_head1:
            st.markdown('<div class="hero-title" style="font-size: 1.8rem; margin: 0;">⚡ ZENO AI CHAT</div>', unsafe_allow_html=True)
            st.caption("Ask questions, upload PDFs in sidebar, or generate images.")
        with c_head2:
            if st.button("🏠 Home Page", use_container_width=True):
                st.session_state.current_view = "home"
                st.rerun()

        # Chat History Display
        for msg in user_messages:
            avatar = "⚡" if msg["role"] == "assistant" else "👤"
            with st.chat_message(msg["role"], avatar=avatar):
                if msg.get("image_url"):
                    st.image(msg["image_url"], caption="Generated Visual")
                st.markdown(msg["content"])

                if msg["role"] == "assistant" and len(msg["content"].strip()) > 0:
                    clean_speech = re.sub(r'[*#_`]', '', msg["content"][:280]).replace('"', '').replace("'", "").replace('\n', ' ')
                    encoded_speech = urllib.parse.quote(clean_speech)
                    tts_ui = f"""
                    <div style="margin-top: 6px; display: flex; gap: 8px;">
                        <button class="speaker-btn-3d" onclick="speakText('{encoded_speech}')">🔊 Read Aloud</button>
                        <button class="speaker-btn-3d" style="background: rgba(255, 0, 127, 0.4); color: #fff;" onclick="window.speechSynthesis.cancel()">⏹ Stop</button>
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
                    st.components.v1.html(tts_ui, height=40)

        # Chat Input Box
        st.markdown('<div style="background: rgba(13, 20, 50, 0.85); border: 1.5px solid #00f2fe; border-radius: 18px; padding: 10px 14px; margin-top: 15px;">', unsafe_allow_html=True)
        col_t, col_s = st.columns([4.2, 0.8])
        with col_t:
            user_input = st.text_input(
                "Message",
                placeholder="Ask Zeno in Kannada/English or type 'image: car'...",
                key="chat_prompt_input",
                label_visibility="collapsed"
            )
        with col_s:
            send_clicked = st.button("🚀 Send", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if send_clicked and user_input.strip():
            user_text = user_input.strip()
            user_messages.append({"role": "user", "content": user_text})

            lower_val = user_text.lower()
            if lower_val.startswith("image:") or lower_val.startswith("generate image:"):
                img_desc = user_text.split(":", 1)[1].strip()
                encoded_desc = urllib.parse.quote(img_desc)
                gen_image_url = f"https://image.pollinations.ai/prompt/{encoded_desc}?width=768&height=768&nologo=true"

                reply_txt = f"Generated visual for: **{img_desc}**"
                user_messages.append({"role": "assistant", "content": reply_txt, "image_url": gen_image_url})
            else:
                with st.spinner("⚡ Zeno is thinking..."):
                    raw_reply = call_groq_api_robust(user_text)
                user_messages.append({"role": "assistant", "content": raw_reply})

            if is_logged_in:
                all_histories[current_user] = user_messages
                save_data(HISTORY_FILE, all_histories)
            st.rerun()
