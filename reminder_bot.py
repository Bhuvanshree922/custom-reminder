import datetime
import os
import pytz
import yaml
from telebot import TeleBot

# Constants
tz = pytz.timezone("Asia/Kolkata")
REMINDER_FILE = "reminders.txt"
ONE_TIME_CRON_FILE = "one_time_cron_schedule.txt"
RECURRING_CRON_FILE = "recurring_cron_schedule.txt"
GITHUB_ACTIONS_FILE = ".github/workflows/main.yml"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = TeleBot(TELEGRAM_TOKEN)

def load_reminders():
    with open(REMINDER_FILE, "r") as file:
        return file.readlines()

def get_cron_expression(reminder_type, time_str=None):
    if reminder_type == "every_hour":
        return "0 * * * *"
    if time_str:
        time_obj = datetime.datetime.strptime(time_str, "%I %p").replace(tzinfo=tz)
        return f"{time_obj.minute} {time_obj.hour} * * {reminder_type.split('_')[0].upper()}" if "recur" in reminder_type else f"{time_obj.minute} {time_obj.hour} * * *"
    return None

def update_cron_files(reminders):
    one_time_entries, recurring_entries = [], []
    for reminder in reminders:
        parts = reminder.strip().split(" - ")
        if len(parts) < 3:
            continue
        reminder_type, time_str, message = parts[0], parts[1], parts[2]
        cron_expr = get_cron_expression(reminder_type, time_str)
        if cron_expr:
            if "one_time" in reminder_type:
                one_time_entries.append(f"{cron_expr} = {message}")
            else:
                recurring_entries.append(f"{cron_expr} = {message}")
    
    with open(ONE_TIME_CRON_FILE, "w") as file:
        file.write("\n".join(one_time_entries))
    with open(RECURRING_CRON_FILE, "w") as file:
        file.write("\n".join(recurring_entries))

def update_github_actions():
    with open(GITHUB_ACTIONS_FILE, "r") as file:
        workflow = yaml.safe_load(file)
    
    with open(ONE_TIME_CRON_FILE, "r") as one_time, open(RECURRING_CRON_FILE, "r") as recurring:
        one_time_crons = [line.split(" = ")[0] for line in one_time.readlines()]
        recurring_crons = [line.split(" = ")[0] for line in recurring.readlines()]
    
    workflow['on']['schedule'] = [{'cron': '*/5 * * * *'}] + [{'cron': cron} for cron in one_time_crons + recurring_crons]
    
    with open(GITHUB_ACTIONS_FILE, "w") as file:
        yaml.dump(workflow, file, default_flow_style=False)
    
    os.system("git config --global user.name 'GitHub Actions'")
    os.system("git config --global user.email 'actions@github.com'")
    os.system("git add .")
    os.system("git commit -m 'Update GitHub Actions cron schedule'")
    os.system("git push")

def remove_executed_crons():
    open(ONE_TIME_CRON_FILE, "w").close()

def main():
    reminders = load_reminders()
    update_cron_files(reminders)
    update_github_actions()
    remove_executed_crons()

if __name__ == "__main__":
    main()
