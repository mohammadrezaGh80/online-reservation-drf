from celery import Celery
from kombu import Queue, Exchange
import os


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.task_queues = [
    Queue('tasks', Exchange('tasks'), routing_key='tasks', queue_arguments={'x-max-priority': 10})
]
app.conf.task_acks_late = True

app.autodiscover_tasks()
