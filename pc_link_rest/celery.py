import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pc_link_rest.settings')

app = Celery('pc_link_rest')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
