import speech_recognition as sr
import webbrowser
import os
import pywhatkit
import pyautogui
import pygetwindow as gw
import time
from datetime import datetime, timedelta
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume


# ------------------- Volume Control -------------------
def get_volume_interface():
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return cast(interface, POINTER(IAudioEndpointVolume))


def set_volume(level: float):
    volume = get_volume_interface()
    volume.SetMasterVolumeLevelScalar(level, None)


def mute_volume():
    volume = get_volume_interface()
    volume.SetMute(1, None)


def unmute_volume():
    volume = get_volume_interface()
    volume.SetMute(0, None)


def increase_volume(step=0.1):
    volume = get_volume_interface()
    current = volume.GetMasterVolumeLevelScalar()
    new_level = min(1.0, current + step)
    volume.SetMasterVolumeLevelScalar(new_level, None)
    return f"🔊 Volume increased to {int(new_level * 100)}%"


def decrease_volume(step=0.1):
    volume = get_volume_interface()
    current = volume.GetMasterVolumeLevelScalar()
    new_level = max(0.0, current - step)
    volume.SetMasterVolumeLevelScalar(new_level, None)
    return f"🔉 Volume decreased to {int(new_level * 100)}%"


# ------------------- YouTube Control -------------------
def focus_youtube():
    windows = gw.getWindowsWithTitle("YouTube")
    if windows:
        win = windows[0]
        win.activate()
        time.sleep(0.5)
        return True
    return False


def pause_youtube():
    if focus_youtube():
        pyautogui.press("space")
        return "⏸️ YouTube paused"
    else:
        return "❌ Could not find YouTube window"


def resume_youtube():
    if focus_youtube():
        pyautogui.press("space")
        return "▶️ YouTube resumed"
    else:
        return "❌ Could not find YouTube window"


# ------------------- Reminders & Alarms -------------------
reminders = []


def set_reminder(text, seconds):
    remind_time = datetime.now() + timedelta(seconds=seconds)
    reminders.append((remind_time, text))
    return f"⏰ Reminder set for {seconds} seconds from now: {text}"


def check_reminders():
    now = datetime.now()
    triggered = []
    for r in reminders[:]:
        if now >= r[0]:
            triggered.append(f"🔔 Reminder: {r[1]}")
            reminders.remove(r)
    return triggered


# ------------------- Perform Actions -------------------
def perform_action(command):
    command = command.lower()

    # --- YouTube Music ---
    if "play" in command and "youtube" in command:
        song = command.replace("play", "").replace("on youtube", "").strip()
        if song:
            print(f"🎵 Playing {song} on YouTube...")
            pywhatkit.playonyt(song)
            return f"🎵 Playing '{song}' on YouTube..."
        else:
            return "❗ I didn't catch the song name."

    # --- Google Search ---
    elif "search for" in command:
        query = command.replace("search for", "").strip()
        if query:
            print(f"🔍 Searching Google for: {query}")
            webbrowser.open(f"https://www.google.com/search?q={query}")
            return f"🔍 Searching Google for: {query}"
        else:
            return "❗ No search query detected."

    # --- Open Websites ---
    elif "open youtube" in command:
        print("🎬 Opening YouTube...")
        webbrowser.open("https://www.youtube.com")
        return "🎬 Opening YouTube..."

    elif "open google" in command:
        print("🌐 Opening Google...")
        webbrowser.open("https://www.google.com")
        return "🌐 Opening Google..."

    # --- YouTube Pause/Resume ---
    elif "pause music" in command or "pause" in command:
        return pause_youtube()

    elif "resume music" in command or "resume" in command:
        return resume_youtube()

    # --- Volume Control ---
    elif "unmute" in command:
        unmute_volume()
        return "🔊 Volume unmuted"

    elif "mute" in command:
        mute_volume()
        return "🔇 Volume muted"

    elif "volume up" in command:
        set_volume(1.0)
        return "🔊 Volume set to 100%"

    elif "volume down" in command:
        set_volume(0.3)
        return "🔉 Volume set to 30%"

    elif "increase volume" in command:
        return increase_volume(0.1)

    elif "decrease volume" in command:
        return decrease_volume(0.1)

    # --- Set Reminder ---
    elif "set reminder" in command or "remind me" in command:
        try:
            parts = command.split("for")[1].strip().split("to")
            seconds = int(parts[0].replace("seconds", "").strip())
            text = parts[1].strip()
            return set_reminder(text, seconds)
        except:
            return "❌ Could not set reminder. Use: 'Set reminder for 10 seconds to check oven'"

    # --- Set Alarm ---
    elif "set alarm" in command:
        try:
            time_part = command.split("for")[1].strip()
            alarm_time = datetime.strptime(time_part, "%H:%M").time()
            reminders.append((datetime.combine(datetime.today(), alarm_time), "Alarm!"))
            return f"⏰ Alarm set for {alarm_time}"
        except:
            return "❌ Could not set alarm. Use: 'Set alarm for HH:MM' (24-hour format)"

    # --- Shutdown (simulation) ---
    elif "shutdown" in command:
        return "⚡ Shutting down system (simulation)..."
        # os.system("shutdown /s /t 1")

    else:
        return "🤔 Command not recognized. Try again."


# ------------------- Main Loop (for standalone usage) -------------------
if __name__ == "__main__":
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    print("🎤 Voice Assistant Started. Examples:")
    print("👉 'Play Believer on YouTube'")
    print("👉 'Search for Python programming'")
    print("👉 'Mute' / 'Unmute' / 'Volume up' / 'Volume down'")
    print("👉 'Increase volume' / 'Decrease volume'")
    print("👉 'Pause music' / 'Resume music'")
    print("👉 'Set reminder for 10 seconds to check oven'")
    print("👉 'Set alarm for 14:30'")

    while True:
        try:
            with mic as source:
                recognizer.adjust_for_ambient_noise(source)
                print("\nListening...")
                audio = recognizer.listen(source)

            command = recognizer.recognize_google(audio)
            print(f"🗣️ You said: {command}")
            result = perform_action(command)
            print(result)

            reminders_triggered = check_reminders()
            for reminder in reminders_triggered:
                print(reminder)

        except sr.UnknownValueError:
            print("⚠️ Could not understand audio.")
        except sr.RequestError:
            print("⚠️ Speech recognition service unavailable.")
        except KeyboardInterrupt:
            print("\n🛑 Exiting Voice Assistant.")
            break