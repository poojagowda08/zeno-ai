import streamlit as st
import streamlit.components.v1 as components
from google import genai
from google.genai import errors
import webbrowser
import urllib.parse

# ----------------- PAGE CONFIG -----------------
st.set_page_config(page_title="ZENO AI", page_icon="⚡", layout="centered")

# ----------------- STYLING (Dark Theme UI) -----------------
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: white; }
    .title-box { text-align: center; padding: 10px 0; }
    .title { color: #58a6ff; font-weight: 800; font-size: 26px; }
    .subtitle { color: #8b949e; font-size: 14px; margin-top: -5px; }
    .chat-bubble {
        padding: 12px 16px;
        border-radius: 12px;
        margin-bottom: 12px;
        font-size: 15px;
        line-height: 1.5;
    }
    .user-bubble {
        background-color: #21262d;
        border-left: 4px solid #58a6ff;
        color: #e6edf3;
    }
    .bot-bubble {
        background-color: #161b22;
        border-left: 4px solid #a371f7;
        color: #f0f6fc;
    }
    .lock-box {
        background: #1c2128;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #30363d;
        text-align: center;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------- APP STATE & APP LOCK -----------------
# ಡಿಫಾಲ್ಟ್ ಸೆಕ್ಯುರಿಟಿ ಪಿನ್ (Security PIN)
DEFAULT_PIN = "1234"

if "is_locked" not in st.session_state:
    st.session_state.is_locked = False

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "latest_reply_to_speak" not in st.session_state:
    st.session_state.latest_reply_to_speak = ""

# ----------------- GEMINI CLIENT -----------------
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    st.error("⚠️ Streamlit Secrets ನಲ್ಲಿ GEMINI_API_KEY ಸೆಟ್ ಮಾಡಿಲ್ಲ!")
    st.stop()

client = genai.Client(api_key=api_key)

# ----------------- LOCK SCREEN (App Lock Requirement) -----------------
if st.session_state.is_locked:
    st.markdown("<div class='title-box'><h2 class='title'>🔒 ZENO AI IS LOCKED</h2></div>", unsafe_allow_html=True)
    st.markdown("<div class='lock-box'>ದಯವಿಟ್ಟು ಅನ್‌ಲಾಕ್ ಮಾಡಲು PIN ನಮೂದಿಸಿ (Default PIN: 1234)</div>", unsafe_allow_html=True)
    
    pin_input = st.text_input("Enter PIN:", type="password")
    if st.button("Unlock 🔓"):
        if pin_input == DEFAULT_PIN:
            st.session_state.is_locked = False
            st.success("ಅನ್‌ಲಾಕ್ ಆಗಿದೆ!")
            st.rerun()
        else:
            st.error("ತಪ್ಪು PIN! ದಯವಿಟ್ಟು ಸರಿಯಾದ PIN ಹಾಕಿ.")
    st.stop()

# ----------------- MAIN UI -----------------
st.markdown("""
    <div class='title-box'>
        <div class='title'>⚡ ZENO AI ⚡</div>
        <div class='subtitle'>Voice Assistant & Smart Task Automation</div>
    </div>
""", unsafe_allow_html=True)

# ----------------- VOICE & COMMAND PROCESSOR -----------------
def process_command_or_chat(prompt: str):
    text = prompt.lower().strip()
    
    # 1. Lock command
    if "lock" in text and ("app" in text or "zeno" in text or text == "lock"):
        st.session_state.is_locked = True
        return "Zeno AI ಅನ್ನು ಲಾಕ್ ಮಾಡಲಾಗಿದೆ. ಅನ್‌ಲಾಕ್ ಮಾಡಲು PIN ಅಗತ್ಯವಿದೆ."
    
    # 2. Play song / YouTube command
    elif text.startswith("play ") or "play song" in text:
        song_name = text.replace("play song", "").replace("play", "").strip()
        query = urllib.parse.quote(song_name)
        yt_url = f"https://www.youtube.com/results?search_query={query}"
        return f"ಯೂಟ್ಯೂಬ್‌ನಲ್ಲಿ ಪ್ಲೇ ಮಾಡಲಾಗುತ್ತಿದೆ: **{song_name}** 🎵\n\n👉 [ಇಲ್ಲಿ ಕ್ಲಿಕ್ ಮಾಡಿ ಹಾಡು ಕೇಳಿ]({yt_url})"
        
    # 3. Open applications / websites
    elif "open google" in text:
        return "ಗೂಗಲ್ ಓಪನ್ ಮಾಡಲಾಗುತ್ತಿದೆ: 👉 [Google.com](https://www.google.com)"
    elif "open youtube" in text:
        return "ಯೂಟ್ಯೂಬ್ ಓಪನ್ ಮಾಡಲಾಗುತ್ತಿದೆ: 👉 [YouTube.com](https://www.youtube.com)"
    elif "open spotify" in text:
        return "ಸ್ಪಾಟಿಫೈ ಓಪನ್ ಮಾಡಲಾಗುತ್ತಿದೆ: 👉 [Spotify.com](https://open.spotify.com)"
    elif "open instagram" in text:
        return "ಇನ್‌ಸ್ಟಾಗ್ರಾಮ್ ಓಪನ್ ಮಾಡಲಾಗುತ್ತಿದೆ: 👉 [Instagram.com](https://www.instagram.com)"
    elif "open github" in text:
        return "ಗಿಟ್‌ಹಬ್ ಓಪನ್ ಮಾಡಲಾಗುತ್ತಿದೆ: 👉 [GitHub.com](https://github.com)"
        
    # 4. Search Google command
    elif text.startswith("search ") or text.startswith("google "):
        search_query = text.replace("search", "").replace("google", "").strip()
        query = urllib.parse.quote(search_query)
        search_url = f"https://www.google.com/search?q={query}"
        return f"ಗೂಗಲ್‌ನಲ್ಲಿ ಹುಡುಕಲಾಗುತ್ತಿದೆ: **{search_query}** 🔍\n\n👉 [ರಿಸಲ್ಟ್ ನೋಡಲು ಇಲ್ಲಿ ಕ್ಲಿಕ್ ಮಾಡಿ]({search_url})"
        
    # 5. Gemini AI Chat (General Queries)
    else:
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return response.text
        except errors.APIError as e:
            return f"API ತಾತ್ಕಾಲಿಕವಾಗಿ ಲಭ್ಯವಿಲ್ಲ: {e}"
        except Exception as e:
            return f"ದೋಷ ಸಂಭವಿಸಿದೆ: {e}"

# ----------------- WORKING HTML/JS MIC & TTS COMPONENT -----------------
# ಬ್ರೌಸರ್ ಮೈಕ್ + ಆಟೋಮ್ಯಾಟಿಕ್ ವಾಯ್ಸ್ ಸ್ಪೀಕ್ (TTS)
voice_js_component = f"""
<div style="text-align: center; margin: 15px 0;">
    <div style="
        width: 65px; height: 65px; 
        background: radial-gradient(circle, #00f0ff 0%, #7000ff 70%); 
        border-radius: 50%; 
        margin: 0 auto 12px auto;
        box-shadow: 0 0 25px rgba(0, 240, 255, 0.6);
        animation: pulse 2s infinite alternate;">
    </div>

    <button id="mic-btn" style="
        background: linear-gradient(135deg, #00d2ff, #3a7bd5);
        color: white;
        border: none;
        padding: 12px 30px;
        font-size: 16px;
        font-weight: 700;
        border-radius: 30px;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(0,210,255,0.4);
        transition: transform 0.2s;
    ">🎙️ Touch to Speak</button>
    
    <p id="mic-status" style="color: #8b949e; font-size: 13px; margin-top: 8px;">Tap to speak or type below</p>
</div>

<script>
const btn = document.getElementById('mic-btn');
const status = document.getElementById('mic-status');
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (!SpeechRecognition) {{
    status.innerText = "Speech Recognition support ಇಲ್ಲ. ದಯವಿಟ್ಟು Chrome ಬಳಸಿ.";
}} else {{
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-IN'; // English (India) - supports Kannada accent well
    recognition.interimResults = false;

    btn.onclick = () => {{
        try {{
            recognition.start();
            status.innerText = "Listening... ಈಗ ಮಾತನಾಡಿ";
            btn.style.background = "#e63946";
        }} catch(e) {{
            recognition.stop();
        }}
    }};

    recognition.onresult = (event) => {{
        const spokenText = event.results[0][0].transcript;
        status.innerText = "ಕೇಳಿಸಿಕೊಂಡಿದ್ದು: " + spokenText;
        btn.style.background = "linear-gradient(135deg, #00d2ff, #3a7bd5)";
        
        // Find Streamlit input and inject spoken text
        const inputs = window.parent.document.querySelectorAll('input[type="text"]');
        if (inputs.length > 0) {{
            const targetInput = inputs[0];
            targetInput.value = spokenText;
            targetInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
            targetInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
            
            // Auto submit form
            const form = targetInput.closest('form');
            if (form) {{
                const submitBtn = form.querySelector('button[kind="secondaryFormSubmit"]') || form.querySelector('button');
                if (submitBtn) submitBtn.click();
            }}
        }}
    }};

    recognition.onerror = (event) => {{
        status.innerText = "Mic Error: " + event.error;
        btn.style.background = "linear-gradient(135deg, #00d2ff, #3a7bd5)";
    }};

    recognition.onend = () => {{
        btn.style.background = "linear-gradient(135deg, #00d2ff, #3a7bd5)";
    }};
}}

// Text-to-Speech (Zeno ಮಾತನಾಡುವುದು)
function speakText(text) {{
    if ('speechSynthesis' in window && text) {{
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;
        window.speechSynthesis.speak(utterance);
    }}
}}
</script>
"""

components.html(voice_js_component, height=170)

# ----------------- CHAT HISTORY DISPLAY -----------------
for chat in st.session_state.chat_history:
    bubble_class = "user-bubble" if chat["role"] == "user" else "bot-bubble"
    icon = "👤 You:" if chat["role"] == "user" else "🔮 Zeno:"
    st.markdown(f"<div class='chat-bubble {bubble_class}'><b>{icon}</b><br>{chat['content']}</div>", unsafe_allow_html=True)

# ----------------- USER INPUT FORM -----------------
with st.form("user_input_form", clear_on_submit=True):
    user_query = st.text_input("Ask Zeno anything...", placeholder="Type or click 'Touch to Speak'...")
    send_clicked = st.form_submit_button("Send ⬆️")

if send_clicked and user_query.strip():
    # User message ಸೇರಿಸಿ
    st.session_state.chat_history.append({"role": "user", "content": user_query})
    
    with st.spinner("Zeno is processing..."):
        response = process_command_or_chat(user_query)
        
    # Bot reply ಸೇರಿಸಿ
    st.session_state.chat_history.append({"role": "bot", "content": response})
    st.rerun()
