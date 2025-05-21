from background_task import background
from django.utils import timezone
from datetime import timedelta
from .models import DummyEmailConfiguration

@background(schedule=60*60*24)  # Run once per day
def reset_daily_email_counters():
    print(f"Resetting daily email counters at {timezone.now()}")
    DummyEmailConfiguration.objects.all().update(daily_sent=0)

@background(schedule=10)
def my_daily_task():
    # Your task code here
    print("Running daily task")


#PowerShell command to run the task

# from background_task.models import Task
# from core.tasks import reset_daily_email_counters

# # Schedule the task to run immediately and then repeat daily
# reset_daily_email_counters(repeat=60*60*24, repeat_until=None) /or
# reset_daily_email_counters(repeat=Task.DAILY, repeat_until=None)

# python manage.py process_tasks