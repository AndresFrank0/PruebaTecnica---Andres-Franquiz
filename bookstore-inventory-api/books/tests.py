import json
import os
import re
from decimal import Decimal
from unittest.mock import patch
from urllib.parse import urlencode

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APITestCase
from rest_framework.validators import UniqueValidator

from .models import Book
from .serializers import BookSerializer

VALID = {
    'title': 'El Quijote',
    'author': 'Miguel de Cervantes',
    'isbn': '978-84-376-0494-7',
    'cost_usd': 15.99,
    'stock_quantity': 25,
    'category': 'Literatura Clásica',
    'supplier_country': 'ES',
}


def make_book(**overrides):
    """Crea un libro directamente en la BD (sin pasar por el serializer)."""
    return Book.objects.create(**{**VALID, 'isbn': '9788437604947', **overrides})


class BookSerializerTests(TestCase):
    def errors_for(self, **overrides):
        serializer = BookSerializer(data={**VALID, **overrides})
        self.assertFalse(serializer.is_valid())
        return serializer.errors

    def test_valid_book_normalizes_isbn(self):
        serializer = BookSerializer(data=VALID)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data['isbn'], '9788437604947')

    def test_cost_must_be_greater_than_zero(self):
        for cost in (0, -5):
            self.assertIn('cost_usd', self.errors_for(cost_usd=cost))

    def test_stock_cannot_be_negative(self):
        self.assertIn('stock_quantity', self.errors_for(stock_quantity=-1))

    def test_isbn_must_have_10_or_13_digits(self):
        for bad in ('123', '978-84-376-0494', 'abcdefghij', '12345678901234'):
            self.assertIn('isbn', self.errors_for(isbn=bad), bad)
        for good in ('0-306-40615-2', '123456789X'):
            self.assertTrue(BookSerializer(data={**VALID, 'isbn': good}).is_valid(), good)

    def test_duplicate_isbn_rejected_even_with_different_format(self):
        make_book()
        self.assertIn('isbn', self.errors_for(isbn='97-884-376-04947'))

    def test_supplier_country_must_be_iso2(self):
        self.assertIn('supplier_country', self.errors_for(supplier_country='ESP'))

    def test_isbn_uppercases_check_digit_x(self):
        serializer = BookSerializer(data={**VALID, 'isbn': '123456789x'})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data['isbn'], '123456789X')

    def test_isbn_accepts_unicode_dashes(self):
        # Word y los PDF convierten "-" en "–", "—" o "‑" al copiar el ISBN.
        serializer = BookSerializer(data={**VALID, 'isbn': '978–84—376‑0494−7'})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data['isbn'], '9788437604947')

    def test_isbn_rejects_non_ascii_digits(self):
        # "\d" de Python acepta dígitos de cualquier alfabeto: "９７８…" no chocaría con "978…".
        for isbn in ('９７８８４３７６０４９４７', '٩٧٨٨٤٣٧٦٠٤٩٤٧'):
            self.assertEqual(self.errors_for(isbn=isbn)['isbn'], ['El ISBN debe tener 10 o 13 dígitos.'])


class BookApiTests(APITestCase):
    def test_create_returns_201_without_selling_price(self):
        r = self.client.post('/books', VALID, format='json')
        self.assertEqual(r.status_code, 201)
        self.assertIsNone(r.data['selling_price_local'])
        self.assertEqual(r.data['cost_usd'], Decimal('15.99'))

    def test_create_invalid_returns_400_with_field_errors(self):
        r = self.client.post('/books', {**VALID, 'cost_usd': 0, 'isbn': '123'}, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertIn('cost_usd', r.data)
        self.assertIn('isbn', r.data)

    def test_list_is_paginated(self):
        for i in range(12):
            make_book(isbn=f'{i:013d}')
        r = self.client.get('/books')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['count'], 12)
        self.assertEqual(len(r.data['results']), 10)
        self.assertIsNotNone(r.data['next'])

    def test_retrieve_existing_and_missing(self):
        book = make_book()
        self.assertEqual(self.client.get(f'/books/{book.id}').data['title'], 'El Quijote')
        r = self.client.get('/books/9999')
        self.assertEqual(r.status_code, 404)
        # Django fija su mensaje en inglés ("No Book matches the given query.").
        self.assertEqual(r.data['detail'], 'No encontrado.')

    def test_response_has_exactly_the_book_fields(self):
        r = self.client.get(f'/books/{make_book().id}')
        self.assertEqual(set(r.data), {
            'id', 'title', 'author', 'isbn', 'cost_usd', 'selling_price_local', 'stock_quantity',
            'category', 'supplier_country', 'created_at', 'updated_at',
        })

    def test_update_with_another_books_isbn_returns_400(self):
        make_book()
        other = make_book(isbn='0306406152')
        r = self.client.put(f'/books/{other.id}', VALID, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertIn('isbn', r.data)

    def test_duplicate_isbn_race_returns_400(self):
        # Simula la carrera: otra petición guarda el mismo ISBN entre la validación y el INSERT.
        make_book()
        with patch.object(UniqueValidator, '__call__', return_value=None):
            r = self.client.post('/books', VALID, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertIn('isbn', r.data)
        # La transacción sigue usable (sin el atomic() de _save, esta consulta fallaría) y no hay duplicado.
        self.assertEqual(Book.objects.count(), 1)

    def test_other_integrity_errors_are_not_reported_as_isbn(self):
        # Solo el choque de ISBN se convierte en 400; cualquier otro IntegrityError sigue siendo un 500.
        error = IntegrityError('CHECK constraint failed: stock_quantity')
        with patch.object(Book, 'save', side_effect=error), self.assertLogs('books.exceptions', 'ERROR'):
            r = self.client.post('/books', VALID, format='json')
        self.assertEqual(r.status_code, 500)

    def test_only_json_bodies_are_accepted(self):
        # Un formulario HTML de otra web puede enviar estos tres tipos sin preflight CORS, y sin
        # autenticación no hay chequeo CSRF: si la API los aceptara, cualquier página crearía libros.
        # Un ISBN distinto en cada uno: sin la corrección, fallarían por aceptarse y no por duplicados.
        big = SimpleUploadedFile('big.bin', b'0' * (3 * 1024 * 1024))  # más de 2,5 MB (Task 1.4)
        responses = {
            'multipart': self.client.post('/books', {**VALID, 'junk': big}, format='multipart'),
            'urlencoded': self.client.post(
                '/books', urlencode({**VALID, 'isbn': '9780306406157'}),
                content_type='application/x-www-form-urlencoded',
            ),
            'text/plain': self.client.post(
                '/books', json.dumps({**VALID, 'isbn': '9780262033848'}), content_type='text/plain',
            ),
        }
        for name, response in responses.items():
            with self.subTest(name):
                self.assertEqual(response.status_code, 415)
        self.assertFalse(Book.objects.exists())

    def test_foreign_basic_auth_header_is_ignored(self):
        # P. ej. un nginx con HTTP Basic delante: la API es pública y no debe responder 403.
        r = self.client.get('/books', HTTP_AUTHORIZATION='Basic dTpw')  # "u:p"
        self.assertEqual(r.status_code, 200)

    def test_spa_origins_pass_cors(self):
        # La SPA se abre con localhost o con 127.0.0.1, en Vite (:5173) o en Docker (:8080). Si el origen
        # no está en la lista, el navegador bloquea la respuesta y la SPA dice "No se pudieron cargar los
        # libros." aunque la API funcione.
        if 'CORS_ALLOWED_ORIGINS' in os.environ:  # como settings.py: definida, aunque esté vacía
            self.skipTest('CORS_ALLOWED_ORIGINS del entorno reemplaza la lista por defecto que se prueba aquí')
        for origin in ('http://localhost:5173', 'http://localhost:8080',
                       'http://127.0.0.1:5173', 'http://127.0.0.1:8080'):
            with self.subTest(origin):
                r = self.client.get('/books', HTTP_ORIGIN=origin)
                self.assertEqual(r.headers.get('Access-Control-Allow-Origin'), origin)

    def test_large_selling_price_can_be_read(self):
        # Costo máximo (99.999.999,99 USD) × 1,40 con una tasa de ~8.557 Bs/USD: no cabía en 14 dígitos.
        book = make_book(cost_usd=Decimal('99999999.99'))
        Book.objects.filter(pk=book.pk).update(selling_price_local=Decimal('1197930000000.00'))
        r = self.client.get(f'/books/{book.id}')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['selling_price_local'], Decimal('1197930000000.00'))

    def test_update_ignores_selling_price(self):
        book = make_book()
        payload = {**VALID, 'stock_quantity': 3, 'selling_price_local': 999}
        r = self.client.put(f'/books/{book.id}', payload, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['stock_quantity'], 3)
        self.assertIsNone(r.data['selling_price_local'])

    def test_changing_cost_clears_selling_price(self):
        # El precio de venta guardado se calculó con el costo anterior: al cambiarlo deja de valer.
        book = make_book(selling_price_local=Decimal('19154.86'))
        r = self.client.put(f'/books/{book.id}', {**VALID, 'stock_quantity': 3}, format='json')
        self.assertEqual(r.data['selling_price_local'], Decimal('19154.86'))  # mismo costo: se conserva
        r = self.client.put(f'/books/{book.id}', {**VALID, 'cost_usd': 30}, format='json')
        self.assertIsNone(r.data['selling_price_local'])

    def test_too_many_fields_returns_400(self):
        # Más de DATA_UPLOAD_MAX_NUMBER_FIELDS (1000): Django lo trata como error del cliente y lo
        # registra en su logger de seguridad. No es un error del servidor. Van en la query string:
        # un cuerpo que no es JSON se rechaza con 415 antes de llegar a parsearse.
        with self.assertLogs('django.security', 'ERROR'):
            r = self.client.get('/books', {f'f{i}': 'x' for i in range(1001)})
        self.assertEqual(r.status_code, 400)

    def test_unexpected_error_rolls_back_with_atomic_requests(self):
        # Con ATOMIC_REQUESTS, convertir el error en un 500 no debe dejar guardado lo que la vista
        # escribió antes de fallar (aquí el libro se guarda y falla al serializar la respuesta).
        with patch.dict(connection.settings_dict, {'ATOMIC_REQUESTS': True}), \
                patch.object(BookSerializer, 'to_representation', side_effect=RuntimeError('boom')), \
                self.assertLogs('books.exceptions', 'ERROR'):
            r = self.client.post('/books', VALID, format='json')
        self.assertEqual(r.status_code, 500)
        self.assertFalse(Book.objects.exists())

    def test_delete(self):
        book = make_book()
        self.assertEqual(self.client.delete(f'/books/{book.id}').status_code, 204)
        self.assertFalse(Book.objects.exists())


class BookFilterTests(APITestCase):
    def setUp(self):
        self.quijote = make_book()  # "Literatura Clásica", stock 25
        self.low = make_book(isbn='0306406152', title='Cosmos', category='Ciencia', stock_quantity=2)

    def test_search_by_category_is_partial_and_case_insensitive(self):
        r = self.client.get('/books/search', {'category': 'literatura'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual([b['id'] for b in r.data['results']], [self.quijote.id])

    def test_search_requires_category(self):
        self.assertEqual(self.client.get('/books/search').status_code, 400)

    def test_search_rejects_blank_category(self):
        self.assertEqual(self.client.get('/books/search', {'category': '   '}).status_code, 400)

    def test_low_stock_uses_threshold(self):
        r = self.client.get('/books/low-stock', {'threshold': 10})
        self.assertEqual([b['id'] for b in r.data['results']], [self.low.id])
        self.assertEqual(self.client.get('/books/low-stock', {'threshold': 30}).data['count'], 2)

    def test_low_stock_default_threshold_includes_stock_equal_to_10(self):
        edge = make_book(isbn='1234567890', stock_quantity=10)
        r = self.client.get('/books/low-stock')
        self.assertEqual([b['id'] for b in r.data['results']], [self.low.id, edge.id])

    def test_low_stock_rejects_non_integer_threshold(self):
        self.assertEqual(self.client.get('/books/low-stock', {'threshold': 'abc'}).status_code, 400)


class BookOrderingAndPageSizeTests(APITestCase):
    """?ordering=campo|-campo y ?page_size=N en la lista, search y low-stock (los usa la tabla de la SPA)."""

    def ids(self, path, **params):
        r = self.client.get(path, params)
        self.assertEqual(r.status_code, 200)
        return [b['id'] for b in r.data['results']]

    def test_orders_by_each_table_column_both_ways(self):
        a = make_book(isbn='0000000001', title='A', author='C', category='B', stock_quantity=3, cost_usd=2)
        b = make_book(isbn='0000000002', title='B', author='A', category='C', stock_quantity=1, cost_usd=3)
        c = make_book(isbn='0000000003', title='C', author='B', category='A', stock_quantity=2, cost_usd=1)
        Book.objects.filter(pk=b.pk).update(selling_price_local=Decimal('5'))
        Book.objects.filter(pk=c.pk).update(selling_price_local=Decimal('9'))
        expected = {
            'title': [a, b, c], 'author': [b, c, a], 'isbn': [a, b, c], 'category': [c, a, b],
            'stock_quantity': [b, c, a], 'cost_usd': [c, a, b],
        }
        for field, books in expected.items():
            with self.subTest(field=field):
                self.assertEqual(self.ids('/books', ordering=field), [x.id for x in books])
                self.assertEqual(self.ids('/books', ordering=f'-{field}'), [x.id for x in reversed(books)])
        # Sin precio (null) va al final en los dos sentidos.
        self.assertEqual(self.ids('/books', ordering='selling_price_local'), [b.id, c.id, a.id])
        self.assertEqual(self.ids('/books', ordering='-selling_price_local'), [c.id, b.id, a.id])

    def test_text_columns_ignore_case(self):
        # En binario (ASCII) "B" < "C" < "a": sin Lower(), "a" iría al final.
        upper_b = make_book(isbn='0000000001', title='B', author='B', category='B')
        lower_a = make_book(isbn='0000000002', title='a', author='a', category='a')
        upper_c = make_book(isbn='0000000003', title='C', author='C', category='C')
        for field in ('title', 'author', 'category'):
            with self.subTest(field=field):
                self.assertEqual(self.ids('/books', ordering=field), [lower_a.id, upper_b.id, upper_c.id])

    def test_ties_break_by_id_so_pages_do_not_repeat_books(self):
        # SQLite devuelve los empates en orden de id aunque falte el desempate: se comprueba el SQL.
        make_book(category='Igual')
        with CaptureQueriesContext(connection) as queries:
            self.ids('/books', ordering='-category')
        self.assertTrue(any(re.search(r'ORDER BY .+, "books_book"\."id" ASC', q['sql']) for q in queries), queries)

    def test_unknown_ordering_field_keeps_default_order(self):
        first, second = make_book(isbn='0000000001', title='Z'), make_book(isbn='0000000002', title='A')
        self.assertEqual(self.ids('/books', ordering='supplier_country'), [first.id, second.id])
        self.assertEqual(self.ids('/books', ordering='nope'), [first.id, second.id])

    def test_search_and_low_stock_accept_ordering_and_page_size(self):
        make_book(isbn='0000000001', title='A', category='Ciencia', stock_quantity=1)
        b = make_book(isbn='0000000002', title='B', category='Ciencia', stock_quantity=2)
        self.assertEqual(self.ids('/books/search', category='ciencia', ordering='-title', page_size=1), [b.id])
        self.assertEqual(self.ids('/books/low-stock', ordering='-stock_quantity', page_size=1), [b.id])

    def test_page_size_defaults_to_10_and_is_capped_at_50(self):
        Book.objects.bulk_create(Book(**{**VALID, 'isbn': f'{i:013d}'}) for i in range(55))
        self.assertEqual(len(self.ids('/books')), 10)
        self.assertEqual(len(self.ids('/books', page_size=30)), 30)
        self.assertEqual(len(self.ids('/books', page_size=100)), 50)
        self.assertEqual(len(self.ids('/books', page_size='abc')), 10)


class BookAdminTests(TestCase):
    def setUp(self):
        self.client.force_login(User.objects.create_superuser('admin', 'admin@example.com', None))

    def test_admin_cannot_edit_selling_price(self):
        book = make_book()
        data = {**VALID, 'isbn': '9788437604947', 'selling_price_local': '999'}
        self.assertEqual(self.client.post(f'/admin/books/book/{book.id}/change/', data).status_code, 302)
        book.refresh_from_db()
        self.assertIsNone(book.selling_price_local)

    def test_admin_search_by_title(self):
        make_book()
        make_book(isbn='0306406152', title='Cosmos')
        r = self.client.get('/admin/books/book/', {'q': 'Cosmos'})
        self.assertContains(r, 'Cosmos')
        self.assertNotContains(r, 'El Quijote')
