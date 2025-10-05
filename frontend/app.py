import streamlit as st
from PIL import Image, ImageDraw
import sys
import os

# Add the parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
backend_dir = os.path.join(parent_dir, 'backend')

if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Try to import speech recognition
try:
    import speech_recognition as sr

    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False

# Import backend
try:
    from soundpy_cloud import perform_action, check_reminders

    BACKEND_LOADED = True
except ImportError:
    try:
        from soundpy import perform_action, check_reminders

        BACKEND_LOADED = True
    except ImportError as e:
        st.error(f"❌ Cannot import backend: {e}")
        BACKEND_LOADED = False

st.set_page_config(page_title="Voice Assistant", layout="centered")

# Initialize session state
if 'listening' not in st.session_state:
    st.session_state.listening = False
if 'last_command' not in st.session_state:
    st.session_state.last_command = ""
if 'status' not in st.session_state:
    st.session_state.status = "Ready"

# ---- Title ----
st.title("🎤 Voice Assistant")
st.markdown("---")


# ---- Circular Listening UI ----
def create_circle_image(radius=150, color=(135, 206, 250), is_listening=False):
    size = (radius * 2, radius * 2)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Change color based on listening state
    if is_listening:
        color = (255, 99, 71)  # Red when listening

    draw.ellipse((0, 0, size[0], size[1]), fill=color)

    # Add inner circle for better effect
    inner_radius = radius - 20
    inner_pos = (20, 20, size[0] - 20, size[1] - 20)
    draw.ellipse(inner_pos, fill=color, outline=(255, 255, 255), width=5)

    return img


# Display circle
circle_img = create_circle_image(is_listening=st.session_state.listening)
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image(circle_img, width=300)

# ---- Status Display ----
status_placeholder = st.empty()
status_placeholder.markdown(f"### Status: {st.session_state.status}")

if st.session_state.last_command:
    st.info(f"🗣️ You said: **{st.session_state.last_command}**")


# ---- Voice Recognition Function ----
def listen_and_act():
    """Main function to listen and execute commands"""

    if not BACKEND_LOADED:
        st.error("❌ Backend not loaded. Cannot execute commands.")
        return

    if not SPEECH_AVAILABLE:
        st.error("❌ Speech recognition not available. Install locally for voice features.")
        return

    recognizer = sr.Recognizer()

    try:
        st.session_state.status = "🔍 Checking microphone..."
        status_placeholder.markdown(f"### Status: {st.session_state.status}")

        with sr.Microphone() as source:
            st.session_state.status = "🎧 Adjusting for ambient noise..."
            status_placeholder.markdown(f"### Status: {st.session_state.status}")

            recognizer.adjust_for_ambient_noise(source, duration=1)

            st.session_state.status = "🎧 Listening... Speak now!"
            st.session_state.listening = True
            status_placeholder.markdown(f"### Status: {st.session_state.status}")

            # Listen for audio
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=10)

        st.session_state.status = "🔄 Processing your speech..."
        st.session_state.listening = False
        status_placeholder.markdown(f"### Status: {st.session_state.status}")

        # Recognize speech
        command = recognizer.recognize_google(audio)
        st.session_state.last_command = command
        st.session_state.status = f"✅ Recognized: {command}"

        # Perform the action
        result = perform_action(command)

        # Process result
        if isinstance(result, dict):
            if result.get("type") == "link":
                st.session_state.status = result["message"]
                st.markdown(f"[🔗 Click here to open]({result['url']})")
            elif result.get("type") == "error":
                st.session_state.status = result["message"]
                st.error(result["message"])
            else:
                st.session_state.status = result.get("message", "✅ Command executed")
                st.success(result.get("message", "✅ Command executed"))
        else:
            st.session_state.status = str(result) if result else "✅ Command executed"

        # Check reminders
        reminders_triggered = check_reminders()
        for reminder in reminders_triggered:
            st.info(reminder)

    except sr.WaitTimeoutError:
        st.session_state.status = "⏱️ Timeout - No speech detected"
        st.session_state.listening = False
    except sr.UnknownValueError:
        st.session_state.status = "⚠️ Could not understand audio"
        st.session_state.listening = False
    except sr.RequestError as e:
        st.session_state.status = f"⚠️ Speech recognition error: {str(e)}"
        st.session_state.listening = False
    except OSError as e:
        st.session_state.status = "❌ Microphone error - Check if it's connected"
        st.session_state.listening = False
    except Exception as e:
        st.session_state.status = f"❌ Error: {str(e)}"
        st.session_state.listening = False

    st.rerun()


# ---- Control Button (ONLY LISTENING) ----
st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    if st.button("🎙️ Start Listening", type="primary", disabled=not (BACKEND_LOADED and SPEECH_AVAILABLE)):
        listen_and_act()

# Warning for cloud users
if not SPEECH_AVAILABLE:
    st.warning("⚠️ Voice recognition requires local installation. This feature doesn't work on Streamlit Cloud.")
    with st.expander("💻 How to Install Locally"):
        st.markdown("""
        ```bash
        # Install dependencies
        pip install streamlit SpeechRecognition pyaudio pillow

        # Run locally
        streamlit run frontend/app.py
        ```
        """)

# ---- Command Examples ----
with st.expander("📋 Available Voice Commands"):
    st.markdown("""
    **YouTube Controls:**
    - "Play Believer on YouTube"
    - "Pause music"
    - "Resume music"

    **Web Browsing:**
    - "Open YouTube"
    - "Open Google"
    - "Search for Python programming"

    **Volume Control:**
    - "Mute" / "Unmute"
    - "Volume up" / "Volume down"
    - "Increase volume" / "Decrease volume"

    **Reminders & Alarms:**
    - "Set reminder for 10 seconds to check oven"
    - "Set alarm for 14:30"
    """)

# ---- Footer ----
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>🎤 Voice Assistant v1.0 - Voice Only Mode</div>",
    unsafe_allow_html=True
)