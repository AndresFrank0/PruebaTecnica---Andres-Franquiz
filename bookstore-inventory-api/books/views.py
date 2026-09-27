from django.db import IntegrityError, transaction
from django.db.models import F
from django.db.models.functions import Lower
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.pagination import PageNumberPagination

from .models import Book
from .serializers import BookSerializer


class BookPagination(PageNumberPagination):
    """?page_size=N elige cuántos libros por página: 10 por defecto (PAGE_SIZE) y hasta 50."""

    page_size_query_param = 'page_size'
    max_page_size = 50


class StableOrderingFilter(OrderingFilter):
    """?ordering=campo (o -campo). Desempata por id: con valores repetidos (p. ej. la misma categoría),
    el orden entre páginas es estable y ningún libro se repite ni se salta."""

    # ponytail: Lower() ignora mayúsculas, pero en SQLite solo las ASCII, así que "Álgebra" queda después
    # de "Zorro". En Postgres ordena bien los acentos; en SQLite haría falta registrar una collation.
    CASE_INSENSITIVE = {'title', 'author', 'category'}

    def get_ordering(self, request, queryset, view):
        return [*(super().get_ordering(request, queryset, view) or []), 'id']

    def filter_queryset(self, request, queryset, view):
        return queryset.order_by(*map(self.expression, self.get_ordering(request, queryset, view)))

    def expression(self, field):
        # nulls_last: los libros sin precio calculado van al final en los dos sentidos (cada base de datos
        # los pone en un extremo distinto).
        name = field.removeprefix('-')
        expression = Lower(name) if name in self.CASE_INSENSITIVE else F(name)
        return expression.desc(nulls_last=True) if field.startswith('-') else expression.asc(nulls_last=True)


class BookViewSet(viewsets.ModelViewSet):
    """CRUD de libros: la lista va paginada y se puede ordenar por las columnas de la tabla de la SPA."""

    queryset = Book.objects.all()
    serializer_class = BookSerializer
    pagination_class = BookPagination
    filter_backends = [StableOrderingFilter]
    # Los campos no listados se ignoran (queda el orden por id).
    ordering_fields = ['title', 'author', 'isbn', 'category', 'stock_quantity', 'cost_usd', 'selling_price_local']

    def perform_create(self, serializer):
        self._save(serializer)

    def perform_update(self, serializer):
        self._save(serializer)

    @staticmethod
    def _save(serializer):
        """Guarda; si otra petición guardó el mismo ISBN entre la validación y el INSERT, responde 400."""
        try:
            # atomic: el IntegrityError no deja rota una transacción externa (ATOMIC_REQUESTS, tests).
            with transaction.atomic():
                serializer.save()
        except IntegrityError as exc:
            if 'isbn' not in str(exc):
                raise
            raise ValidationError({'isbn': ['Ya existe libro con este isbn.']}) from None

    def _paginated(self, queryset):
        """Responde con la misma forma paginada (y el mismo ?ordering) que GET /books."""
        page = self.paginate_queryset(self.filter_queryset(queryset))
        return self.get_paginated_response(self.get_serializer(page, many=True).data)

    @action(detail=False)
    def search(self, request):
        """GET /books/search?category=... (coincidencia parcial, sin distinguir mayúsculas)."""
        category = request.query_params.get('category', '').strip()
        if not category:
            raise ValidationError({'category': 'Este parámetro es obligatorio.'})
        return self._paginated(self.get_queryset().filter(category__icontains=category))

    @action(detail=False, url_path='low-stock')
    def low_stock(self, request):
        """GET /books/low-stock?threshold=10: libros con stock_quantity <= threshold."""
        try:
            threshold = int(request.query_params.get('threshold', 10))
        except ValueError:
            raise ValidationError({'threshold': 'Debe ser un número entero.'}) from None
        return self._paginated(self.get_queryset().filter(stock_quantity__lte=threshold))
