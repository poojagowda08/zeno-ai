import streamlit as st
import os
from PIL import Image
from pypdf import PdfReader
from google import genai
from google.genai import types

# ----------------- PAGE CONFIG -----------------
st.set_page_config(
    page_title="ZENO AI | Futuristic Core",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ----------------- ADVANCED CYBERPUNK STYLING -----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800;900&family=Rajdhani:wght@500;600;700&display=swap');

    .stApp {
        background: radial-gradient(circle at 50% 15%, #090e23 0%, #03050c 100%);
        color: #e0f7fa;
        font-family: 'Rajdhani', sans-serif;
    }

    /* Cinematic Welcome Card */
    .enter-card {
        background: rgba(10, 16, 38, 0.85);
        border: 2px solid rgba(0, 242, 254, 0.45);
        box-shadow: 0 0 40px rgba(0, 242, 254, 0.25), inset 0 0 20px rgba(127, 0, 255, 0.2);
        border-radius: 24px;
        padding: 45px 25px;
        text-align: center;
        backdrop-filter: blur(12px);
        margin: 40px auto;
        max-width: 600px;
        animation: fadeIn 1s ease-in-out;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(15px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .zeno-brand {
        font-family: 'Orbitron', sans-serif;
        font-size: 2.8rem;
        font-weight: 900;
        letter-spacing: 3px;
        background: linear-gradient(90deg, #00f2fe 0%, #4facfe 50%, #b388ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 6px;
    }

    .status-pill {
        display: inline-block;
        padding: 6px 18px;
        border-radius: 20px;
        background: rgba(0, 242, 254, 0.12);
        border: 1px solid #00f2fe;
        color: #00f2fe;
        font-size: 0.85rem;
        font-weight: bold;
        letter-spacing: 2px;
        margin-bottom: 25px;
    }

    /* Glowing Pulsing Core */
    .orb-wrapper {
        display: flex;
        justify-content: center;
        margin: 25px 0;
    }

    .core-orb {
        width: 105px;
        height: 105px;
        border-radius: 50%;
        background: radial-gradient(circle, #00f2fe 10%, #7f00ff 70%, #03050c 100%);
        box-shadow: 0 0 35px #00f2fe, 0 0 70px rgba(127, 0, 255, 0.7);
        animation: pulseOrb 2.2s infinite alternate ease-in-out;
    }

    @keyframes pulseOrb {
        0% { transform: scale(0.94); box-shadow: 0 0 20px #00f2fe; }
        100% { transform: scale(1.08); box-shadow: 0 0 50px #00f2fe, 0 0 85px #7f00ff; }
    }

    section[data-testid="stSidebar"] {
        background-color: #060914;
        border-right: 1px solid rgba(0, 242, 254, 0.25);
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SESSION STATE -----------------
if "app_entered" not in st.session_state:
    st.session_state.app_entered = False

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Zeno core systems active. Tap mic or ask me anything!"}
    ]

# ----------------- API SETUP -----------------
api_key = st.secrets.get("GEMINI_API_KEY", "") or os.environ.get("GEMINI_API_KEY", "")
client = genai.Client(api_key=api_key) if api_key else None

SYSTEM_INSTRUCTION = """
You are Zeno, a hyper-intelligent, polite, and futuristic AI assistant.
Keep spoken replies brief, crisp, and conversational (1 to 2 short sentences).
Never use markdown symbols like asterisks (*) or hashes (#) so the speech synthesizer reads it naturally.
"""

# ----------------- SCREEN 1: CLICK TO ENTER SCREEN -----------------
if not st.session_state.app_entered:
    st.markdown("""
    <div class="enter-card">
        <div class="status-pill">NEURAL CORE READY</div>
        <div class="zeno-brand">⚡ ZENO AI ⚡</div>
        <p style="color: #80deea; font-size: 1.15rem; margin-top: 5px;">
            Next-Gen Multimodal Voice Interface
        </p>
        <div class="orb-wrapper">
            <div class="core-orb"></div>
        </div>
        <p style="color: #90caf9; font-size: 0.92rem; margin-bottom: 25px;">
            Touch-to-Speak • Vision AI • PDF Document Analysis
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        if st.button("✨ CLICK TO ENTER ZENO AI", use_container_width=True):
            st.session_state.app_entered = True
            st.rerun()

# ----------------- SCREEN 2: MAIN DASHBOARD -----------------
else:
    st.markdown('<div class="zeno-brand" style="text-align: center; font-size: 2.1rem; margin-top: -15px;">⚡ ZENO AI CORE ⚡</div>', unsafe_allow_html=True)
    st.markdown('<div class="orb-wrapper"><div class="core-orb" style="width: 70px; height: 70px;"></div></div>', unsafe_allow_html=True)

    # Sidebar inputs
    with st.sidebar:
        st.markdown("### 🎛️ Navigation & Tools")
        if st.button("🚪 Exit to Welcome Screen", use_container_width=True):
            st.session_state.app_entered = False
            st.rerun()

        st.markdown("---")
        st.markdown("### 📂 Upload Files")
        uploaded_image = st.file_uploader("🖼️ Upload Image", type=["jpg", "jpeg", "png"])
        if uploaded_image:
            img = Image.open(uploaded_image)
            st.image(img, caption="Image Ready", use_container_width=True)

        uploaded_pdf = st.file_uploader("📄 Upload PDF", type=["pdf"])
        pdf_extracted_text = ""
        if uploaded_pdf:
            reader = PdfReader(uploaded_pdf)
            for page in reader.pages:
                txt = page.extract_text()
                if txt:
                    pdf_extracted_text += txt
            st.success(f"PDF Loaded ({len(reader.pages)} Pages)")

        uploaded_audio = st.file_uploader("🎵 Upload Audio", type=["mp3", "wav", "ogg"])
        if uploaded_audio:
            st.audio(uploaded_audio)

    # Mic Component
    st.components.v1.html("""
    <div style="text-align: center; margin: 10px 0 15px 0;">
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
        ">🎙️ TOUCH TO SPEAK</button>
        <div id="status" style="color: #80deea; font-size: 13px; margin-top: 8px;">Tap button to speak your command</div>
    </div>

    <script>
        const micBtn = document.getElementById('micBtn');
        const status = document.getElementById('status');
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (SpeechRecognition) {
            const recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-IN';

            let isListening = false;

            micBtn.onclick = () => {
                if (isListening) {
                    recognition.stop();
                    return;
                }
                try {
                    recognition.start();
                    isListening = true;
                    status.innerText = "🔴 Listening... Speak clearly now";
                    micBtn.style.background = "#ff1744";
                    micBtn.innerText = "🛑 STOP SPEAKING";
                } catch (e) {
                    recognition.stop();
                }
            };

            recognition.onresult = (event) => {
                const text = event.results[0][0].transcript;
                status.innerText = "Heard: " + text;

                const doc = window.parent.document;
                const textarea = doc.querySelector('textarea[aria-label="Ask Zeno anything..."]');
                if (textarea) {
                    textarea.value = text;
                    textarea.dispatchEvent(new Event('input', { bubbles: true }));
                    setTimeout(() => {
                        const sendBtn = doc.querySelector('button[data-testid="stBaseButton-secondary"]') || 
                                        doc.querySelector('button[kind="secondaryFormSubmit"]');
                        if (sendBtn) {
                            sendBtn.click();
                        }
                    }, 300);
                }
            };

            recognition.onerror = (e) => {
                status.innerText = "Mic Error. Tap again and allow permission";
                resetBtn();
            };

            recognition.onend = () => {
                resetBtn();
            };

            function resetBtn() {
                isListening = false;
                micBtn.style.background = "linear-gradient(45deg, #00f2fe, #4facfe)";
                micBtn.innerText = "🎙️ TOUCH TO SPEAK";
            }
        } else {
            status.innerText = "Voice Recognition requires Chrome browser.";
        }
    </script>
    """, height=90)

    # Chat Messages
    for msg in st.session_state.messages:
        avatar = "🔮" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # Chat Input
    user_prompt = st.chat_input("Ask Zeno anything...")

    if user_prompt:
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_prompt)

        with st.chat_message("assistant", avatar="🔮"):
            if not client:
                st.error("API Key configure aagilla. Streamlit Secrets nalli GEMINI_API_KEY check maadi.")
            else:
                payload = []
                if pdf_extracted_text:
                    payload.append(f"Context from PDF:\n{pdf_extracted_text[:4000]}\n")
                if uploaded_image:
                    payload.append(Image.open(uploaded_image))
                payload.append(user_prompt)

                # 503 Server Rush ತಪ್ಪಿಸಲು ಆಟೋಮ್ಯಾಟಿಕ್ ಬ್ಯಾಕಪ್ ಮಾಡೆಲ್‌ಗಳು
                candidate_models = ["gemini-1.5-flash-8b", "gemini-1.5-flash", "gemini-2.5-flash"]
                response = None

                for target_model in candidate_models:
                    try:
                        response = client.models.generate_content(
                            model=target_model,
                            contents=payload,
                            config=types.GenerateContentConfig(
                                system_instruction=SYSTEM_INSTRUCTION,
                                temperature=0.6,
                            )
                        )
                        if response and response.text:
                            break
                    except Exception:
                        continue

                if response and response.text:
                    clean_reply = response.text.replace("*", "").replace("#", "").replace('"', '').replace("'", "").strip()
                    st.markdown(clean_reply)
                    st.session_state.messages.append({"role": "assistant", "content": clean_reply})

                    tts_script = f"""
                    <script>
                        if ('speechSynthesis' in window) {{
                            window.speechSynthesis.cancel();
                            const speakNow = () => {{
                                const voices = window.speechSynthesis.getVoices();
                                const utterance = new SpeechSynthesisUtterance("{clean_reply[:250]}");
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
                    st.components.v1.html(tts_script, height=0)
                else:
                    st.error("Google Server High Demand. Please try again in a few seconds.")
