import datetime
import os
import pytz
from telebot import TeleBot

# Constants
REMINDER_FILE = "reminders.txt"
CRON_FILE = "cron_schedule.txt"
TRACKED_DAYS_FILE = "tracked_days.txt"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # Replace with the recipient's chat ID

# Set the timezone (replace with your desired timezone)
timezone = pytz.timezone("Asia/Kolkata")

# Initialize the Telegram bot
bot = TeleBot(TELEGRAM_TOKEN)


def load_reminders():
    """Load reminders from the reminders file."""
    with open(REMINDER_FILE, "r") as file:
        return file.readlines()


def send_telegram_message(message):
    """Send a message to the specified Telegram chat."""
    bot.send_message(CHAT_ID, message)


def get_current_time():
    """Get the current time in the configured timezone."""
    return datetime.datetime.now(timezone)


def get_cron_expression(reminder_type, time_str=None):
    """
    Converts a reminder type and time into a cron expression.
    """
    if reminder_type == "every_minute":
        return "* * * * *"
    if reminder_type == "every_hour":
        return "0 * * * *"

    if time_str:
        time_obj = datetime.datetime.strptime(time_str, "%I %p").replace(tzinfo=timezone)
        minute = time_obj.minute
        hour = time_obj.hour

        if "recur" in reminder_type:
            day_abbreviation = reminder_type.split("_")[0].upper()  # e.g., "SUN" for "sun_recur"
            return f"{minute} {hour} * * {day_abbreviation}"
        return f"{minute} {hour} * * *"
    return None


def should_execute_reminder(reminder, current_time):
    """Check if the reminder should execute based on the current time."""
    reminder_parts = reminder.strip().split(" - ")
    reminder_type = reminder_parts[0]
    time_str = reminder_parts[1] if len(reminder_parts) > 1 else None

    if reminder_type == "every_minute":
        return True  # Run every minute

    if reminder_type == "every_hour" and current_time.minute == 0:
        return True  # Run at the top of every hour

    if reminder_type == "everyday" and time_str:
        reminder_time = datetime.datetime.strptime(time_str, "%I %p").time()
        return current_time.time().hour == reminder_time.hour and current_time.time().minute == reminder_time.minute

    if reminder_type == "one_time" and time_str:
        reminder_time = datetime.datetime.strptime(time_str, "%I %p").time()
        return current_time.time().hour == reminder_time.hour and current_time.time().minute == reminder_time.minute

    if reminder_type in ["mon", "tue", "wed", "thu", "fri", "sat", "sun"] and time_str:
        day_name = current_time.strftime("%a").lower()
        if reminder_type.startswith(day_name):
            reminder_time = datetime.datetime.strptime(time_str, "%I %p").time()
            return current_time.time().hour == reminder_time.hour and current_time.time().minute == reminder_time.minute

    if "recur" in reminder_type and time_str:
        day_name = reminder_type.split("_")[0]
        if day_name.startswith(current_time.strftime("%a").lower()):
            reminder_time = datetime.datetime.strptime(time_str, "%I %p").time()
            return current_time.time().hour == reminder_time.hour and current_time.time().minute == reminder_time.minute

    return False


def update_files(reminders, executed_reminders, cron_expressions):
    """Update reminders and cron schedule files."""
    # Update reminders.txt by removing executed reminders
    with open(REMINDER_FILE, "w") as file:
        file.writelines([r for r in reminders if r not in executed_reminders])

    # Update cron_schedule.txt with new cron expressions
    with open(CRON_FILE, "w") as file:
        for cron in cron_expressions:
            file.write(f"{cron}\n")


def main():
    reminders = load_reminders()
    executed_reminders = []
    cron_expressions = []
    current_time = get_current_time()

    for reminder in reminders:
        reminder_parts = reminder.strip().split(" - ")
        reminder_type = reminder_parts[0]
        time_str = reminder_parts[1] if len(reminder_parts) > 1 else None
        message = reminder_parts[-1] if len(reminder_parts) > 2 else "Reminder!"

        if should_execute_reminder(reminder, current_time):
            send_telegram_message(message)
            if "one_time" in reminder or "recur" not in reminder:
                executed_reminders.append(reminder)

        # Generate cron expressions for recurring reminders
        if "recur" in reminder or reminder_type in ["every_minute", "every_hour", "everyday"]:
            cron_expr = get_cron_expression(reminder_type, time_str)
            if cron_expr:
                cron_expressions.append(cron_expr)

    # Update files to reflect the changes
    update_files(reminders, executed_reminders, cron_expressions)


if __name__ == "__main__":
    main()
