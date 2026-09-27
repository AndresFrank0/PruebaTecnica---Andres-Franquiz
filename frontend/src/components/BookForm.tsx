import type { FormEvent } from "react";
import type { BookInput } from "../api";
import { useBook, useSaveBook } from "../hooks";

const ISBN_RE = /^(\d{9}[\dX]|\d{13})$/;
// Mismo patrón que ISBN_SEPARATORS del backend: quita espacios y guiones (también los Unicode).
const normalizeIsbn = (value: string) => value.replace(/[\s\u2010-\u2015\u2212-]/g, "").toUpperCase();

interface Props {
  bookId: number | null;
  onDone: () => void;
}

// Con bookId null crea (POST); con un id carga el libro (GET) y lo actualiza (PUT).
// La validación es la nativa de HTML; el backend vuelve a validar y sus 400 salen como toast.
export function BookForm({ bookId, onDone }: Props) {
  const { data: book, isLoading } = useBook(bookId);
  const save = useSaveBook();

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const text = (name: string) => String(form.get(name) ?? "").trim();
    const data: BookInput = {
      title: text("title"),
      author: text("author"),
      isbn: normalizeIsbn(text("isbn")),
      cost_usd: Number(text("cost_usd")),
      stock_quantity: Number(text("stock_quantity")),
      category: text("category"),
      supplier_country: text("supplier_country").toUpperCase(),
    };
    save.mutate({ id: bookId, data }, { onSuccess: onDone });
  }

  if (bookId !== null && !book) {
    return <p aria-busy={isLoading}>{isLoading ? "Cargando libro…" : "No se pudo cargar el libro."}</p>;
  }

  return (
    <form onSubmit={handleSubmit}>
      <label>
        Título
        <input name="title" required pattern=".*\S.*" title="No puede estar en blanco" maxLength={255} defaultValue={book?.title} autoFocus />
      </label>
      <label>
        Autor
        <input name="author" required pattern=".*\S.*" title="No puede estar en blanco" maxLength={255} defaultValue={book?.author} />
      </label>
      <label>
        ISBN
        <input
          name="isbn"
          required
          placeholder="978-84-376-0494-7"
          defaultValue={book?.isbn}
          onInput={(e) =>
            e.currentTarget.setCustomValidity(
              ISBN_RE.test(normalizeIsbn(e.currentTarget.value))
                ? ""
                : "El ISBN debe tener 10 o 13 dígitos (se permiten guiones).",
            )
          }
        />
      </label>
      <div className="grid">
        <label>
          Costo (USD)
          <input name="cost_usd" type="number" required min="0.01" max="99999999.99" step="0.01" defaultValue={book?.cost_usd} />
        </label>
        <label>
          Stock
          <input name="stock_quantity" type="number" required min="0" max="2147483647" step="1" defaultValue={book?.stock_quantity ?? 0} />
        </label>
      </div>
      <div className="grid">
        <label>
          Categoría
          <input name="category" required pattern=".*\S.*" title="No puede estar en blanco" maxLength={100} defaultValue={book?.category} />
        </label>
        <label>
          País proveedor (ISO)
          <input
            name="supplier_country"
            required
            pattern="[A-Za-z]{2}"
            maxLength={2}
            placeholder="ES"
            title="Código de país de 2 letras"
            defaultValue={book?.supplier_country}
          />
        </label>
      </div>
      <button type="submit" aria-busy={save.isPending} disabled={save.isPending}>
        Guardar
      </button>
    </form>
  );
}
