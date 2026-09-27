from decimal import Decimal

from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

# El serializer normaliza el ISBN a solo dígitos antes de validar (ver serializers.py).
# [0-9] y no \d: en Python \d acepta dígitos de cualquier alfabeto ("９７８…", "٩٧٨…").
isbn_validator = RegexValidator(
    r'^([0-9]{9}[0-9X]|[0-9]{13})\Z', 'El ISBN debe tener 10 o 13 dígitos.'
)
country_validator = RegexValidator(
    r'^[A-Z]{2}$', 'Debe ser un código de país ISO de 2 letras (ej. ES).'
)


class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    isbn = models.CharField(max_length=13, unique=True, validators=[isbn_validator])
    cost_usd = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))]
    )
    # Bolívares: con 20 dígitos, el costo máximo (99.999.999,99 USD) × 1,40 cabe hasta con una
    # tasa de ~7.000 millones de Bs/USD. Con 14, SQLite guardaba el valor pero leerlo daba un 500.
    # Límite: SQLite guarda los decimales como REAL, así que los céntimos solo son exactos hasta
    # ~1 billón (1e12) de Bs. Si hiciera falta más, usar Postgres (numeric es exacto).
    selling_price_local = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    # Sin índice: la búsqueda es icontains (LIKE '%x%'), que no puede usarlo.
    category = models.CharField(max_length=100)
    supplier_country = models.CharField(max_length=2, validators=[country_validator])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']
        verbose_name = 'libro'

    def __str__(self):
        return self.title
