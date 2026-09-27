import logging

from django.core.exceptions import SuspiciousOperation
from django.http import Http404
from rest_framework.exceptions import NotFound, ParseError
from rest_framework.response import Response
from rest_framework.views import exception_handler, set_rollback

logger = logging.getLogger(__name__)


def json_exception_handler(exc, context):
    """Manejador de errores de la API (REST_FRAMEWORK['EXCEPTION_HANDLER'])."""
    if isinstance(exc, Http404):
        # Django fija su mensaje en inglés ("No Book matches the given query."); DRF lo traduce.
        exc = NotFound()
    elif isinstance(exc, SuspiciousOperation):
        # La petición supera los límites de Django (demasiados campos o archivos, cuerpo muy grande).
        # Es un error del cliente: como Django, se registra en su logger de seguridad y se responde 400.
        logging.getLogger(f'django.security.{type(exc).__name__}').error(str(exc), exc_info=exc)
        exc = ParseError()
    response = exception_handler(exc, context)
    if response is None:
        # Error no controlado: se registra con su traceback y el cliente recibe un 500 en JSON,
        # no la página HTML de Django.
        logger.error('Unhandled API error', exc_info=exc)
        # La excepción ya no llega a Django: con ATOMIC_REQUESTS hay que marcar el rollback a mano,
        # como hace DRF con las excepciones que sí maneja.
        set_rollback()
        response = Response({'detail': 'Error interno del servidor.'}, status=500)
    return response
