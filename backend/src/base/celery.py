from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Djangoのsettingsモジュールを設定
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'base.settings')

app = Celery('base')

# Djangoのsettingsから設定を読み込む
app.config_from_object('django.conf:settings', namespace='CELERY')

# アプリケーションのタスクを自動的に検出
app.autodiscover_tasks()
