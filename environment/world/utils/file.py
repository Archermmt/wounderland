import os
from django.conf import settings


def static_path(path: str):
    return os.path.join(settings.STATICFILES_DIRS[0], path)
