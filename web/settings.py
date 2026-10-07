from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "dev-only-neuro-draft"
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]

INSTALLED_APPS = ["django.contrib.staticfiles", "web"]
MIDDLEWARE = []
ROOT_URLCONF = "web.urls"
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "web" / "static"]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "web" / "templates"],
        "APP_DIRS": False,
        "OPTIONS": {},
    },
]
