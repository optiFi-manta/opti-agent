import schedule
import time
import pytz
from src.rules import runner

utc = pytz.utc

def task_periodicly():
    print("Running...")
    runner()

schedule.every().day.at("07:00").do(task_periodicly)

while True:
    schedule.run_pending()
    time.sleep(1)
