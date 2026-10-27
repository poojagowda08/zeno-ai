import streamlit as st
import datetime
from google import genai
from google.genai import types

# ----------------- PAGE CONFIG -----------------
st.set_page_config(
    page_title="ZENO AI",
    page_icon="🔮",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Clean Cyberpunk Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;900&family=Rajdhani:wght@600&display=swap');
    
    .stApp {
        background: radial-gradient(circle at 50% 20%, #0c1024 0%, #05070e 100%);
        color: #e0f7fa;
        font-family: 'Rajdhani', sans-serif;
    }
    
    .zeno-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 2.1rem;
        font-weight: 900;
        text-align: center;
        background: linear-gradient(90deg, #00f2fe 0%, #4facfe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: 2px;
        margin-bottom: 2px;
    }
    
    .zeno-subtitle {
        text-align: center;
        font-size: 0.9rem;
        color: #80deea;
        margin-bottom: 20px;
    }
    
    .orb-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 15px 0;
    }
    
    .orb {
        width: 85px;
        height: 85px;
        border-radius: 50%;
        background: radial-gradient(circle, #00f2fe 20%, #7f00ff 80%);
        box-shadow: 0 0 25px #00f2fe, 0 0 50px #7f00ff;
        animation: pulse 2s infinite alternate;
    }
    
    @keyframes pulse {
        0% { transform: scale(0.95); box-shadow: 0 0 15px #00f2fe; }
        100% { transform: scale(1.05); box-shadow: 0 0 35px #00f2fe, 0 0 60px #7f00ff; }
    }
</style>
""", unsafe_allow_html=True)

# ----------------- GEMINI CLIENT -----------------
api_key = st.secrets.get("GEMINI_API_KEY", "")
client = genai.Client(api_key=api_key)

SYSTEM_INSTRUCTION = """
You are Zeno, a friendly and ultra-smart AI assistant.
Keep spoken replies brief, clean, and conversational (1 to 3 short sentences).
Never use markdown symbols like asterisks (*) or hashes (#) in your response, so the speech engine reads it completely cleanly.
"""

# ----------------- SESSION -----------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am Zeno. How can I help you today?"}
    ]

# ----------------- HEADER -----------------
st.markdown('<div class="zeno-title">⚡ ZENO AI ⚡</div>', unsafe_allow_html=True)
st.markdown('<div class="zeno-subtitle">Voice Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="orb-container"><div class="orb"></div></div>', unsafe_allow_html=True)

# ----------------- SPEECH RECOGNITION (MIC) -----------------
st.components.v1.html("""
<div style="text-align: center; margin-bottom: 10px;">
    <button id="micBtn" style="
        background: linear-gradient(45deg, #00f2fe, #4facfe);
        border: none;
        color: #030816;
        padding: 10px 22px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 14px;
        cursor: pointer;
        box-shadow: 0 0 15px rgba(0, 242, 254, 0.4);
    ">🎙️ Touch to Speak</button>
    <div id="status" style="color: #80deea; font-size: 12px; margin-top: 6px;">Tap to speak</div>
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

        recognition.onerror = (e) => {
            status.innerText = "Mic Error: Please tap again";
            micBtn.style.background = "linear-gradient(45deg, #00f2fe, #4facfe)";
        };

        recognition.onend = () => {
            micBtn.style.background = "linear-gradient(45deg, #00f2fe, #4facfe)";
        };
    } else {
        status.innerText = "Use Google Chrome for Voice Input.";
    }
</script>
""", height=70)

# ----------------- DISPLAY CHAT -----------------
for msg in st.session_state.messages:
    avatar = "🔮" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# ----------------- CHAT INPUT -----------------
user_input = st.chat_input("Ask Zeno anything...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="🔮"):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_input,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.6,
                )
            )
            clean_reply = response.text.replace("*", "").replace("#", "").replace('"', '').replace("'", "").strip()
            
            st.markdown(clean_reply)
            st.session_state.messages.append({"role": "assistant", "content": clean_reply})

            # Voice Output
            tts_script = f"""
            <script>
                if ('speechSynthesis' in window) {{
                    window.speechSynthesis.cancel();
                    
                    const speakNow = () => {{
                        const voices = window.speechSynthesis.getVoices();
                        const utterance = new SpeechSynthesisUtterance("{clean_reply[:250]}");
                        
                        const naturalVoice = voices.find(v => (v.name.includes('Google') || v.name.includes('Natural') || v.name.includes('Female')) && v.lang.startsWith('en')) || voices.find(v => v.lang.startsWith('en'));
                        
                        if (naturalVoice) {{
                            utterance.voice = naturalVoice;
                        }}
                        
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
