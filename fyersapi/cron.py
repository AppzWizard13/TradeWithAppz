# from django_cron import CronJobBase, Schedule
# from datetime import datetime

# class MyCronJob(CronJobBase):
#     # RUN_AT_TIMES = ['10:32']
#     RUN_EVERY_MINS = 1

#     schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
#     code = 'fyersapi.my_cron_job'  # a unique code

#     def do(self):
#         # Your task here
#         print(f'Cron job running at {datetime.now()}')
#         print('***********************************************************************************************')
#         # For example, sending an email, updating database, etc.

