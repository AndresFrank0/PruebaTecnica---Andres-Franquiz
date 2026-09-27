import copy
import re

from rest_framework import serializers

from .models import Book

# Espacios y guiones, incluidos los Unicode (‐ ‑ ‒ – — ― −) que meten Word y los PDF al copiar.
ISBN_SEPARATORS = re.compile(r'[\s\u2010-\u2015\u2212-]')


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        # Lista explícita: un campo nuevo del modelo no se expone en la API sin decidirlo.
        fields = [
            'id', 'title', 'author', 'isbn', 'cost_usd', 'selling_price_local', 'stock_quantity',
            'category', 'supplier_country', 'created_at', 'updated_at',
        ]
        read_only_fields = ['selling_price_local', 'created_at', 'updated_at']

    def to_internal_value(self, data):
        # Se normaliza antes de los validadores del campo, así la validación de unicidad
        # trata "978-84-..." y "97884..." como el mismo ISBN.
        if isinstance(data, dict) and isinstance(data.get('isbn'), str):
            # Copia superficial: QueryDict.copy() hace deepcopy, y los archivos subidos grandes
            # (TemporaryUploadedFile) no se pueden copiar así: daba un 500.
            data = copy.copy(data)
            data['isbn'] = ISBN_SEPARATORS.sub('', data['isbn']).upper()
        return super().to_internal_value(data)

    def update(self, instance, validated_data):
        # El precio de venta guardado se calculó con el costo anterior: si el costo cambia, deja de valer.
        if validated_data.get('cost_usd', instance.cost_usd) != instance.cost_usd:
            validated_data['selling_price_local'] = None
        return super().update(instance, validated_data)
