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
    initial_sidebar_state="expanded"
)

# ----------------- ADVANCED CYBERPUNK STYLING -----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@500;600;700&display=swap');

    .stApp {
        background: radial-gradient(circle at 50% 10%, #0d122b 0%, #05070e 100%);
        color: #e0f7fa;
        font-family: 'Rajdhani', sans-serif;
    }

    /* Cinematic Intro Box */
    .intro-card {
        background: rgba(12, 18, 42, 0.75);
        border: 1px solid rgba(0, 242, 254, 0.4);
        box-shadow: 0 0 30px rgba(0, 242, 254, 0.2);
        border-radius: 20px;
        padding: 40px 20px;
        text-align: center;
        backdrop-filter: blur(10px);
        margin: 40px auto;
        max-width: 650px;
    }

    .zeno-brand {
        font-family: 'Orbitron', sans-serif;
        font-size: 2.6rem;
        font-weight: 900;
        letter-spacing: 3px;
        background: linear-gradient(90deg, #00f2fe 0%, #4facfe 50%, #7f00ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
    }

    .status-badge {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 12px;
        background: rgba(0, 242, 254, 0.1);
        border: 1px solid #00f2fe;
        color: #00f2fe;
        font-size: 0.85rem;
        font-weight: bold;
        letter-spacing: 1.5px;
        margin-bottom: 25px;
    }

    /* Glowing Core Orb */
    .orb-wrapper {
        display: flex;
        justify-content: center;
        margin: 20px 0;
    }

    .core-orb {
        width: 100px;
        height: 100px;
        border-radius: 50%;
        background: radial-gradient(circle, #00f2fe 10%, #7f00ff 70%, #05070e 100%);
        box-shadow: 0 0 30px #00f2fe, 0 0 60px rgba(127, 0, 255, 0.7);
        animation: pulseCore 2.5s infinite alternate ease-in-out;
    }

    @keyframes pulseCore {
        0% { transform: scale(0.95); box-shadow: 0 0 20px #00f2fe; }
        100% { transform: scale(1.06); box-shadow: 0 0 45px #00f2fe, 0 0 75px #7f00ff; }
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #070a17;
        border-right: 1px solid rgba(0, 242, 254, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SESSION STATE -----------------
if "app_launched" not in st.session_state:
    st.session_state.app_launched = False

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Zeno core systems operational. How may I assist you today?"}
    ]

# ----------------- API SETUP -----------------
api_key = ""
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
elif "GEMINI_API_KEY" in os.environ:
    api_key = os.environ["GEMINI_API_KEY"]

client = genai.Client(api_key=api_key) if api_key else None

SYSTEM_INSTRUCTION = """
You are Zeno, a hyper-intelligent, polite, and futuristic AI assistant.
Keep spoken replies brief, crisp, and conversational (1 to 3 short sentences).
Do not use markdown symbols like asterisks (*) or hashes (#) so the speech engine reads it cleanly.
"""

# ----------------- SCREEN 1: DEMO / SPLASH SCREEN -----------------
if not st.session_state.app_launched:
    st.markdown("""
    <div class="intro-card">
        <div class="status-badge">SYSTEMS ONLINE • V3.2</div>
        <div class="zeno-brand">⚡ ZENO AI ⚡</div>
        <p style="color: #80deea; font-size: 1.1rem; margin-bottom: 20px;">
            Next-Gen Multimodal Voice & Cognitive Interface
        </p>
        <div class="orb-wrapper">
            <div class="core-orb"></div>
        </div>
        <p style="color: #90caf9; font-size: 0.95rem; margin-top: 15px;">
            Supports Voice Interaction, Multimodal Vision, Document Auditing & Realtime Synthesis.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        if st.button("🚀 INITIALIZE & LAUNCH ZENO", use_container_width=True):
            st.session_state.app_launched = True
            st.rerun()

# ----------------- SCREEN 2: MAIN DASHBOARD -----------------
else:
    # Top Header
    st.markdown('<div class="zeno-brand" style="text-align: center; font-size: 2rem;">⚡ ZENO AI CORE ⚡</div>', unsafe_allow_html=True)
    st.markdown('<div class="orb-wrapper"><div class="core-orb" style="width: 70px; height: 70px;"></div></div>', unsafe_allow_html=True)

    # ----------------- SIDEBAR CONTROLS & UPLOADS -----------------
    with st.sidebar:
        st.markdown("### 🎛️ Neural Controls")
        
        if st.button("🔄 Reset / Standby Mode", use_container_width=True):
            st.session_state.app_launched = False
            st.rerun()

        st.markdown("---")
        st.markdown("### 📂 Multimodal Inputs")
        
        # 1. Image Upload
        uploaded_image = st.file_uploader("🖼️ Upload Image (Vision)", type=["jpg", "jpeg", "png"])
        if uploaded_image:
            img = Image.open(uploaded_image)
            st.image(img, caption="Loaded into Buffer", use_container_width=True)

        # 2. PDF Upload
        uploaded_pdf = st.file_uploader("📄 Upload PDF (Document Analysis)", type=["pdf"])
        pdf_extracted_text = ""
        if uploaded_pdf:
            reader = PdfReader(uploaded_pdf)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pdf_extracted_text += text
            st.success(f"PDF Parsed: {len(reader.pages)} pages")

        # 3. Audio File Upload
        uploaded_audio = st.file_uploader("🎵 Upload Audio", type=["mp3", "wav", "ogg"])
        if uploaded_audio:
            st.audio(uploaded_audio)

    # ----------------- TOUCH TO SPEAK MIC -----------------
    st.components.v1.html("""
    <div style="text-align: center; margin-bottom: 12px;">
        <button id="micBtn" style="
            background: linear-gradient(45deg, #00f2fe, #4facfe);
            border: none;
            color: #030816;
            padding: 12px 28px;
            border-radius: 25px;
            font-weight: bold;
            font-size: 15px;
            cursor: pointer;
            box-shadow: 0 0 20px rgba(0, 242, 254, 0.4);
            letter-spacing: 1px;
        ">🎙️ Touch to Speak</button>
        <div id="status" style="color: #80deea; font-size: 13px; margin-top: 8px;">Tap button to command Zeno</div>
    </div>

    <script>
        const micBtn = document.getElementById('micBtn');
        const status = document.getElementById('status');
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (SpeechRecognition) {
            const recognition = new SpeechRecognition();
            recognition.lang = 'en-US';
            recognition.interimResults = false;

            micBtn.onclick = () => {
                try {
                    recognition.start();
                    status.innerText = "Listening... Speak now";
                    micBtn.style.background = "#ff3366";
                } catch(e) {
                    recognition.stop();
                }
            };

            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                status.innerText = "Heard: " + transcript;
                micBtn.style.background = "linear-gradient(45deg, #00f2fe, #4facfe)";

                const lower = transcript.toLowerCase();
                if (lower.startsWith("play ")) {
                    const query = transcript.replace(/play/i, '').trim();
                    window.open("https://www.youtube.com/results?search_query=" + encodeURI(query), "_blank");
                } else if (lower.includes("open youtube")) {
                    window.open("https://www.youtube.com", "_blank");
                } else if (lower.includes("open google")) {
                    window.open("https://www.google.com", "_blank");
                }

                const inputField = window.parent.document.querySelector('textarea[aria-label="Ask Zeno anything..."]');
                if (inputField) {
                    inputField.value = transcript;
                    inputField.dispatchEvent(new Event('input', { bubbles: true }));
                    const submitBtn = window.parent.document.querySelector('button[kind="secondaryFormSubmit"], button[data-testid="stBaseButton-secondary"]');
                    if (submitBtn) submitBtn.click();
                }
            };

            recognition.onerror = () => {
                status.innerText = "Mic Error. Tap to try again.";
                micBtn.style.background = "linear-gradient(45deg, #00f2fe, #4facfe)";
            };

            recognition.onend = () => {
                micBtn.style.background = "linear-gradient(45deg, #00f2fe, #4facfe)";
            };
        } else {
            status.innerText = "Speech API supported best on Google Chrome.";
        }
    </script>
    """, height=85)

    # ----------------- CHAT HISTORY -----------------
    for msg in st.session_state.messages:
        avatar = "🔮" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # ----------------- CHAT INPUT & EXECUTION -----------------
    user_prompt = st.chat_input("Ask Zeno anything...")

    if user_prompt:
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_prompt)

        with st.chat_message("assistant", avatar="🔮"):
            if not client:
                st.error("API Key configure aagilla. Streamlit Secrets nalli GEMINI_API_KEY add maadi.")
            else:
                try:
                    payload = []
                    
                    # Context from PDF
                    if pdf_extracted_text:
                        payload.append(f"Context from attached PDF document:\n{pdf_extracted_text[:4000]}\n")
                    
                    # Context from Image
                    if uploaded_image:
                        payload.append(Image.open(uploaded_image))

                    payload.append(user_prompt)

                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=payload,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_INSTRUCTION,
                            temperature=0.6,
                        )
                    )

                    clean_reply = response.text.replace("*", "").replace("#", "").replace('"', '').replace("'", "").strip()
                    st.markdown(clean_reply)
                    st.session_state.messages.append({"role": "assistant", "content": clean_reply})

                    # Natural Voice Speech Output
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

                except Exception as e:
                    st.error(f"Error: {str(e)}")
