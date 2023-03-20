# You should start your standalone scripts with this:
from __future__ import annotations

from django.conf import settings

assert settings.SECRET_KEY == 'a'
