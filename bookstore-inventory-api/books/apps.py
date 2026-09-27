from django.apps import AppConfig


class BooksConfig(AppConfig):
    """App del inventario de libros: modelo Book, API REST y cálculo de precios."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'books'
