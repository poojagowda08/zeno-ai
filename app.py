import streamlit as st
import streamlit.components.v1 as components
from google import genai
from google.genai import errors
import urllib.parse

# 1. Page Configuration
st.set_page_config(page_title="ZENO AI", page_icon="⚡", layout="centered")

# 2. Dark Theme Styling
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #ffffff; }
    .title-box { text-align: center; padding: 10px 0; }
    .title { color: #58a6ff; font-weight: 800; font-size: 28px; }
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
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #30363d;
        text-align: center;
        margin-top: 30px;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Session State & App Lock Variables
DEFAULT_PIN = "1234"

if "is_locked" not in st.session_state:
    st.session_state.is_locked = False

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 4. Gemini API Client Setup
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    st.error("⚠️ Streamlit Secrets ನಲ್ಲಿ GEMINI_API_KEY ಸೆಟ್ ಮಾಡಿಲ್ಲ!")
    st.stop()

client = genai.Client(api_key=api_key)

# 5. Lock Screen Check
if st.session_state.is_locked:
    st.markdown("<div class='title-box'><h2 class='title'>🔒 ZENO AI IS LOCKED</h2></div>", unsafe_allow_html=True)
    st.markdown("<div class='lock-box'>ಅನ್‌ಲಾಕ್ ಮಾಡಲು PIN ನಮೂದಿಸಿ (Default PIN: <b>1234</b>)</div>", unsafe_allow_html=True)
    
    pin_input = st.text_input("PIN:", type="password", key="unlock_pin")
    if st.button("Unlock 🔓"):
        if pin_input == DEFAULT_PIN:
            st.session_state.is_locked = False
            st.success("Unlocked successfully!")
            st.rerun()
        else:
            st.error("ತಪ್ಪು PIN! ದಯವಿಟ್ಟು 1234 ನಮೂದಿಸಿ.")
    st.stop()

# 6. Main UI Header
st.markdown("""
    <div class='title-box'>
        <div class='title'>⚡ ZENO AI ⚡</div>
        <div class='subtitle'>Smart Voice & AI Assistant</div>
    </div>
""", unsafe_allow_html=True)

# 7. Command & AI Handler Function
def process_message(prompt: str):
    text = prompt.lower().strip()
    
    # Feature 1: Lock command
    if text == "lock" or "lock app" in text or "lock zeno" in text:
        st.session_state.is_locked = True
        return "🔒 Zeno AI ಅನ್ನು ಲಾಕ್ ಮಾಡಲಾಗಿದೆ. ಅನ್‌ಲಾಕ್ ಮಾಡಲು PIN ಹಾಕಿ."
    
    # Feature 2: Play Song (YouTube)
    elif text.startswith("play ") or "play song" in text:
        song_name = text.replace("play song", "").replace("play", "").strip()
        query = urllib.parse.quote(song_name)
        yt_url = f"https://www.youtube.com/results?search_query={query}"
        return f"🎵 ಪ್ಲೇ ಮಾಡಲಾಗುತ್ತಿದೆ: **{song_name}**\n\n👉 [ಹಾಡು ಕೇಳಲು ಇಲ್ಲಿ ಕ್ಲಿಕ್ ಮಾಡಿ]({yt_url})"
        
    # Feature 3: Open Apps / Websites
    elif "open google" in text:
        return "👉 [Google ತೆರೆಯಲು ಇಲ್ಲಿ ಕ್ಲಿಕ್ ಮಾಡಿ](https://www.google.com)"
    elif "open youtube" in text:
        return "👉 [YouTube ತೆರೆಯಲು ಇಲ್ಲಿ ಕ್ಲಿಕ್ ಮಾಡಿ](https://www.youtube.com)"
    elif "open spotify" in text:
        return "👉 [Spotify ತೆರೆಯಲು ಇಲ್ಲಿ ಕ್ಲಿಕ್ ಮಾಡಿ](https://open.spotify.com)"
    elif "open instagram" in text:
        return "👉 [Instagram ತೆರೆಯಲು ಇಲ್ಲಿ ಕ್ಲಿಕ್ ಮಾಡಿ](https://www.instagram.com)"
    elif "open github" in text:
        return "👉 [GitHub ತೆರೆಯಲು ಇಲ್ಲಿ ಕ್ಲಿಕ್ ಮಾಡಿ](https://github.com)"
        
    # Feature 4: Google Search
    elif text.startswith("search ") or text.startswith("google "):
        search_query = text.replace("search", "").replace("google", "").strip()
        query = urllib.parse.quote(search_query)
        search_url = f"https://www.google.com/search?q={query}"
        return f"🔍 ಗೂಗಲ್‌ನಲ್ಲಿ ಹುಡುಕಲಾಗುತ್ತಿದೆ: **{search_query}**\n\n👉 [ರಿಸಲ್ಟ್ ನೋಡಲು ಇಲ್ಲಿ ಕ್ಲಿಕ್ ಮಾಡಿ]({search_url})"
        
    # Feature 5: Gemini AI Response (Fixed to gemini-1.5-flash)
    else:
        try:
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt
            )
            return response.text
        except errors.APIError as e:
            return f"API Error: {e}"
        except Exception as e:
            return f"Error: {e}"

# 8. Web Speech Microphone Component (Pure JavaScript)
mic_component = """
<div style="text-align: center; margin: 15px 0;">
    <div style="
        width: 60px; height: 60px; 
        background: radial-gradient(circle, #00f0ff 0%, #7000ff 70%); 
        border-radius: 50%; 
        margin: 0 auto 10px auto;
        box-shadow: 0 0 20px rgba(0, 240, 255, 0.6);">
    </div>

    <button id="mic-btn" style="
        background: linear-gradient(135deg, #00d2ff, #3a7bd5);
        color: white;
        border: none;
        padding: 10px 24px;
        font-size: 15px;
        font-weight: 700;
        border-radius: 25px;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(0,210,255,0.4);
    ">🎙️ Touch to Speak</button>
    
    <p id="mic-status" style="color: #8b949e; font-size: 13px; margin-top: 6px;">Tap to speak</p>
</div>

<script>
const btn = document.getElementById('mic-btn');
const status = document.getElementById('mic-status');
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (!SpeechRecognition) {
    status.innerText = "Speech Recognition not supported. Please use Chrome.";
} else {
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-IN';
    recognition.interimResults = false;

    btn.onclick = () => {
        try {
            recognition.start();
            status.innerText = "Listening... Speak now";
            btn.style.background = "#e63946";
        } catch(e) {
            recognition.stop();
        }
    };

    recognition.onresult = (event) => {
        const spokenText = event.results[0][0].transcript;
        status.innerText = "Heard: " + spokenText;
        btn.style.background = "linear-gradient(135deg, #00d2ff, #3a7bd5)";
        
        // Put text into Streamlit input box and trigger Send
        const inputs = window.parent.document.querySelectorAll('input[type="text"]');
        if (inputs.length > 0) {
            const targetInput = inputs[0];
            targetInput.value = spokenText;
            targetInput.dispatchEvent(new Event('input', { bubbles: true }));
            targetInput.dispatchEvent(new Event('change', { bubbles: true }));
            
            setTimeout(() => {
                const forms = window.parent.document.querySelectorAll('form');
                if (forms.length > 0) {
                    const submitBtn = forms[0].querySelector('button');
                    if (submitBtn) submitBtn.click();
                }
            }, 300);
        }
    };

    recognition.onerror = (event) => {
        status.innerText = "Mic Error: " + event.error;
        btn.style.background = "linear-gradient(135deg, #00d2ff, #3a7bd5)";
    };

    recognition.onend = () => {
        btn.style.background = "linear-gradient(135deg, #00d2ff, #3a7bd5)";
    };
}
</script>
"""

components.html(mic_component, height=140)

# 9. Display Chat Messages
for chat in st.session_state.chat_history:
    bubble_class = "user-bubble" if chat["role"] == "user" else "bot-bubble"
    sender = "👤 You:" if chat["role"] == "user" else "🔮 Zeno:"
    st.markdown(f"<div class='chat-bubble {bubble_class}'><b>{sender}</b><br>{chat['content']}</div>", unsafe_allow_html=True)

# 10. User Text Input Form
with st.form("chat_input_form", clear_on_submit=True):
    user_query = st.text_input("Ask Zeno anything...", placeholder="Type here or use Touch to Speak...")
    submitted = st.form_submit_button("Send ⬆️")

if submitted and user_query.strip():
    st.session_state.chat_history.append({"role": "user", "content": user_query})
    
    with st.spinner("Zeno is thinking..."):
        reply = process_message(user_query)
        
    st.session_state.chat_history.append({"role": "bot", "content": reply})
    st.rerun()
