"""
Bare minimum settings for collecting production assets.
"""
import json
from .common import *
from openedx.core.lib.derived import derive_settings

SERVICE_VARIANT = os.environ.get('SERVICE_VARIANT', None)
CONFIG_ROOT = path(os.environ.get('CONFIG_ROOT', ENV_ROOT))
CONFIG_PREFIX = SERVICE_VARIANT + "." if SERVICE_VARIANT else ""

with open(CONFIG_ROOT / CONFIG_PREFIX + "env.json") as env_file:
    ENV_TOKENS = json.load(env_file)
with open(CONFIG_ROOT / CONFIG_PREFIX + "auth.json") as auth_file:
    AUTH_TOKENS = json.load(auth_file)

# following setting is for backward compatibility
if ENV_TOKENS.get('COMPREHENSIVE_THEME_DIR', None):
    COMPREHENSIVE_THEME_DIR = ENV_TOKENS.get('COMPREHENSIVE_THEME_DIR')

COMPREHENSIVE_THEME_DIRS = ENV_TOKENS.get('COMPREHENSIVE_THEME_DIRS', COMPREHENSIVE_THEME_DIRS) or []
COMPREHENSIVE_THEME_LOCALE_PATHS = ENV_TOKENS.get('COMPREHENSIVE_THEME_LOCALE_PATHS', [])

DEFAULT_SITE_THEME = ENV_TOKENS.get('DEFAULT_SITE_THEME', DEFAULT_SITE_THEME)
ENABLE_COMPREHENSIVE_THEMING = ENV_TOKENS.get('ENABLE_COMPREHENSIVE_THEMING', ENABLE_COMPREHENSIVE_THEMING)

STATIC_ROOT_BASE = ENV_TOKENS.get('STATIC_ROOT_BASE', None)
if STATIC_ROOT_BASE:
    STATIC_ROOT = path(STATIC_ROOT_BASE)
    WEBPACK_LOADER['DEFAULT']['STATS_FILE'] = STATIC_ROOT / "webpack-stats.json"
    WEBPACK_LOADER['WORKERS']['STATS_FILE'] = STATIC_ROOT / "webpack-worker-stats.json"

SECRET_KEY = AUTH_TOKENS['SECRET_KEY']
XQUEUE_INTERFACE = {
    'django_auth': None,
    'url': None,
}
DATABASES = {
    "default": {},
}
derive_settings(__name__)