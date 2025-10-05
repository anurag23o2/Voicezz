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

# Try to import speech recognition (optional for cloud)
try:
    import speech_recognition as sr

    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False
    st.warning("⚠️ Speech recognition not available. Using text input mode.")

# Import cloud-compatible backend
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
if 'log' not in st.session_state:
    st.session_state.log = []

# ---- Title ----
st.title("🎤 Voice Assistant")
if not SPEECH_AVAILABLE:
    st.info("💡 Running in text mode. Voice features require local installation.")
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
    st.info(f"🗣️ Last Command: **{st.session_state.last_command}**")


# ---- Voice Recognition Function ----
def listen_and_act():
    """Main function to listen and execute commands"""

    if not BACKEND_LOADED:
        st.error("❌ Backend not loaded. Cannot execute commands.")
        return

    if not SPEECH_AVAILABLE:
        st.error("❌ Speech recognition not available.")
        return

    recognizer = sr.Recognizer()

    try:
        st.session_state.status = "🔍 Checking microphone..."
        st.session_state.log.append("Checking microphone...")
        status_placeholder.markdown(f"### Status: {st.session_state.status}")

        with sr.Microphone() as source:
            st.session_state.status = "🎧 Adjusting for ambient noise..."
            st.session_state.log.append("Adjusting for noise...")
            status_placeholder.markdown(f"### Status: {st.session_state.status}")

            recognizer.adjust_for_ambient_noise(source, duration=1)

            st.session_state.status = "🎧 Listening... Speak now!"
            st.session_state.listening = True
            st.session_state.log.append("Listening started...")
            status_placeholder.markdown(f"### Status: {st.session_state.status}")

            # Listen for audio
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=10)
            st.session_state.log.append("Audio captured")

        st.session_state.status = "🔄 Processing your speech..."
        st.session_state.listening = False
        st.session_state.log.append("Processing audio...")
        status_placeholder.markdown(f"### Status: {st.session_state.status}")

        # Recognize speech
        command = recognizer.recognize_google(audio)
        st.session_state.last_command = command
        st.session_state.log.append(f"Recognized: {command}")

        # Perform the action
        result = perform_action(command)
        process_result(result)

        # Check reminders
        reminders_triggered = check_reminders()
        for reminder in reminders_triggered:
            st.session_state.log.append(reminder)

    except sr.WaitTimeoutError:
        st.session_state.status = "⏱️ Timeout - No speech detected"
        st.session_state.listening = False
        st.session_state.log.append("ERROR: Timeout")
    except sr.UnknownValueError:
        st.session_state.status = "⚠️ Could not understand audio"
        st.session_state.listening = False
        st.session_state.log.append("ERROR: Could not understand")
    except sr.RequestError as e:
        st.session_state.status = f"⚠️ Speech recognition error: {str(e)}"
        st.session_state.listening = False
        st.session_state.log.append(f"ERROR: {str(e)}")
    except OSError as e:
        st.session_state.status = "❌ Microphone error - Check if it's connected"
        st.session_state.listening = False
        st.session_state.log.append(f"ERROR: Microphone - {str(e)}")
    except Exception as e:
        st.session_state.status = f"❌ Error: {str(e)}"
        st.session_state.listening = False
        st.session_state.log.append(f"ERROR: {type(e).__name__} - {str(e)}")

    st.rerun()


# ---- Text Input Function ----
def process_text_command(command):
    """Process text-based commands"""
    if not BACKEND_LOADED:
        st.error("❌ Backend not loaded.")
        return

    st.session_state.last_command = command
    st.session_state.log.append(f"Text command: {command}")

    result = perform_action(command)
    process_result(result)

    # Check reminders
    reminders_triggered = check_reminders()
    for reminder in reminders_triggered:
        st.info(reminder)
        st.session_state.log.append(reminder)


def process_result(result):
    """Process the result from backend"""
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


# ---- Text Input Mode ----
st.markdown("---")
st.markdown("### Enter Command:")
command_input = st.text_input(
    "Type your command",
    placeholder="e.g., open youtube, search for python tutorials",
    label_visibility="collapsed"
)

# ---- Control Buttons ----
col1, col2, col3 = st.columns([1, 1, 1])

if SPEECH_AVAILABLE:
    with col1:
        if st.button("🎙️ Voice", type="secondary", disabled=not BACKEND_LOADED):
            st.session_state.log.append("=== VOICE REQUEST ===")
            listen_and_act()

with col2 if SPEECH_AVAILABLE else col1:
    if st.button("🚀 Execute", type="primary", disabled=not BACKEND_LOADED):
        if command_input:
            st.session_state.log.append("=== TEXT REQUEST ===")
            process_text_command(command_input)
            st.rerun()
        else:
            st.warning("Please enter a command first!")

with col3 if SPEECH_AVAILABLE else col2:
    if st.button("🔄 Clear"):
        st.session_state.last_command = ""
        st.session_state.status = "Ready"
        st.rerun()

# ---- Debug Log ----
with st.expander("🐛 Debug Log"):
    if st.session_state.log:
        for log_entry in st.session_state.log[-20:]:
            st.text(log_entry)
    else:
        st.text("No logs yet.")

    if st.button("Clear Log"):
        st.session_state.log = []
        st.rerun()

# ---- Command Examples ----
with st.expander("📋 Available Commands"):
    st.markdown("""
    **Web Browsing:**
    - 'Open YouTube'
    - 'Open Google'
    - 'Search for [query]'
    - 'Play [song name] on YouTube'

    **Reminders & Alarms:**
    - 'Set reminder for 10 seconds to check oven'
    - 'Set alarm for 14:30'

    **Note:** Audio controls (volume, pause/resume) require local installation.
    """)

# ---- Installation Instructions ----
with st.expander("💻 Install Full Version Locally"):
    st.markdown("""
    For voice recognition and desktop automation:

    ```bash
    # Clone the repository
    git clone https://github.com/yourusername/voicezz.git
    cd voicezz

    # Install dependencies
    pip install -r requirements.txt

    # Run locally
    streamlit run frontend/app.py
    ```
    """)

# ---- System Check ----
with st.expander("⚙️ System Check"):
    st.write("**Backend Status:**", "✅ Loaded" if BACKEND_LOADED else "❌ Not Loaded")
    st.write("**Speech Recognition:**", "✅ Available" if SPEECH_AVAILABLE else "❌ Not Available")

    if SPEECH_AVAILABLE:
        try:
            mic_list = sr.Microphone.list_microphone_names()
            st.write("**Available Microphones:**")
            for idx, name in enumerate(mic_list):
                st.text(f"  [{idx}] {name}")
        except Exception as e:
            st.error(f"Cannot list microphones: {e}")

# ---- Footer ----
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>🎤 Voice Assistant v1.0</div>",
    unsafe_allow_html=True
)