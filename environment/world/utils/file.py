import os
from django.conf import settings
from .arguments import load_dict


def static_root():
    return settings.STATICFILES_DIRS[0]


def load_static(path):
    return load_dict(os.path.join(static_root(), path))
