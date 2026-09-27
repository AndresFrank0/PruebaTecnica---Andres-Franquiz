# API de Django. Python 3.14: la versión con la que se desarrolló y probó.
FROM python:3.14-slim
# Sin archivos .pyc y con la salida sin búfer (los logs se ven al instante en `docker compose logs`).
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
# Primero las dependencias: la capa de pip se reutiliza mientras requirements.txt no cambie.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
# Docker detiene el contenedor con SIGINT (como Ctrl+C), que Python siempre atiende. Con el SIGTERM por
# defecto, un PID 1 sin handler ni siquiera lo recibe y Docker termina matándolo con SIGKILL. Límite:
# mientras corre migrate, el PID 1 todavía es sh, que espera al hijo; un stop en esos segundos acaba en
# SIGKILL, y la migración a medias se deshace porque en SQLite cada una corre en una transacción.
STOPSIGNAL SIGINT
# Aplica las migraciones y arranca el servidor de desarrollo de Django (en producción iría gunicorn).
# exec: runserver pasa a ser el PID 1 y recibe la señal. --noreload: el código va dentro de la imagen, así
# que el autoreloader no tendría nada que recargar y solo gastaría CPU revisando archivos.
CMD ["sh", "-c", "python manage.py migrate && exec python manage.py runserver --noreload 0.0.0.0:8000"]
# Sano cuando el 8000 acepta conexiones: runserver solo lo abre después de migrate (el && del CMD).
# `docker compose up --wait` espera a esto; sin él, un `loaddata` lanzado justo después de `up -d` puede
# correr antes que las migraciones. Conexión TCP y no un GET: un GET dejaría una línea en el log cada 5 s.
# Con Python porque la imagen slim no trae curl. Los fallos del primer minuto no cuentan (máquinas lentas).
HEALTHCHECK --interval=5s --start-period=60s CMD ["python", "-c", "import socket; socket.create_connection(('127.0.0.1', 8000), 2).close()"]
