"""
Cloud-compatible version of soundpy.py
Only includes web-based features that work without desktop access
"""

import webbrowser
from datetime import datetime, timedelta

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
    """
    Process commands - Cloud version
    Only includes web-based actions
    """
    command = command.lower()

    # --- YouTube Music ---
    if "play" in command and "youtube" in command:
        song = command.replace("play", "").replace("on youtube", "").strip()
        if song:
            search_url = f"https://www.youtube.com/results?search_query={song.replace(' ', '+')}"
            return {"type": "link", "url": search_url, "message": f"🎵 Search YouTube for: {song}"}
        else:
            return {"type": "error", "message": "❗ I didn't catch the song name."}

    # --- Google Search ---
    elif "search for" in command:
        query = command.replace("search for", "").strip()
        if query:
            search_url = f"https://www.google.com/search?q={query}"
            return {"type": "link", "url": search_url, "message": f"🔍 Search Google for: {query}"}
        else:
            return {"type": "error", "message": "❗ No search query detected."}

    # --- Open Websites ---
    elif "open youtube" in command:
        return {"type": "link", "url": "https://www.youtube.com", "message": "🎬 Opening YouTube..."}

    elif "open google" in command:
        return {"type": "link", "url": "https://www.google.com", "message": "🌐 Opening Google..."}

    # --- Disabled Features (Desktop only) ---
    elif any(keyword in command for keyword in ["pause", "resume", "mute", "unmute", "volume"]):
        return {"type": "error", "message": "⚠️ Audio controls require local installation"}

    # --- Set Reminder ---
    elif "set reminder" in command or "remind me" in command:
        try:
            parts = command.split("for")[1].strip().split("to")
            seconds = int(parts[0].replace("seconds", "").strip())
            text = parts[1].strip()
            message = set_reminder(text, seconds)
            return {"type": "success", "message": message}
        except:
            return {"type": "error",
                    "message": "❌ Could not set reminder. Use: 'Set reminder for 10 seconds to check oven'"}

    # --- Set Alarm ---
    elif "set alarm" in command:
        try:
            time_part = command.split("for")[1].strip()
            alarm_time = datetime.strptime(time_part, "%H:%M").time()
            reminders.append((datetime.combine(datetime.today(), alarm_time), "Alarm!"))
            return {"type": "success", "message": f"⏰ Alarm set for {alarm_time}"}
        except:
            return {"type": "error", "message": "❌ Could not set alarm. Use: 'Set alarm for HH:MM' (24-hour format)"}

    else:
        return {"type": "error", "message": "🤔 Command not recognized. Try: 'open youtube', 'search for python'"}