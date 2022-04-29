"""
PÇ-Link is a report creation software for MÜDEK.
Copyright (C) 2021  Tolga ÜSTÜNKÖK

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

"""
Django settings for pc_link_rest project.

Generated by 'django-admin startproject' using Django 3.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

from pathlib import Path
from dotenv import load_dotenv
from django.contrib.messages import constants as messages
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
ADMINS = [('Tolga Üstünkök', 'tolgaustunkok@gmail.com')]

ALLOWED_HOSTS = ['pc-link.atilim.edu.tr', '172.16.91.99']

if DEBUG == True:
    # Load environment variables from .env file.
    load_dotenv()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('PCLINK_SECRET_KEY')

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_filters',
    'crispy_forms',
    'coverage',
    'django_celery_results',
    'django_probes',
    'pc_calculator.apps.PcCalculatorConfig',
    'accounts.apps.AccountsConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'pc_link_rest.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'pc_link_rest.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('PCLINK_DB_NAME', 'pclink'),
        'USER': os.getenv('PCLINK_DB_USER', 'pclink'),
        'PASSWORD': os.getenv('PCLINK_DB_PASSWORD'),
        'HOST': os.getenv('PCLINK_DB_HOST'),
        'PORT': os.getenv('PCLINK_DB_PORT', '3306'),
        'OPTIONS': {
            'init_command': 'SET default_storage_engine=INNODB',
            'read_default_file': str(BASE_DIR / 'my.cnf'),
        },
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Istanbul'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

MAINTENANCE_MODE_IGNORE_ADMIN_SITE = True

STATIC_URL = 'static/'

MEDIA_URL = 'media/'

STATIC_ROOT = BASE_DIR / 'static'

MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

CRISPY_TEMPLATE_PACK = 'bootstrap4'

LOGIN_REDIRECT_URL = 'pc-calc:home'

if os.getenv('SCRIPT_NAME') is not None:
    LOGIN_URL = f'{os.getenv("SCRIPT_NAME")}/accounts/login/'
else:
    LOGIN_URL = '/accounts/login/'

AUTH_USER_MODEL = 'pc_calculator.User'

SERVER_EMAIL = os.getenv('PCLINK_EMAIL_ADDR') # 'pc-link@atilim.edu.tr'
EMAIL_HOST = os.getenv('PCLINK_EMAIL_HOST') # 'mail.atilim.edu.tr'
EMAIL_PORT = os.getenv('PCLINK_EMAIL_PORT') # 587
# with open(BASE_DIR / 'persist' / 'email_settings.txt', 'r') as f:
EMAIL_HOST_USER = os.getenv('PCLINK_EMAIL_USER') # f.readline().strip()
EMAIL_HOST_PASSWORD = os.getenv('PCLINK_EMAIL_PASSWORD') # f.readline().strip()
EMAIL_USE_TLS = bool(int(os.getenv('PCLINK_EMAIL_USE_TLS'))) # True
DEFAULT_FROM_EMAIL = os.getenv('PCLINK_EMAIL_ADDR') # 'pc-link@atilim.edu.tr'

DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
DBBACKUP_STORAGE_OPTIONS = {'location': BASE_DIR / 'backups'}
DBBACKUP_CLEANUP_KEEP = 1
DBBACKUP_CLEANUP_KEEP_MEDIA = 1
#DBBACKUP_GPG_RECIPIENT = ''

CELERY_RESULT_BACKEND = 'django-db'
# CELERY_TASK_SERIALIZER = 'pickle'
CELERY_RESULT_SERIALIZER = 'pickle'
CELERY_ACCEPT_CONTENT = ['application/x-python-serialize']
# CELERY_RESULT_ACCEPT_CONTENT = ['pickle']

MESSAGE_TAGS = {
    messages.ERROR: 'danger'
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime} {levelname}]  {message}',
            'datefmt': '%d/%b/%Y %H:%M:%S',
            'style': '{'
        },
        'original': {
            'format': '[{asctime}] {message}',
            'datefmt': '%d/%b/%Y %H:%M:%S',
            'style': '{'
        }
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'original'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'persist' / 'pc-link.log',
            'formatter': 'verbose',
            'maxBytes': 3146000,
            'backupCount': 5
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'pc_link_custom_logger': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': False
        }
    }
}
