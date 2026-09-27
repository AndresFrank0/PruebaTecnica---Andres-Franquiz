"""
Configuración de Django del proyecto `config` (API de inventario de librerías).

Generado con 'django-admin startproject' usando Django 5.2.17.
"""

import os
from pathlib import Path

# Rutas dentro del proyecto: BASE_DIR / 'subcarpeta'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Configuración pensada para desarrollo; no usar tal cual en producción.
# Los valores sensibles se leen de variables de entorno;
# los defaults solo sirven para desarrollo local.

# ADVERTENCIA DE SEGURIDAD: en producción, definir DJANGO_SECRET_KEY con una clave propia.
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-insecure-key-change-me')

# ADVERTENCIA DE SEGURIDAD: no dejar DEBUG activo en producción (usar DJANGO_DEBUG=0).
DEBUG = os.environ.get('DJANGO_DEBUG', '1') == '1'

# Hosts permitidos, separados por comas (ej. "api.midominio.com,localhost"); se ignoran los espacios
# y las entradas vacías.
ALLOWED_HOSTS = [
    host.strip() for host in os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',') if host.strip()
]


# Aplicaciones instaladas

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'books',  # Inventario de libros: modelo, endpoints y cálculo de precios
]

MIDDLEWARE = [
    # Va primero para que las cabeceras CORS se agreguen a todas las respuestas.
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Base de datos
# SQLite; en Docker, SQLITE_PATH apunta a un volumen para no perder los datos.

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.environ.get('SQLITE_PATH', BASE_DIR / 'db.sqlite3'),
    }
}


# Validación de contraseñas

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


# Internacionalización
# 'es': Django y DRF devuelven sus mensajes (p. ej. errores de validación) en español.

LANGUAGE_CODE = 'es'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Archivos estáticos (CSS, JavaScript, imágenes)

STATIC_URL = 'static/'

# Tipo de clave primaria por defecto

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# CORS: la SPA corre en otro origen (Vite en :5173 o nginx de Docker en :8080), abierta como
# localhost o como 127.0.0.1: para el navegador son orígenes distintos.
# Se puede sobrescribir con CORS_ALLOWED_ORIGINS, separando los orígenes con comas. Se ignoran los
# espacios y las entradas vacías: una coma final dejaría un '' que el system check de corsheaders rechaza.

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        'CORS_ALLOWED_ORIGINS',
        'http://localhost:5173,http://localhost:8080,http://127.0.0.1:5173,http://127.0.0.1:8080',
    ).split(',')
    if origin.strip()
]


# Django REST Framework

REST_FRAMEWORK = {
    # Paginación por número de página (?page=N) con 10 resultados por defecto. BookViewSet usa
    # BookPagination (books/views.py), que además acepta ?page_size=N hasta 50.
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    # Los Decimal se devuelven como números JSON (15.99) en vez de strings ("15.99").
    'COERCE_DECIMAL_TO_STRING': False,
    # La API es pública (el enunciado no pide autenticación). Sin esto, DRF intenta autenticar
    # cualquier cabecera Authorization (p. ej. la de un proxy con HTTP Basic) y responde 403.
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    # Solo JSON: un formulario HTML de otra web puede enviar urlencoded, multipart o text/plain sin
    # preflight CORS y, sin autenticación, no hay chequeo CSRF; aceptarlos permitiría crear libros
    # desde cualquier página. La SPA y Postman envían JSON. El resto recibe 415.
    'DEFAULT_PARSER_CLASSES': ['rest_framework.parsers.JSONParser'],
    # Errores de la API: 404 en español, 400 para peticiones que superan los límites de Django
    # y 500 en JSON (ver books/exceptions.py).
    'EXCEPTION_HANDLER': 'books.exceptions.json_exception_handler',
}
