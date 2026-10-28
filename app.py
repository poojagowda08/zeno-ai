import streamlit as st
import os
import json
import urllib.request
import urllib.error
from PIL import Image

st.set_page_config(
page_title="ZENO AI",
page_icon="🔮",
layout="wide",
initial_sidebar_state="collapsed"
)

st.markdown("""

<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800;900&family=Rajdhani:wght@500;600;700&display=swap');

.stApp {
    background: radial-gradient(circle at 50% 15%, #090e23, #03050c);
    color: #e0f7fa;
    font-family: 'Rajdhani', sans-serif;
}

.zeno-brand {
    font-family: 'Orbitron', sans-serif;
    font-size: 2.5rem;
    font-weight: 900;
    text-align: center;
    letter-spacing: 3px;
    background: linear-gradient(90deg, #00f2fe, #4facfe, #b388ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.enter-card {
    background: rgba(10,16,38,.85);
    border: 2px solid rgba(0,242,254,.45);
    box-shadow: 0 0 40px rgba(0,242,254,.25);
    border-radius: 24px;
    padding: 35px 20px;
    text-align: center;
    margin: 30px auto;
    max-width: 650px;
}

.core-orb {
    width: 100px;
    height: 100px;
    border-radius: 50%;
    margin: 25px auto;
    background: radial-gradient(circle, #00f2fe, #7f00ff 70%, #03050c);
    box-shadow: 0 0 35px #00f2fe, 0 0 70px #7f00ff;
    animation: pulseOrb 2s infinite alternate;
}

@keyframes pulseOrb {
    from { transform: scale(.94); }
    to { transform: scale(1.07); }
}

.stButton > button {
    background: linear-gradient(90deg, #00f2fe, #4facfe);
    color: #03050c;
    font-weight: 800;
    border-radius: 14px;
    border: 1px solid #00f2fe;
}

section[data-testid="stSidebar"] {
    background: #060914;
}
</style>""", unsafe_allow_html=True)

if "app_entered" not in st.session_state:
st.session_state.app_entered = False

if "messages" not in st.session_state:
st.session_state.messages = [
{
"role": "assistant",
"content": "Hello! I am ZENO AI. Ask me anything!"
}
]

def get_groq_key():
try:
key = st.secrets.get("GROQ_API_KEY", "")
if key:
return key.strip()
except Exception:
pass
return os.environ.get("GROQ_API_KEY", "").strip()

groq_key = get_groq_key()

def call_groq_api(prompt, api_token, history=None):
url = "https://api.groq.com/openai/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json"
}

messages = [{
    "role": "system",
    "content": (
        "You are ZENO AI, a friendly assistant. "
        "Answer clearly in English or Kannada, depending "
        "on the user's language. Keep answers concise."
    )
}]

if history:
    messages.extend(history[-10:])

messages.append({"role": "user", "content": prompt})

body = {
    "model": "openai/gpt-oss-120b",
    "messages": messages,
    "max_completion_tokens": 500,
    "temperature": 0.6
}

request = urllib.request.Request(
    url,
    data=json.dumps(body).encode("utf-8"),
    headers=headers,
    method="POST"
)

try:
    with urllib.request.urlopen(request, timeout=45) as response:
        result = json.loads(response.read().decode("utf-8"))
    return result["choices"][0]["message"]["content"].strip()

except urllib.error.HTTPError as error:
    details = error.read().decode("utf-8", errors="replace")
    raise RuntimeError(
        f"Groq API error {error.code}: {details}"
    ) from error

except urllib.error.URLError as error:
    raise RuntimeError(
        f"Internet connection error: {error}"
    ) from error

def speak_text(text):
safe_text = json.dumps(text[:1000], ensure_ascii=True)

html = """
<script>
const message = MESSAGE_TEXT;
if ("speechSynthesis" in window) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(message);
    utterance.lang = "en-IN";
    utterance.rate = 1;
    const voices = window.speechSynthesis.getVoices();
    const voice = voices.find(v =>
        v.lang.toLowerCase().startsWith("en-in")
    ) || voices.find(v =>
        v.lang.toLowerCase().startsWith("en")
    );
    if (voice) utterance.voice = voice;
    window.speechSynthesis.speak(utterance);
}
</script>
""".replace("MESSAGE_TEXT", safe_text)

st.components.v1.html(html, height=0)

if not st.session_state.app_entered:
st.markdown("""
<div class="enter-card">
<h3 style="color:#00f2fe;">NEURAL CORE READY</h3>
<div class="zeno-brand">⚡ ZENO AI ⚡</div>
<p style="color:#80deea;font-size:20px;">
Your Futuristic AI Assistant
</p>
<div class="core-orb"></div>
<p style="color:#90caf9;">
AI CHAT • VOICE • SMART ASSISTANT
</p>
</div>
""", unsafe_allow_html=True)

left, center, right = st.columns([1, 1.5, 1])
with center:
    if st.button("✨ ENTER ZENO AI", use_container_width=True):
        st.session_state.app_entered = True
        st.rerun()

else:
st.markdown(
'<div class="zeno-brand">⚡ ZENO AI CORE ⚡</div>',
unsafe_allow_html=True
)
st.markdown('<div class="core-orb"></div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## Navigation & Tools")

    if st.button("🚪 Exit to Welcome Screen"):
        st.session_state.app_entered = False
        st.rerun()

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = [{
            "role": "assistant",
            "content": "Chat cleared. How can I help you?"
        }]
        st.rerun()

    st.markdown("---")
    st.markdown("### Upload Media")

    uploaded_image = st.file_uploader(
        "Upload Image",
        type=["jpg", "jpeg", "png"]
    )

    if uploaded_image:
        try:
            img = Image.open(uploaded_image)
            st.image(img, caption="Uploaded Image",
                     use_container_width=True)
            st.info("Image preview is available.")
        except Exception as error:
            st.error(f"Image error: {error}")

    uploaded_audio = st.file_uploader(
        "Upload Audio",
        type=["mp3", "wav", "ogg"]
    )

    if uploaded_audio:
        st.audio(uploaded_audio)

st.components.v1.html("""
<div style="text-align:center;margin:15px;">
  <button id="micBtn" style="
    background:linear-gradient(45deg,#00f2fe,#4facfe);
    border:0;padding:14px 28px;border-radius:25px;
    font-weight:800;cursor:pointer;">
    🎙️ TOUCH TO SPEAK
  </button>
  <div id="status" style="color:#80deea;margin-top:10px;">
    Tap the button and speak in English.
  </div>
</div>
<script>
const button = document.getElementById("micBtn");
const status = document.getElementById("status");
const SR = window.SpeechRecognition ||
           window.webkitSpeechRecognition;

if (SR) {
    const recognition = new SR();
    recognition.lang = "en-IN";
    recognition.continuous = false;
    recognition.interimResults = false;

    button.onclick = () => {
        status.innerText = "Listening...";
        try { recognition.start(); }
        catch (e) { status.innerText = "Please try again."; }
    };

    recognition.onresult = (event) => {
        const spoken = event.results[0][0].transcript;
        status.innerText = "Heard: " + spoken;

        const doc = window.parent.document;
        const input = doc.querySelector(
            'textarea[aria-label="Ask Zeno anything..."]'
        );

        if (input) {
            const setter = Object.getOwnPropertyDescriptor(
                window.parent.HTMLTextAreaElement.prototype,
                "value"
            ).set;
            setter.call(input, spoken);
            input.dispatchEvent(
                new Event("input", {bubbles: true})
            );
            status.innerText =
                "Question captured. Press Enter to send.";
        }
    };

    recognition.onerror = (event) => {
        status.innerText = "Microphone error: " + event.error;
    };
} else {
    status.innerText =
        "Voice recognition unavailable. Try Chrome.";
}
</script>
""", height=100)

for msg in st.session_state.messages:
    avatar = "🔮" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

user_prompt = st.chat_input("Ask Zeno anything...")

if user_prompt:
    st.session_state.messages.append({
        "role": "user",
        "content": user_prompt
    })

    with st.chat_message("user", avatar="👤"):
        st.markdown(user_prompt)

    with st.chat_message("assistant", avatar="🔮"):
        if not groq_key:
            st.error(
                "GROQ_API_KEY missing. Add it to Streamlit Secrets."
            )
        else:
            try:
                history = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages[:-1]
                    if m["role"] in ("user", "assistant")
                ]

                with st.spinner("ZENO is thinking..."):
                    reply = call_groq_api(
                        user_prompt, groq_key, history
                    )

                st.markdown(reply)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": reply
                })
                speak_text(reply)

            except Exception as error:
                st.error(str(error))
