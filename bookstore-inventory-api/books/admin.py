from django.contrib import admin

from .models import Book


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'isbn', 'category', 'stock_quantity', 'cost_usd', 'selling_price_local')
    search_fields = ('title', 'author', 'isbn')
    list_filter = ('category',)
    # Lo calcula POST /books/{id}/calculate-price; no se edita a mano (igual que en la API).
    readonly_fields = ('selling_price_local',)
