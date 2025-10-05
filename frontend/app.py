import streamlit as st
import speech_recognition as sr
from PIL import Image, ImageDraw
import sys
import os

# Add the parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
backend_dir = os.path.join(parent_dir, 'backend')

if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

try:
    from soundpy import perform_action, check_reminders

    BACKEND_LOADED = True
except ImportError as e:
    st.error(f"❌ Cannot import backend: {e}")
    st.info("💡 Make sure soundpy.py is in the backend folder")
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

    recognizer = sr.Recognizer()

    # Add to log
    st.session_state.log.append(f"[{st.session_state.status}] Button clicked")

    try:
        # Check if microphone is available
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
        st.session_state.status = f"✅ Recognized: {command}"
        st.session_state.log.append(f"Recognized: {command}")

        # Perform the action
        result = perform_action(command)
        if result:
            st.session_state.status = result
            st.session_state.log.append(f"Result: {result}")

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


# ---- Control Buttons ----
st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    if st.button("🎙️ Start Listening", type="primary", disabled=not BACKEND_LOADED):
        st.session_state.log.append("=== NEW REQUEST ===")
        listen_and_act()

# ---- Debug Log ----
with st.expander("🐛 Debug Log"):
    if st.session_state.log:
        for log_entry in st.session_state.log[-20:]:  # Show last 20 entries
            st.text(log_entry)
    else:
        st.text("No logs yet. Click 'Start Listening' to begin.")

    if st.button("Clear Log"):
        st.session_state.log = []
        st.rerun()

# ---- Command Examples ----
with st.expander("📋 Available Commands"):
    st.markdown("""
    **YouTube Controls:**
    - 'Play [song name] on YouTube'
    - 'Pause music' or 'Pause'
    - 'Resume music' or 'Resume'

    **Web Browsing:**
    - 'Open YouTube'
    - 'Open Google'
    - 'Search for [query]'

    **Volume Control:**
    - 'Mute' / 'Unmute'
    - 'Volume up' / 'Volume down'
    - 'Increase volume' / 'Decrease volume'

    **Reminders & Alarms:**
    - 'Set reminder for 10 seconds to check oven'
    - 'Set alarm for 14:30'

    **System:**
    - 'Shutdown' (simulated)
    """)

# ---- System Check ----
with st.expander("⚙️ System Check"):
    st.write("**Backend Status:**", "✅ Loaded" if BACKEND_LOADED else "❌ Not Loaded")

    # Check microphone
    try:
        mic_list = sr.Microphone.list_microphone_names()
        st.write("**Available Microphones:**")
        for idx, name in enumerate(mic_list):
            st.text(f"  [{idx}] {name}")
    except Exception as e:
        st.error(f"Cannot list microphones: {e}")

    st.write("**Python Path:**")
    st.code("\n".join(sys.path[:3]))

# ---- Footer ----
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>🎤 Voice Assistant v1.0</div>",
    unsafe_allow_html=True
)