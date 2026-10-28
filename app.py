import streamlit as st
import os
import json
import urllib.request
import urllib.error
from PIL import Image
#
=====================================================

ZENO AI - FUTURISTIC VOICE ASSISTANT

=====================================================

st.set_page_config(
page_title="ZENO AI | Futuristic Core",
page_icon="🔮",
layout="wide",
initial_sidebar_state="collapsed"
)

=====================================================

CYBERPUNK BLUE UI

=====================================================

st.markdown("""

<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800;900&family=Rajdhani:wght@500;600;700&display=swap');

.stApp {
    background: radial-gradient(circle at 50% 15%, #090e23 0%, #03050c 100%);
    color: #e0f7fa;
    font-family: 'Rajdhani', sans-serif;
}

.zeno-brand {
    font-family: 'Orbitron', sans-serif;
    font-size: 2.6rem;
    font-weight: 900;
    letter-spacing: 3px;
    text-align: center;
    background: linear-gradient(90deg, #00f2fe, #4facfe, #b388ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.enter-card {
    background: rgba(10, 16, 38, 0.85);
    border: 2px solid rgba(0, 242, 254, 0.45);
    box-shadow: 0 0 40px rgba(0, 242, 254, 0.25);
    border-radius: 24px;
    padding: 35px 20px;
    text-align: center;
    margin: 30px auto;
    max-width: 650px;
}

.status-pill {
    display: inline-block;
    padding: 7px 18px;
    border-radius: 20px;
    background: rgba(0, 242, 254, 0.12);
    border: 1px solid #00f2fe;
    color: #00f2fe;
    letter-spacing: 2px;
}

.orb-wrapper {
    display: flex;
    justify-content: center;
    margin: 22px 0;
}

.core-orb {
    width: 100px;
    height: 100px;
    border-radius: 50%;
    background: radial-gradient(circle, #00f2fe 10%, #7f00ff 70%, #03050c 100%);
    box-shadow: 0 0 35px #00f2fe, 0 0 70px #7f00ff;
    animation: pulseOrb 2s infinite alternate ease-in-out;
}

@keyframes pulseOrb {
    from { transform: scale(.94); }
    to {
        transform: scale(1.07);
        box-shadow: 0 0 50px #00f2fe, 0 0 85px #7f00ff;
    }
}

section[data-testid="stSidebar"] {
    background-color: #060914;
    border-right: 1px solid rgba(0, 242, 254, .25);
}

.stButton > button {
    border-radius: 14px;
    border: 1px solid #00d9ff;
    background: linear-gradient(90deg, #00bcd4, #448aff);
    color: #03101c;
    font-weight: 800;
}

[data-testid="stChatMessage"] {
    border: 1px solid rgba(0, 242, 254, .18);
    border-radius: 15px;
}

.stTextInput input {
    border: 1px solid #00d9ff;
}
</style>""", unsafe_allow_html=True)

=====================================================

SESSION STATE

=====================================================

if "app_entered" not in st.session_state:
st.session_state.app_entered = False

if "messages" not in st.session_state:
st.session_state.messages = [
{
"role": "assistant",
"content": "Hello! I am ZENO AI. Your assistant is ready. How can I help you?"
}
]

=====================================================

API KEY

=====================================================

def get_groq_key():
# First check Streamlit secrets.
try:
key = st.secrets.get("GROQ_API_KEY", "")
if key:
return key.strip()
except Exception:
pass

# Then check environment variables.
return os.environ.get("GROQ_API_KEY", "").strip()

groq_key = get_groq_key()

=====================================================

GROQ API FUNCTION

=====================================================

def call_groq_api(prompt, api_token, history=None):
url = "https://api.groq.com/openai/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {api_token.strip()}",
    "Content-Type": "application/json",
    "User-Agent": "ZenoAI/2.0"
}

messages = [
    {
        "role": "system",
        "content": (
            "You are ZENO AI, a friendly and helpful personal assistant. "
            "Answer accurately and naturally. "
            "Understand English and Kannada. "
            "Reply in the language used by the user. "
            "Keep normal answers concise and easy to understand. "
            "Never claim you performed an action on the device "
            "unless that action was actually performed."
        )
    }
]

# Include recent conversation for context.
if history:
    messages.extend(history[-10:])

messages.append({
    "role": "user",
    "content": prompt
})

body = {
    "model": "openai/gpt-oss-120b",
    "messages": messages,
    "max_completion_tokens": 500,
    "temperature": 0.6
}

data = json.dumps(body).encode("utf-8")

request = urllib.request.Request(
    url,
    data=data,
    headers=headers,
    method="POST"
)

try:
    with urllib.request.urlopen(request, timeout=45) as response:
        result = json.loads(response.read().decode("utf-8"))

    return result["choices"][0]["message"]["content"].strip()

except urllib.error.HTTPError as error:
    details = error.read().decode("utf-8", errors="replace")

    if error.code == 401:
        raise RuntimeError(
            "API key invalid or unauthorized. Check your GROQ_API_KEY."
        ) from error

    if error.code == 403:
        raise RuntimeError(
            "API access denied. Check your Groq account and API permissions."
        ) from error

    if error.code == 404:
        raise RuntimeError(
            "API returned 404 Not Found. Check the endpoint and model ID. "
            f"Server details: {details}"
        ) from error

    if error.code == 429:
        raise RuntimeError(
            "API rate limit or quota reached. Please try again later. "
            f"Details: {details}"
        ) from error

    raise RuntimeError(
        f"Groq API HTTP {error.code}: {details}"
    ) from error

except urllib.error.URLError as error:
    raise RuntimeError(
        f"Network error. Check your internet connection: {error}"
    ) from error

except (KeyError, IndexError, json.JSONDecodeError) as error:
    raise RuntimeError(
        f"Unexpected API response: {error}"
    ) from error

=====================================================

BROWSER VOICE OUTPUT

=====================================================

def speak_text(text):
# JSON encoding safely escapes quotes and special characters.
safe_text = json.dumps(text[:1000], ensure_ascii=True)

speech_html = """
<script>
const message = MESSAGE_PLACEHOLDER;

if ("speechSynthesis" in window) {
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(message);
    utterance.lang = "en-IN";
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    const voices = window.speechSynthesis.getVoices();
    const voice = voices.find(
        v => v.lang.toLowerCase().startsWith("en-in")
    ) || voices.find(
        v => v.lang.toLowerCase().startsWith("en")
    );

    if (voice) {
        utterance.voice = voice;
    }

    window.speechSynthesis.speak(utterance);
}
</script>
""".replace("MESSAGE_PLACEHOLDER", safe_text)

st.components.v1.html(speech_html, height=0)

=====================================================

WELCOME SCREEN

=====================================================

if not st.session_state.app_entered:

st.markdown("""
<div class="enter-card">
    <div class="status-pill">NEURAL CORE READY</div>

    <div class="zeno-brand">
        ⚡ ZENO AI ⚡
    </div>

    <p style="color:#80deea;font-size:20px;">
        Next-Gen AI Voice Assistant
    </p>

    <div class="orb-wrapper">
        <div class="core-orb"></div>
    </div>

    <p style="color:#90caf9;">
        TOUCH TO SPEAK • AI CHAT • VOICE RESPONSE
    </p>
</div>
""", unsafe_allow_html=True)

left, center, right = st.columns([1, 1.5, 1])

with center:
    if st.button(
        "✨ CLICK TO ENTER ZENO AI",
        use_container_width=True
    ):
        st.session_state.app_entered = True
        st.rerun()

=====================================================

MAIN DASHBOARD

=====================================================

else:

st.markdown(
    '<div class="zeno-brand">⚡ ZENO AI CORE ⚡</div>',
    unsafe_allow_html=True
)

st.markdown("""
<div class="orb-wrapper">
    <div class="core-orb"
         style="width:70px;height:70px;">
    </div>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------

with st.sidebar:

    st.markdown("## 🎛️ Navigation & Tools")

    if st.button(
        "🚪 Exit to Welcome Screen",
        use_container_width=True
    ):
        st.session_state.app_entered = False
        st.rerun()

    if st.button(
        "🗑️ Clear Chat",
        use_container_width=True
    ):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Chat cleared. Hello again! How can I help?"
            }
        ]
        st.rerun()

    st.markdown("---")
    st.markdown("### 📂 Upload Media")

    uploaded_image = st.file_uploader(
        "🖼️ Upload Image",
        type=["jpg", "jpeg", "png"]
    )

    if uploaded_image:
        try:
            image = Image.open(uploaded_image)
            st.image(
                image,
                caption="Uploaded Image",
                use_container_width=True
            )
            st.info(
                "Image uploaded successfully. "
                "Automatic image understanding is not enabled in this version."
            )
        except Exception as error:
            st.error(f"Image error: {error}")

    uploaded_audio = st.file_uploader(
        "🎵 Upload Audio",
        type=["mp3", "wav", "ogg"]
    )

    if uploaded_audio:
        st.audio(uploaded_audio)

    st.markdown("---")
    st.caption("ZENO AI • Futuristic Assistant")

# -------------------------------------------------
# MICROPHONE
# -------------------------------------------------

st.components.v1.html("""
<div style="text-align:center;margin:10px 0 20px;">
    <button id="micBtn" style="
        background:linear-gradient(45deg,#00f2fe,#4facfe);
        border:none;
        color:#04091a;
        padding:14px 30px;
        border-radius:25px;
        font-weight:800;
        font-size:16px;
        cursor:pointer;
        box-shadow:0 0 20px rgba(0,242,254,.45);
    ">🎙️ TOUCH TO SPEAK</button>

    <div id="status"
         style="color:#80deea;font-size:14px;margin-top:10px;">
        Tap the button and speak your question.
    </div>
</div>

<script>
(() => {
    const micBtn = document.getElementById("micBtn");
    const status = document.getElementById("status");

    const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        status.innerText =
            "Voice recognition is unavailable in this browser. "
            + "Try a supported browser with microphone permission.";
        return;
    }

    const recognition = new SpeechRecognition();

    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-IN";

    let listening = false;

    function resetButton() {
        listening = false;
        micBtn.innerText = "🎙️ TOUCH TO SPEAK";
        micBtn.style.background =
            "linear-gradient(45deg,#00f2fe,#4facfe)";
    }

    micBtn.addEventListener("click", () => {
        if (listening) {
            recognition.stop();
            return;
        }

        try {
            recognition.start();
            listening = true;
            micBtn.innerText = "🛑 LISTENING...";
            micBtn.style.background = "#ff1744";
            status.innerText = "🔴 Listening... Speak now.";
        } catch (error) {
            status.innerText =
                "Could not start microphone. Please retry.";
            resetButton();
        }
    });

    recognition.onresult = (event) => {
        const spokenText =
            event.results[0][0].transcript;

        status.innerText = "Heard: " + spokenText;

        const parentDoc = window.parent.document;

        const input = parentDoc.querySelector(
            'textarea[aria-label="Ask Zeno anything..."]'
        );

        if (input) {
            const setter = Object.getOwnPropertyDescriptor(
                window.parent.HTMLTextAreaElement.prototype,
                "value"
            ).set;

            setter.call(input, spokenText);

            input.dispatchEvent(
                new Event("input", {bubbles: true})
            );

            status.innerText =
                "Question captured. Press Enter or Send to submit.";
        } else {
            status.innerText =
                "Speech recognized: " + spokenText
                + ". Type the question into the chat box.";
        }
    };

    recognition.onerror = (event) => {
        status.innerText =
            "Microphone error: " + event.error
            + ". Check microphone permission.";
        resetButton();
    };

    recognition.onend = () => {
        resetButton();
    };
})();
</script>
""", height=110)

# -------------------------------------------------
# DISPLAY CHAT HISTORY
# -------------------------------------------------

for message in st.session_state.messages:

    avatar = (
        "🔮"
        if message["role"] == "assistant"
        else "👤"
    )

    with st.chat_message(
        message["role"],
        avatar=avatar
    ):
        st.markdown(message["content"])

# -------------------------------------------------
# CHAT INPUT AND AI RESPONSE
# -------------------------------------------------

user_prompt = st.chat_input(
    "Ask Zeno anything...",
    key="zeno_chat_input"
)

if user_prompt:

    # Display and save user question.
    st.session_state.messages.append({
        "role": "user",
        "content": user_prompt
    })

    with st.chat_message("user", avatar="👤"):
        st.markdown(user_prompt)

    with st.chat_message("assistant", avatar="🔮"):

        if not groq_key:
            st.error(
                "GROQ_API_KEY is missing. Configure your API key "
                "in Streamlit secrets or your environment variables."
            )

        else:
            with st.spinner("🔮 ZENO is thinking..."):

                try:
                    # Keep previous conversation for context.
                    history = [
                        {
                            "role": msg["role"],
                            "content": msg["content"]
                        }
                        for msg in st.session_state.messages[:-1]
                        if msg["role"] in ("user", "assistant")
                    ]

                    # Keep the most recent messages.
                    reply = call_groq_api(
                        user_prompt,
                        groq_key,
                        history=history[-10:]
                    )

                    if not reply:
                        reply = "Sorry, I could not generate an answer."

                    st.markdown(reply)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": reply
                    })

                    # Speak the AI response.
                    speak_text(reply)

                except Exception as error:
                    st.error(str(error))

# -------------------------------------------------
# FOOTER
# -------------------------------------------------

st.markdown("""
<div style="
    text-align:center;
    color:#80deea;
    padding:20px;
    font-size:13px;">
    🔮 ZENO AI CORE • YOUR SMART AI ASSISTANT
</div>
""", unsafe_allow_html=True)
