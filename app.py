import os
import webbrowser
import streamlit as st
import streamlit.components.v1 as components
from pypdf import PdfReader
from google import genai

# API Key handling: Works both locally and on Streamlit Cloud
api_key = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6I6VHkhukOgzUVTRi54mxXkfjSM-i_Y_0BZwoLUGzsNYA")

st.set_page_config(
    page_title="Zeno AI | Mobile & Web Voice Assistant",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"  # Mobile screen nalli automatically fit aguthe
)

# Mobile-Optimized Sci-Fi Dark UI
st.markdown("""
<style>
    .main {
        background: radial-gradient(circle at 50% 20%, #1e1b4b 0%, #090d16 100%);
        color: #f8fafc;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .zeno-card {
        background: rgba(15, 23, 42, 0.85);
        backdrop-filter: blur(16px);
        padding: 16px 20px;
        border-radius: 18px;
        border: 1.5px solid rgba(56, 189, 248, 0.35);
        box-shadow: 0 0 20px rgba(56, 189, 248, 0.2);
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 15px;
    }
    .zeno-title {
        font-size: 26px;
        font-weight: 900;
        letter-spacing: 1.5px;
        background: linear-gradient(90deg, #38bdf8, #a855f7, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    .zeno-subtitle {
        color: #94a3b8;
        font-size: 12px;
        margin-top: 2px;
    }
    .ai-wave-box {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        height: 22px;
    }
    .ai-bar {
        width: 3px;
        background: #38bdf8;
        border-radius: 3px;
        animation: soundBars 1.2s ease-in-out infinite alternate;
    }
    .ai-bar:nth-child(2) { height: 16px; animation-delay: 0.2s; background: #818cf8; }
    .ai-bar:nth-child(3) { height: 22px; animation-delay: 0.4s; background: #c084fc; }
    .ai-bar:nth-child(4) { height: 12px; animation-delay: 0.1s; background: #ec4899; }
    .ai-bar:nth-child(5) { height: 18px; animation-delay: 0.3s; background: #38bdf8; }
    @keyframes soundBars {
        0% { transform: scaleY(0.4); }
        100% { transform: scaleY(1.3); }
    }
    div[data-testid="stChatInput"] {
        border-radius: 25px !important;
        border: 1.5px solid rgba(56, 189, 248, 0.4) !important;
        background: rgba(15, 23, 42, 0.95) !important;
    }
    div[data-testid="stChatInput"] button {
        background: linear-gradient(135deg, #0284c7, #9333ea) !important;
        border-radius: 50% !important;
        color: white !important;
    }
</style>

<div class="zeno-card">
    <div>
        <h1 class="zeno-title">⚡ ZENO AI</h1>
        <p class="zeno-subtitle">Ultra-Fast Voice & Study Partner</p>
    </div>
    <div class="ai-wave-box">
        <div class="ai-bar" style="height: 10px;"></div>
        <div class="ai-bar"></div>
        <div class="ai-bar"></div>
        <div class="ai-bar"></div>
        <div class="ai-bar" style="height: 8px;"></div>
    </div>
</div>
""", unsafe_allow_html=True)

# Instant 0-Lag Audio Output
def speak_instant(text_to_speak):
    safe_text = text_to_speak.replace("'", " ").replace('"', ' ').replace('\n', ' ')
    html_code = f"""
    <script>
        window.speechSynthesis.cancel();
        var msg = new SpeechSynthesisUtterance("{safe_text[:250]}");
        msg.rate = 1.05;
        window.speechSynthesis.speak(msg);
    </script>
    """
    components.html(html_code, height=0, width=0)

# Touch-Friendly Pulse Mic
def render_pulse_mic():
    html_code = """
    <div style="display: flex; align-items: center; gap: 15px; margin: 10px 0 15px 0;">
              <button id="zenoOrb" style="
            background: radial-gradient(circle at 50% 30%, #38bdf8 0%, #a855f7 50%, #090d16 100%);
            border: 2px solid #38bdf8;
            color: white;
            width: 55px;
            height: 55px;
            border-radius: 50%;
            cursor: pointer;
            box-shadow: 0 0 20px rgba(56, 189, 248, 0.6);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            -webkit-tap-highlight-color: transparent;
        ">
            <span id="micOrb">🎤</span>
        </button>
        <div>
            <div id="micLabel" style="color: #38bdf8; font-weight: 800; font-size: 14px;">TAP TO SPEAK</div>
            <div id="micStatus" style="color: #94a3b8; font-size: 12px;">Touch orb to speak commands</div>
        </div>
    </div>

    <script>
        const btn = document.getElementById('zenoOrb');
        const icon = document.getElementById('micOrb');
        const label = document.getElementById('micLabel');
        const status = document.getElementById('micStatus');

        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRec) {
            status.innerText = "Please use Chrome / Webview for voice.";
        } else {
            const rec = new SpeechRec();
            rec.continuous = false;
            rec.interimResults = false;
            rec.lang = 'en-US';

            btn.onclick = () => {
                try {
                    rec.start();
                    btn.style.boxShadow = "0 0 25px rgba(239, 68, 68, 0.8)";
                    icon.innerText = "🔴";
                    label.innerText = "LISTENING...";
                    status.innerText = "Listening to you...";
                } catch(e) {
                    rec.stop();
                }
            };

            rec.onresult = (e) => {
                const speech = e.results[0][0].transcript;
                status.innerText = 'Analyzing: "' + speech + '"';
                label.innerText = "PROCESSING...";
                icon.innerText = "⚡";
                btn.style.boxShadow = "0 0 20px rgba(56, 189, 248, 0.6)";

                const currentUrl = new URL(window.parent.location.href);
                currentUrl.searchParams.set("voice_prompt", speech);
                window.parent.location.href = currentUrl.toString();
            };

            rec.onerror = () => {
                icon.innerText = "🎤";
                label.innerText = "TAP TO SPEAK";
                status.innerText = "Mic timeout. Try again.";
            };

            rec.onend = () => {
                icon.innerText = "🎤";
                label.innerText = "TAP TO SPEAK";
            };
        }
    </script>
    """
    components.html(html_code, height=75)

def extract_text(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages[:10]:
        content = page.extract_text()
        if content:
            text += content + "\n"
    return text

if "notes_text" not in st.session_state:
    st.session_state.notes_text = ""
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar Hub (Document Vault)
st.sidebar.markdown("<h3 style='color: #38bdf8;'>⚡ Zeno Memory Core</h3>", unsafe_allow_html=True)
uploaded_file = st.sidebar.file_uploader("Upload Notes (PDF)", type=["pdf"])

if uploaded_file:
    st.sidebar.info(f"📄 {uploaded_file.name}")
    if st.sidebar.button("🚀 Load Context"):
        with st.spinner("Loading document..."):
            extracted = extract_text(uploaded_file)
            st.session_state.notes_text = extracted
            st.sidebar.success("✨ Context Loaded!")

st.sidebar.markdown("---")
if st.sidebar.button("🧹 Flash Memory"):
    st.session_state.messages = []
    st.rerun()

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Render Pulse Mic
render_pulse_mic()
# Voice parameter bridge check
voice_input_query = None
if "voice_prompt" in st.query_params:
    voice_input_query = st.query_params.get("voice_prompt")
    st.query_params.clear()

# Text Input
typed_query = st.chat_input("Ask anything or say 'open youtube'...")

user_query = voice_input_query if voice_input_query else typed_query

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    query_lower = user_query.lower().strip()

    # Browser Automation Commands
    if query_lower.startswith("open "):
        target = query_lower.replace("open ", "").strip().replace(" ", "")
        known_sites = {
            "google": "https://www.google.com",
            "youtube": "https://www.youtube.com",
            "whatsapp": "https://web.whatsapp.com",
            "github": "https://www.github.com",
            "chatgpt": "https://chatgpt.com",
            "instagram": "https://www.instagram.com"
        }
        url = known_sites.get(target, f"https://www.{target}.com")
        webbrowser.open(url)
        ans_text = f"Opening {target.capitalize()} right now."

        with st.chat_message("assistant"):
            st.markdown(f"⚡ {ans_text}")
            speak_instant(ans_text)
            st.session_state.messages.append({"role": "assistant", "content": ans_text})
        st.stop()

    if not api_key or "YOUR_GEMINI" in api_key:
        st.error("⚠️ Insert your valid Gemini API Key in line 10 of app.py.")
        st.stop()

    with st.chat_message("assistant"):
        with st.spinner("Answering..."):
            doc_context = st.session_state.notes_text[:2000] if st.session_state.notes_text else ""
            prompt = f"Answer crisply in 2-3 points. Context: {doc_context}\nQuestion: {user_query}"

            client = genai.Client(api_key=api_key)
            response = None
            last_err = ""

            for m in ["gemini-3.5-flash-lite", "gemini-3.8-flash"]:
                try:
                    response = client.models.generate_content(
                        model=m,
                        contents=prompt
                    )
                    if response and response.text:
                        break
                except Exception as e:
                    last_err = str(e)
                    continue

            if response and response.text:
                answer = response.text
                st.markdown(answer)

                clean_speech = answer.replace("*", " ").replace("#", " ").replace("\n", " ").strip()
                speak_instant(clean_speech)

                st.session_state.messages.append({"role": "assistant", "content": answer})
            else:
                st.error(f"Error: {last_err}")