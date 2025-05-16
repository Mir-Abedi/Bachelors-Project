import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'persian_name_finder.settings')

app = Celery('persian_name_finder')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()