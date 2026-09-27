# Bookstore Inventory API — Prueba Técnica Nextep (Full Stack)

API REST (Django + DRF) para gestionar el inventario de una cadena de librerías. Calcula el precio de venta sugerido en **bolívares** con la tasa oficial del BCV en tiempo real. Incluye una SPA en React que consume todos los endpoints.

## Stack
- **Backend** (`bookstore-inventory-api/`): Python 3.12+, Django 5.2, Django REST Framework, SQLite
- **Frontend** (`frontend/`): React + TypeScript (Vite), TanStack Query, Pico CSS, Sonner
- **Tasa de cambio:** oficial del BCV vía [DolarAPI](https://ve.dolarapi.com) (`/v1/dolares/oficial`)
- **Infra (opcional):** Docker + Docker Compose

## Requisitos previos
- Python 3.12 o superior, con pip (en Debian/Ubuntu, también el paquete `python3-venv`)
- Node.js 20.19+ (o 22.12+), con npm
- Opcional: Docker Desktop

## Ejecución con Docker
```bash
docker compose up --build --wait
docker compose exec backend python manage.py loaddata sample_books   # datos de ejemplo (opcional)
```
- Los contenedores quedan en segundo plano, como con `-d`. `--wait` devuelve el control cuando la API ya está escuchando (después de aplicar las migraciones), así que el `loaddata` encuentra las tablas. Si falla, el error está en `docker compose logs backend`.
- SPA: http://localhost:8080
- API: http://localhost:8000/books
- Los puertos se publican solo en `127.0.0.1`: la app se usa desde el mismo equipo.
- Si otro programa ocupa el 8000 o el 8080, `docker compose up` falla con "ports are not available". Detenlo o cambia el puerto en `docker-compose.yml`; si cambias el del frontend, añade su origen a `CORS_ALLOWED_ORIGINS`.
- `docker compose down` conserva los datos (volumen `db-data`); `docker compose down -v` los borra.
- Para probar la tasa por defecto, añade `EXCHANGE_API_URL: http://127.0.0.1:9/` al `environment` del backend. Para el 503, añade además `DEFAULT_EXCHANGE_RATE: ""`.

## Ejecución local
### Backend
```bash
cd bookstore-inventory-api
python -m venv .venv                     # Linux/macOS: python3 · Windows sin python en el PATH: py
source .venv/bin/activate                # Windows: .venv\Scripts\activate (Git Bash: source .venv/Scripts/activate)
pip install -r requirements.txt
python manage.py migrate
python manage.py loaddata sample_books   # opcional: 12 libros de ejemplo
python manage.py runserver               # http://localhost:8000
```
Si PowerShell no deja cargar `Activate.ps1` porque la ejecución de scripts está deshabilitada, habilítala solo para esa terminal con `Set-ExecutionPolicy -Scope Process RemoteSigned -Force`.
### Frontend
En otra terminal, desde la raíz del repo (`runserver` sigue ocupando la primera):
```bash
cd frontend
npm install
npm run dev                              # http://localhost:5173
```
El frontend apunta a `http://localhost:8000` por defecto. Para cambiarlo, crea `frontend/.env` a partir de `.env.example`.

### Tests
Con el entorno virtual activado (en una terminal nueva, activarlo otra vez):
```bash
cd bookstore-inventory-api && python manage.py test books
```

## Variables de entorno (backend)
| Variable | Default | Descripción |
|---|---|---|
| `EXCHANGE_API_URL` | `https://ve.dolarapi.com/v1/dolares/oficial` | Endpoint de la tasa oficial BCV (se lee el campo `promedio`, en Bs por 1 USD) |
| `DEFAULT_EXCHANGE_RATE` | `855.6625` | Tasa (Bs/USD) que se usa si la API falla. Si se deja vacía, el endpoint responde 503 |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173`, `http://localhost:8080` y los mismos con `127.0.0.1` | Orígenes permitidos para la SPA, separados por comas |
| `DJANGO_DEBUG` / `DJANGO_SECRET_KEY` / `DJANGO_ALLOWED_HOSTS` | `1` / dev key / `*` | Configuración de Django |
| `SQLITE_PATH` | `bookstore-inventory-api/db.sqlite3` | Ruta de la base de datos |

## Endpoints
| Método | Ruta | Descripción |
|---|---|---|
| POST | `/books` | Crear libro |
| GET | `/books?page=N` | Listar (paginado, 10 por página por defecto) |
| GET | `/books/{id}` | Obtener por ID |
| PUT | `/books/{id}` | Actualizar |
| DELETE | `/books/{id}` | Eliminar |
| GET | `/books/search?category=X` | Buscar por categoría (parcial, sin distinguir mayúsculas; paginado) |
| GET | `/books/low-stock?threshold=10` | Libros con `stock_quantity <= threshold` (paginado) |
| POST | `/books/{id}/calculate-price` | Calcula y guarda el precio de venta sugerido en Bs. |

Las rutas van sin barra final, como en el enunciado: `/books/` da 404.

La lista, search y low-stock aceptan además:
- `page_size=N`: libros por página (10 por defecto, máximo 50).
- `ordering=campo` (o `-campo` para descendente) con `title`, `author`, `isbn`, `category`, `stock_quantity`, `cost_usd` o `selling_price_local`. Los textos se ordenan sin distinguir mayúsculas, los libros sin precio van al final en los dos sentidos y los empates se ordenan por `id`, así ningún libro se repite ni se salta entre páginas. Con SQLite, como en la búsqueda, un texto que empieza con acento (`Álgebra`) va después de la Z; en Postgres los acentos se ordenan bien.

Códigos de error: `400` validación · `404` no existe · `500` error interno (JSON) · `503` API de cambio caída y sin tasa por defecto.

## Ejemplos
Para bash (Linux, macOS o Git Bash) y PowerShell 7.3 o posterior. En cmd y en Windows PowerShell 5.1, el POST con JSON no funciona (se pierden las comillas del cuerpo); los demás sí, escribiendo `curl.exe` en la 5.1, donde `curl` es un alias de `Invoke-WebRequest`.
```bash
curl -X POST localhost:8000/books -H "Content-Type: application/json" -d '{
  "title": "Ficciones", "author": "Jorge Luis Borges", "isbn": "978-0-306-40615-7",
  "cost_usd": 13.50, "stock_quantity": 4, "category": "Literatura Latinoamericana", "supplier_country": "AR"}'

curl "localhost:8000/books/search?category=literatura"
curl "localhost:8000/books/low-stock?threshold=10"
curl -X POST localhost:8000/books/1/calculate-price
```
Respuesta de `calculate-price` para el libro 1 de los datos de ejemplo (El Quijote, 15,99 USD), con la tasa BCV del 25/09/2026:
```json
{
  "book_id": 1, "cost_usd": 15.99, "exchange_rate": 855.6625, "cost_local": 13682.04,
  "margin_percentage": 40, "selling_price_local": 19154.86, "currency": "VES",
  "rate_source": "live", "calculation_timestamp": "2026-09-25T14:30:00.447882Z"
}
```

## Postman
Importa `postman/bookstore-inventory.postman_collection.json` y ejecútala en orden con el Runner: crea su propio libro, recorre los 8 endpoints (también la lista ordenada con `ordering` y `page_size`) y los casos de error (400, 404, 415) y al final lo borra, así que no depende de los datos de ejemplo y se puede repetir. La variable `baseUrl` apunta por defecto a `http://localhost:8000` (runserver o Docker).

## Decisiones de diseño
- **Moneda local: bolívares (VES).** La tasa es la oficial del BCV y se obtiene de DolarAPI (campo `promedio`). El enunciado sugiere exchangerate-api, pero su tasa para `VES` tiene 2 decimales y no siempre coincide con la oficial (el 26/09/2026 daba 857,01 y DolarAPI 855,6625). DolarAPI da la del BCV con 4 decimales.
- **User-Agent propio:** DolarAPI rechaza (403) el User-Agent por defecto de Python, así que el backend manda `bookstore-inventory-api/1.0`.
- **Tasa por defecto:** si la API falla (timeout de 5 s por operación de red, error de red o HTTP, o respuesta inválida), se usa `DEFAULT_EXCHANGE_RATE` y la respuesta lo indica con `rate_source: "default"`.
- **ISBN:** se guarda sin espacios ni guiones (también los Unicode que meten Word o los PDF al copiar) para detectar duplicados aunque cambie el formato. Solo se aceptan dígitos ASCII (en el ISBN‑10, el último puede ser `X`) y se valida la longitud (10 o 13); el dígito de control no, así que el ISBN‑10 y el ISBN‑13 del mismo libro cuentan como libros distintos.
- **País del proveedor:** se valida el formato ISO alpha‑2 (2 letras mayúsculas), no que el código exista.
- **Búsqueda por categoría:** `icontains`. Con SQLite solo ignora mayúsculas en letras ASCII (`FICCIÓN` no encuentra "Ficción"); en Postgres funciona con acentos.
- **API pública:** sin autenticación (el enunciado no la pide); `DEFAULT_AUTHENTICATION_CLASSES = []` para que una cabecera `Authorization` ajena (p. ej. de un proxy) no provoque un 403.
- **Solo JSON:** un cuerpo que no es `application/json` recibe 415. Un formulario HTML de otra web puede enviar urlencoded, multipart o text/plain sin preflight CORS, y sin autenticación no hay chequeo CSRF: aceptarlos permitiría crear libros desde cualquier página. En la API navegable de DRF se usa la pestaña "Raw data".
- **Errores en JSON y en español** (en las rutas de la API): 400 con el detalle por campo (o "Solicitud con formato incorrecto." si la petición supera los límites de Django), 404 "No encontrado." (también cuando el libro no existe) y 500 "Error interno del servidor.".
- **Redondeo:** `Decimal` con `ROUND_HALF_UP` a 2 decimales en cada paso (costo en Bs. y precio final), así el desglose cuadra: `cost_local × 1,40` da exactamente `selling_price_local`.
- **Precio de venta guardado:** lo calcula y guarda `POST /books/{id}/calculate-price`. Si después un PUT cambia el `cost_usd`, el precio vuelve a `null`, porque se calculó con el costo anterior.
- **Frontend:** TanStack Query maneja el estado del servidor (caché, paginación, invalidación después de cada mutación). La tabla se ordena haciendo clic en los encabezados (ascendente, descendente y sin orden) y muestra 10, 20, 30 o 50 libros por página: el orden y el tamaño los aplica el backend, así que valen para todas las páginas y no solo para la visible. Los errores de todas las peticiones se muestran en un solo punto como toasts. Los formularios usan la validación nativa de HTML5 y los montos se muestran con formato `es-VE` (`Bs. 19.154,86`).
