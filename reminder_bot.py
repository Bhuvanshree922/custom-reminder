import datetime
import requests
import os

# Telegram Bot configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Set in GitHub secrets
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")      # Set in GitHub secrets

# File path
REMINDERS_FILE = "reminders.txt"

def send_telegram_message(message):
    """Send a message to Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("Message sent:", message)
    else:
        print("Failed to send message:", response.json())

def parse_reminders(file_path):
    """Parse the reminders file and return a list of reminders."""
    reminders = []
    with open(file_path, "r") as file:
        for line in file:
            line = line.strip()
            if line:  # Skip empty lines
                parts = line.split(" - ", 2)
                if len(parts) == 3:
                    reminders.append({"type": parts[0], "time": parts[1], "task": parts[2]})
    return reminders

def get_next_run_time():
    """Calculate the next execution time based on reminders."""
    now = datetime.datetime.now()
    reminders = parse_reminders(REMINDERS_FILE)

    # Default cron for every_minute or every_hour
    cron_parts = {"minute": "*", "hour": "*"}
    next_times = []

    for reminder in reminders:
        reminder_type = reminder["type"]
        reminder_time = reminder["time"].strip().lower()

        # Send messages for every_minute or every_hour
        if reminder_type == "every_minute":
            send_telegram_message(f"⏰ Reminder: {reminder['task']}")
            return "* * * * *"

        if reminder_type == "every_hour":
            if now.minute == 0:
                send_telegram_message(f"⏰ Reminder: {reminder['task']}")
            return "0 * * * *"

        # Parse time for other reminders
        try:
            reminder_dt = datetime.datetime.strptime(reminder_time, "%I %p")
            reminder_dt = now.replace(hour=reminder_dt.hour, minute=reminder_dt.minute, second=0, microsecond=0)
        except ValueError:
            continue

        if reminder_type == "everyday":
            if reminder_dt < now:
                reminder_dt += datetime.timedelta(days=1)
            next_times.append(reminder_dt)

        elif reminder_type.startswith(now.strftime("%a").lower()):
            if reminder_dt < now:
                reminder_dt += datetime.timedelta(days=7)
            next_times.append(reminder_dt)

        elif reminder_type == "one_time" and reminder_dt > now:
            send_telegram_message(f"⏰ One-time Reminder: {reminder['task']}")
            continue  # Skip adding this to next cron

    if not next_times:
        return None

    # Get the nearest time
    next_run = min(next_times)

    cron_parts["minute"] = str(next_run.minute)
    cron_parts["hour"] = str(next_run.hour)

    # Return cron format for the next time
    return f"{cron_parts['minute']} {cron_parts['hour']} * * *"

if __name__ == "__main__":
    next_cron = get_next_run_time()
    if next_cron:
        print(next_cron)
