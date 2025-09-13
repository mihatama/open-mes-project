from __future__ import absolute_import, unicode_literals

# Celeryアプリケーションをインポートして、Django起動時にロードされるようにする
from .celery import app as celery_app

__all__ = ('celery_app',)
