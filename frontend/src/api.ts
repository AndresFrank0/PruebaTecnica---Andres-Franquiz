// || y no ??: una VITE_API_URL vacía también usa el valor por defecto.
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Opciones de "libros por página"; el backend acepta hasta 50 (max_page_size en views.py).
export const PAGE_SIZES = [10, 20, 30, 50];
export const LOW_STOCK_THRESHOLD = 10;

export interface Book {
  id: number;
  title: string;
  author: string;
  isbn: string;
  cost_usd: number;
  selling_price_local: number | null;
  stock_quantity: number;
  category: string;
  supplier_country: string;
  created_at: string;
  updated_at: string;
}

export type BookInput = Omit<Book, "id" | "selling_price_local" | "created_at" | "updated_at">;

export interface Page<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface PriceCalculation {
  book_id: number;
  cost_usd: number;
  exchange_rate: number;
  cost_local: number;
  margin_percentage: number;
  selling_price_local: number;
  currency: "VES";
  rate_source: "live" | "default";
  calculation_timestamp: string;
}

export type BookFilter =
  | { kind: "all" }
  | { kind: "category"; category: string }
  | { kind: "lowStock"; threshold: number };

// Columnas por las que el backend sabe ordenar (ordering_fields en views.py).
export type SortField = "title" | "author" | "isbn" | "category" | "stock_quantity" | "cost_usd" | "selling_price_local";
export interface BookSort {
  field: SortField;
  desc: boolean;
}

// Nombres de campo de la API tal como los ve el usuario en los toasts de error.
const FIELD_LABELS: Record<string, string> = {
  title: "Título", author: "Autor", isbn: "ISBN", cost_usd: "Costo", stock_quantity: "Stock",
  category: "Categoría", supplier_country: "País", threshold: "Umbral",
};

function errorMessage(status: number, body: unknown): string {
  if (body && typeof body === "object") {
    if ("detail" in body) return String(body.detail);
    // Errores de validación de DRF: { campo: ["mensaje", ...] }
    return Object.entries(body)
      .map(([field, messages]) => `${FIELD_LABELS[field] ?? field}: ${[messages].flat().join(" ")}`)
      .join(" · ");
  }
  return `Error ${status}`;
}

export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, body: unknown) {
    super(errorMessage(status, body));
    this.status = status;
    this.body = body;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      // Content-Type solo con cuerpo: en un GET obliga al navegador a un preflight CORS extra.
      headers: init?.body ? { "Content-Type": "application/json" } : undefined,
      // Sin esto, una API colgada deja la UI cargando para siempre.
      signal: AbortSignal.timeout(10_000),
      ...init,
    });
  } catch (error) {
    // AbortSignal.timeout rechaza con un TimeoutError; cualquier otro error es de red.
    const timedOut = error instanceof DOMException && error.name === "TimeoutError";
    throw new ApiError(0, { detail: timedOut ? "La API no respondió a tiempo." : "No se pudo conectar con la API." });
  }
  const body = response.status === 204 ? null : await response.json().catch(() => undefined);
  if (!response.ok) throw new ApiError(response.status, body);
  // Un 2xx sin JSON no viene de la API (p. ej. VITE_API_URL apunta al servidor de la SPA).
  if (body === undefined) throw new ApiError(response.status, { detail: "La respuesta no es de la API." });
  return body as T;
}

export const api = {
  listBooks(filter: BookFilter, page: number, pageSize: number, sort: BookSort | null) {
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
    if (sort) params.set("ordering", `${sort.desc ? "-" : ""}${sort.field}`);
    let path = "/books";
    if (filter.kind === "category") {
      path = "/books/search";
      params.set("category", filter.category);
    } else if (filter.kind === "lowStock") {
      path = "/books/low-stock";
      params.set("threshold", String(filter.threshold));
    }
    return request<Page<Book>>(`${path}?${params}`);
  },
  getBook: (id: number) => request<Book>(`/books/${id}`),
  createBook: (data: BookInput) =>
    request<Book>("/books", { method: "POST", body: JSON.stringify(data) }),
  updateBook: (id: number, data: BookInput) =>
    request<Book>(`/books/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteBook: (id: number) => request<null>(`/books/${id}`, { method: "DELETE" }),
  calculatePrice: (id: number) =>
    request<PriceCalculation>(`/books/${id}/calculate-price`, {
      method: "POST",
      // Si DolarAPI no responde, el backend espera hasta 5 s por cada una de sus IP antes de usar la
      // tasa por defecto. Con 10 s, la SPA diría "Sin conexión" con el precio ya guardado.
      signal: AbortSignal.timeout(30_000),
    }),
};
