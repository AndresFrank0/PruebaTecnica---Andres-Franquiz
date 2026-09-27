import json
import logging
import urllib.request
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import APIException

logger = logging.getLogger(__name__)

CURRENCY = 'VES'
MARGIN_PERCENTAGE = 40
CENTS = Decimal('0.01')
# DolarAPI responde 403 al User-Agent por defecto de urllib ("Python-urllib/x.y").
USER_AGENT = 'bookstore-inventory-api/1.0'


class ExchangeRateUnavailable(APIException):
    status_code = 503
    default_detail = 'Servicio de tasas de cambio no disponible y no hay una tasa por defecto válida.'
    default_code = 'exchange_rate_unavailable'


def _parse_rate(value):
    """Tasa en Bs por 1 USD. ValueError si no es un número finito y mayor que 0."""
    try:
        rate = Decimal(str(value))
    except InvalidOperation:
        raise ValueError(f'Invalid exchange rate: {value!r}') from None
    if not rate.is_finite() or rate <= 0:
        raise ValueError(f'Invalid exchange rate: {value!r}')
    return rate


def fetch_live_rate():
    """Tasa oficial del BCV (Bs por 1 USD), del campo `promedio` de DolarAPI."""
    request = urllib.request.Request(settings.EXCHANGE_API_URL, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(request, timeout=5) as response:
        return _parse_rate(json.load(response)['promedio'])


def get_exchange_rate():
    """Devuelve (tasa, 'live' | 'default'); ExchangeRateUnavailable (503) si no hay ninguna usable."""
    try:
        return fetch_live_rate(), 'live'
    except Exception:  # red, timeout, error HTTP, JSON o tasa inválida: todo significa "sin tasa en vivo"
        logger.warning('Exchange API failed, falling back to default rate', exc_info=True)
    if settings.DEFAULT_EXCHANGE_RATE:
        try:
            return _parse_rate(settings.DEFAULT_EXCHANGE_RATE), 'default'
        except ValueError:
            # P. ej. "855,66" (coma decimal) o "0": mejor un 503 que un 500 o precios en cero.
            logger.error('DEFAULT_EXCHANGE_RATE is not a valid rate: %r', settings.DEFAULT_EXCHANGE_RATE)
    raise ExchangeRateUnavailable()


def calculate_price(book):
    """Calcula el precio de venta en Bs (costo × tasa × 1,40), lo guarda en el libro y devuelve el desglose."""
    rate, source = get_exchange_rate()
    # La consulta a la API puede tardar segundos: se relee el costo por si otra petición lo cambió.
    # Si en ese tiempo borraron el libro, lanza Book.DoesNotExist (la vista responde 404).
    book.refresh_from_db(fields=['cost_usd'])
    cost_local = (book.cost_usd * rate).quantize(CENTS, ROUND_HALF_UP)
    selling_price = (cost_local * (1 + Decimal(MARGIN_PERCENTAGE) / 100)).quantize(CENTS, ROUND_HALF_UP)

    book.selling_price_local = selling_price
    book.save(update_fields=['selling_price_local', 'updated_at'])

    return {
        'book_id': book.id,
        'cost_usd': book.cost_usd,
        'exchange_rate': rate,
        'cost_local': cost_local,
        'margin_percentage': MARGIN_PERCENTAGE,
        'selling_price_local': selling_price,
        'currency': CURRENCY,
        'rate_source': source,
        'calculation_timestamp': timezone.now(),
    }
