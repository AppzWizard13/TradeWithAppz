# # tasks.py

# from celery import Celery
# from .models import DailyTaskData

# app = Celery('tasks', broker='redis://localhost')

# @app.task
# def daily_task():
  
#   # Get current date
#   date = datetime.datetime.now().date()  

#   # Store data to Django model
#   DailyTaskData.objects.create(
#     date=date,
#     # any other fields    
#   )

#   # Task logic here
#   #print(f"Running daily task at {datetime.datetime.now()}")

# # celerybeat_schedule in settings.py

# CELERYBEAT_SCHEDULE = {
#   'daily-task': {
#     'task': 'tasks.daily_task',
#     'schedule': crontab(minute=15, hour=3), 
#   }
# }
