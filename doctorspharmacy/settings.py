from pathlib import Path
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-dpu_f9^-4%z+7%4e5b73^=t268syd_ouhm78t%=frz*yp@n9v-"
)

DEBUG = False

ALLOWED_HOSTS = ["doctor-hospital.onrender.com", "localhost", "127.0.0.1"]

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

import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv()

import os

ENVIRONMENT = os.getenv("ENVIRONMENT", "local")

if ENVIRONMENT == "production":
    import dj_database_url
    DATABASES = {
        "default": dj_database_url.config(
            default=os.environ.get("DATABASE_URL"),
            conn_max_age=600,
            ssl_require=True
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }



STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")


AUTH_USER_MODEL = "pharmacy.User"

from decouple import config

AUTH_USER_MODEL = "pharmacy.User"


EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True


import os
from web3 import Web3

WEB3_PROVIDER_URI = os.getenv("WEB3_PROVIDER_URI")

web3 = None
if WEB3_PROVIDER_URI:
    web3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER_URI))
    print("Web3 enabled")
else:
    print("Web3 disabled")


import os

BNB_RECEIVER_ADDRESS = os.getenv("BNB_RECEIVER_ADDRESS")



DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
from decouple import config
BLOCKCHAIN_ENV = config("BLOCKCHAIN_ENV", default="LOCAL")

from decouple import config


BLOCKCHAIN_ENV = config("BLOCKCHAIN_ENV")
from decouple import config
from web3 import Web3

BLOCKCHAIN_ENV = config("BLOCKCHAIN_ENV", default="LOCAL")

if BLOCKCHAIN_ENV == "MAINNET":
    CHAIN_ID = int(config("CHAIN_ID", default=56))
    WEB3_RPC_URL = config("WEB3_RPC_URL", default=None)

    if not WEB3_RPC_URL:
        raise RuntimeError("WEB3_RPC_URL must be set in MAINNET mode")

else:
    CHAIN_ID = int(config("CHAIN_ID", default=31337))
    WEB3_RPC_URL = config(
        "LOCAL_WEB3_RPC_URL",
        default="http://127.0.0.1:8545"
    )

BNB_RECEIVER_ADDRESS = Web3.to_checksum_address(
    config("BNB_RECEIVER_ADDRESS")
)
