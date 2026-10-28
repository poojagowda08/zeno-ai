import streamlit as st
import os
import json
import urllib.request
import urllib.parse
import urllib.error
from PIL import Image

# ----------------- PAGE CONFIG -----------------
st.set_page_config(
    page_title="ZENO AI | English Tutor & Core",
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
        background: rgba(10, 16, 38, 0.88);
        border: 2px solid rgba(0, 242, 254, 0.45);
        box-shadow: 0 0 35px rgba(0, 242, 254, 0.25);
        border-radius: 22px;
        padding: 35px 25px;
        text-align: center;
        backdrop-filter: blur(12px);
        margin: 20px auto;
        max-width: 550px;
    }

    .zeno-brand {
        font-family: 'Orbitron', sans-serif;
        font-size: 2.6rem;
        font-weight: 900;
        letter-spacing: 2px;
        background: linear-gradient(90deg, #00f2fe 0%, #4facfe 50%, #b388ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 6px;
    }

    .core-orb {
        width: 85px;
        height: 85px;
        border-radius: 50%;
        background: radial-gradient(circle, #00f2fe 10%, #7f00ff 70%, #03050c 100%);
        box-shadow: 0 0 30px #00f2fe, 0 0 60px rgba(127, 0, 255, 0.6);
        animation: pulseOrb 2.2s infinite alternate ease-in-out;
        margin: 15px auto;
    }

    @keyframes pulseOrb {
        0% { transform: scale(0.95); box-shadow: 0 0 20px #00f2fe; }
        100% { transform: scale(1.08); box-shadow: 0 0 45px #00f2fe, 0 0 80px #7f00ff; }
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

if "spoken_welcome" not in st.session_state:
    st.session_state.spoken_welcome = False

# ----------------- GROQ API HELPER (ENGLISH TUTOR PROMPT) -----------------
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

    # AI Persona: English Teaching Assistant + General QA
    system_instruction = (
        "You are Zeno, an encouraging, friendly, and expert English Learning Voice Assistant. "
        "Your mission is to help the user speak, learn, and master English comfortably. "
        "Whenever the user speaks or types with grammatical errors, gently correct them first in a simple sentence, "
        "then provide the best natural phrasing. If they ask general questions, answer accurately and politely. "
        "Always keep answers short, conversational, and direct (2 to 3 sentences maximum) so it can be spoken out loud. "
        "Never use markdown symbols, bullet points, or asterisks."
    )

    for selected_model in available_models:
        payload = {
            "model": selected_model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.6
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

    return "Service temporarily busy. Please ask again."

# ----------------- AUTHENTICATION SYSTEM -----------------
if not st.session_state.logged_in_user:
    st.markdown("""
    <div class="enter-card">
        <div style="color: #00f2fe; font-weight: bold; letter-spacing: 2px;">NEURAL LEARNING PLATFORM</div>
        <div class="zeno-brand">⚡ ZENO AI ⚡</div>
        <p style="color: #80deea; font-size: 1.1rem; margin-top: -5px;">Personal Interactive English Voice Tutor</p>
        <div class="core-orb"></div>
    </div>
    """, unsafe_allow_html=True)

    auth_tab1, auth_tab2 = st.tabs(["🔑 Sign In", "📝 Create Account (Sign Up)"])
    users_db = load_data(USERS_FILE, {})

    with auth_tab1:
        st.subheader("Login to your Account")
        login_id = st.text_input("Username or Email", key="login_id")
        login_pwd = st.text_input("Password", type="password", key="login_pwd")
        
        if st.button("🚀 Sign In to Zeno AI", use_container_width=True):
            if login_id in users_db and users_db[login_id] == login_pwd:
                st.session_state.logged_in_user = login_id
                st.session_state.spoken_welcome = False
                st.success("Access Granted! Loading Zeno AI...")
                st.rerun()
            else:
                st.error("Invalid Username or Password. Try again or Sign Up.")

    with auth_tab2:
        st.subheader("New User Registration")
        new_id = st.text_input("Choose Username or Email", key="reg_id")
        new_pwd = st.text_input("Create Password", type="password", key="reg_pwd")
        new_pwd_confirm = st.text_input("Confirm Password", type="password", key="reg_pwd_confirm")

        if st.button("✨ Create Account & Enter", use_container_width=True):
            if not new_id or not new_pwd:
                st.warning("Please fill all details.")
            elif new_pwd != new_pwd_confirm:
                st.error("Passwords do not match!")
            elif new_id in users_db:
                st.error("Username already registered. Please Sign In.")
            else:
                users_db[new_id] = new_pwd
                save_data(USERS_FILE, users_db)
                st.session_state.logged_in_user = new_id
                st.session_state.spoken_welcome = False
                st.success("Account created successfully! Logging you in...")
                st.rerun()

# ----------------- MAIN TUTOR DASHBOARD -----------------
else:
    user_id = st.session_state.logged_in_user
    all_histories = load_data(HISTORY_FILE, {})
    
    if user_id not in all_histories:
        all_histories[user_id] = [
            {"role": "assistant", "content": f"Hello {user_id}! I am Zeno, your English tutor. What would you like to learn or practice today?"}
        ]

    user_messages = all_histories[user_id]

    # TOP HEADER & LOGOUT
    head_col1, head_col2 = st.columns([3, 1])
    with head_col1:
        st.markdown(f'<div class="zeno-brand" style="font-size: 1.9rem;">⚡ ZENO AI | ENGLISH TUTOR ⚡</div>', unsafe_allow_html=True)
        st.caption(f"Logged in as: **{user_id}**")
    with head_col2:
        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state.logged_in_user = None
            st.session_state.spoken_welcome = False
            st.rerun()

    st.markdown('<div class="core-orb" style="width: 55px; height: 55px;"></div>', unsafe_allow_html=True)

    # AUTOMATIC VOICE WELCOME ON LOGIN
    if not st.session_state.spoken_welcome:
        st.session_state.spoken_welcome = True
        auto_speech_text = f"Hello {user_id}! I am Zeno, your English tutor. Shall we practice speaking English today?"
        st.components.v1.html(f"""
        <script>
            if ('speechSynthesis' in window) {{
                window.speechSynthesis.cancel();
                const utter = new SpeechSynthesisUtterance("{auto_speech_text}");
                utter.rate = 1.0;
                window.speechSynthesis.speak(utter);
            }}
        </script>
        """, height=0)

    # TOOLS & MEDIA EXPANDER
    with st.expander("📂 UPLOAD PHOTOS / AUDIO / PRACTICE SHEETS", expanded=False):
        c_up1, c_up2 = st.columns([2, 1])
        with c_up1:
            multi_file = st.file_uploader(
                "Upload Image, Audio recording, or Notes",
                type=["png", "jpg", "jpeg", "mp3", "wav", "pdf", "txt"],
                key="direct_multi_uploader"
            )
            if multi_file:
                st.success(f"Attached: {multi_file.name}")
                if multi_file.type.startswith("image/"):
                    st.image(multi_file, width=200)
                elif multi_file.type.startswith("audio/"):
                    st.audio(multi_file)

        with c_up2:
            st.write("### Tutor Controls")
            if st.button("🗑️ Reset Chat History", use_container_width=True):
                all_histories[user_id] = [
                    {"role": "assistant", "content": "Memory refreshed. Ready to practice speaking!"}
                ]
                save_data(HISTORY_FILE, all_histories)
                st.rerun()

    # TOUCH-TO-SPEAK COMPONENT
    mic_html = """
    <div style="text-align: center; margin: 8px 0;">
        <button id="micBtn" style="
            background: linear-gradient(45deg, #00f2fe, #4facfe);
            border: none;
            color: #04091a;
            padding: 12px 28px;
            border-radius: 25px;
            font-weight: 800;
            font-size: 15px;
            cursor: pointer;
            box-shadow: 0 0 20px rgba(0, 242, 254, 0.45);
            letter-spacing: 1px;
            outline: none;
        ">🎙️ TOUCH TO SPEAK (PRACTICE ENGLISH)</button>
        <div id="status" style="color: #80deea; font-size: 13px; margin-top: 6px;">Tap and speak in English or ask any query</div>
    </div>
    <script>
        const micBtn = document.getElementById('micBtn');
        const status = document.getElementById('status');
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {
            status.innerText = "Speech recognition requires Google Chrome.";
        } else {
            const recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-US';

            let isListening = false;

            micBtn.onclick = async () => {
                if (isListening) {
                    recognition.stop();
                    return;
                }
                try {
                    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                        await navigator.mediaDevices.getUserMedia({ audio: true });
                    }
                    recognition.start();
                    isListening = true;
                    status.innerText = "🔴 Listening... Speak clearly now";
                    micBtn.style.background = "#ff1744";
                    micBtn.innerText = "🛑 STOP SPEAKING";
                } catch (e) {
                    status.innerText = "Allow Microphone permission in Chrome settings.";
                    resetBtn();
                }
            };

            recognition.onresult = (event) => {
                const text = event.results[0][0].transcript;
                status.innerText = "Heard: " + text;

                const parentDoc = window.parent.document;
                const textarea = parentDoc.querySelector('textarea[aria-label="Ask Zeno or practice your English sentence..."]') ||
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

            recognition.onerror = () => {
                status.innerText = "Mic error. Please tap again.";
                resetBtn();
            };

            recognition.onend = () => {
                resetBtn();
            };

            function resetBtn() {
                isListening = false;
                micBtn.style.background = "linear-gradient(45deg, #00f2fe, #4facfe)";
                micBtn.innerText = "🎙️ TOUCH TO SPEAK (PRACTICE ENGLISH)";
            }
        }
    </script>
    """
    st.components.v1.html(mic_html, height=95)

    # DISPLAY CHAT HISTORY
    for msg in user_messages:
        avatar = "🎓" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            if msg.get("image_url"):
                st.image(msg["image_url"], caption="Generated Illustration")
            st.markdown(msg["content"])

    # CHAT INPUT
    user_prompt = st.chat_input("Ask Zeno or practice your English sentence... (e.g. 'How do I introduce myself?')")

    if user_prompt:
        user_messages.append({"role": "user", "content": user_prompt})
        all_histories[user_id] = user_messages
        save_data(HISTORY_FILE, all_histories)

        with st.chat_message("user", avatar="👤"):
            st.markdown(user_prompt)

        with st.chat_message("assistant", avatar="🎓"):
            lower_input = user_prompt.lower().strip()
            
            # 1. IMAGE GENERATION COMMAND
            if lower_input.startswith("image:") or lower_input.startswith("generate image:"):
                img_desc = user_prompt.split(":", 1)[1].strip()
                encoded_desc = urllib.parse.quote(img_desc)
                gen_image_url = f"https://image.pollinations.ai/prompt/{encoded_desc}?width=768&height=768&nologo=true"
                
                reply_txt = f"Here is the visual representation for: {img_desc}"
                st.image(gen_image_url, caption=f"Prompt: {img_desc}")
                st.markdown(reply_txt)

                user_messages.append({"role": "assistant", "content": reply_txt, "image_url": gen_image_url})
                all_histories[user_id] = user_messages
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

            # 2. ENGLISH LEARNING & GENERAL QA
            else:
                if not groq_key:
                    st.error("GROQ_API_KEY Missing! Streamlit Secrets nalli GROQ_API_KEY add maadi.")
                else:
                    raw_reply = call_groq_api(user_prompt, groq_key)
                    clean_reply = raw_reply.replace("*", "").replace("#", "").replace('"', '').replace("'", "").strip()
                    st.markdown(clean_reply)

                    user_messages.append({"role": "assistant", "content": clean_reply})
                    all_histories[user_id] = user_messages
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
