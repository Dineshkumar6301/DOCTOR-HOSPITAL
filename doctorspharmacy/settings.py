from pathlib import Path
import os
from dotenv import load_dotenv
from web3 import Web3
from decouple import config

# --------------------------------------------------
# BASE SETTINGS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv()

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")

DEBUG = False

ALLOWED_HOSTS = [
    "doctor-hospital-09tj.onrender.com",
    "localhost",
    "127.0.0.1",
]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# --------------------------------------------------
# APPLICATIONS
# --------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "pharmacy",
    "widget_tweaks",

    "whitenoise.runserver_nostatic",
]

# --------------------------------------------------
# MIDDLEWARE
# --------------------------------------------------
CSRF_TRUSTED_ORIGINS = [
    "https://doctor-hospital-09tj.onrender.com"
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",

    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",

    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "doctorspharmacy.urls"

# --------------------------------------------------
# TEMPLATES
# --------------------------------------------------

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "doctorspharmacy.wsgi.application"

# --------------------------------------------------
# DATABASE (Render PostgreSQL)
# --------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# --------------------------------------------------
# STATIC FILES
# --------------------------------------------------

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# --------------------------------------------------
# MEDIA FILES
# --------------------------------------------------

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# --------------------------------------------------
# AUTH USER MODEL
# --------------------------------------------------

AUTH_USER_MODEL = "pharmacy.User"

# --------------------------------------------------
# EMAIL SETTINGS
# --------------------------------------------------

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# --------------------------------------------------
# LANGUAGE & TIME
# --------------------------------------------------

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True
USE_TZ = True

# --------------------------------------------------
# BLOCKCHAIN / WEB3
# --------------------------------------------------

BLOCKCHAIN_ENV = config("BLOCKCHAIN_ENV", default="LOCAL")

WEB3_PROVIDER_URI = os.getenv("WEB3_PROVIDER_URI")

web3 = None

if WEB3_PROVIDER_URI:
    web3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER_URI))
    print("Web3 enabled")
else:
    print("Web3 disabled")

# Chain configuration
if BLOCKCHAIN_ENV == "MAINNET":
    CHAIN_ID = int(config("CHAIN_ID", default=56))
    WEB3_RPC_URL = config(
        "WEB3_RPC_URL",
        default="https://bsc-dataseed.binance.org"
    )
else:
    CHAIN_ID = int(config("CHAIN_ID", default=31337))
    WEB3_RPC_URL = config(
        "LOCAL_WEB3_RPC_URL",
        default="http://127.0.0.1:8545"
    )

# Wallet address
bnb_address = config("BNB_RECEIVER_ADDRESS", default=None)

if bnb_address:
    BNB_RECEIVER_ADDRESS = Web3.to_checksum_address(bnb_address)
else:
    BNB_RECEIVER_ADDRESS = None

# --------------------------------------------------
# DEFAULT FIELD
# --------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"