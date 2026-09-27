import { useState } from "react";
import { ApiError, PAGE_SIZES, type Book, type BookFilter, type BookSort, type SortField } from "./api";
import { BookDetail } from "./components/BookDetail";
import { BookForm } from "./components/BookForm";
import { BookTable } from "./components/BookTable";
import { ConfirmDialog } from "./components/ConfirmDialog";
import { Filters } from "./components/Filters";
import { Modal } from "./components/Modal";
import { Pagination } from "./components/Pagination";
import { useBooks, useDeleteBook } from "./hooks";

export default function App() {
  const [filter, setFilter] = useState<BookFilter>({ kind: "all" });
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(PAGE_SIZES[0]);
  // null: el orden por defecto de la API (por id, el de alta).
  const [sort, setSort] = useState<BookSort | null>(null);
  const [formId, setFormId] = useState<number | "new" | null>(null);
  const [detailId, setDetailId] = useState<number | null>(null);
  const [toDelete, setToDelete] = useState<Book | null>(null);

  const books = useBooks(filter, page, pageSize, sort);
  const deleteBook = useDeleteBook();
  // La página ya no existe (se borró o se editó su último libro, aquí o en otra pestaña): se retrocede
  // una página hasta dar con una que exista (la 1 siempre existe). Se ajusta durante el render, como
  // recomienda React, y no en un efecto. Solo con la respuesta ya recibida: al volver a una página que
  // dio 404, TanStack entrega ese error viejo mientras la repide.
  if (page > 1 && !books.isFetching && books.error instanceof ApiError && books.error.status === 404) setPage(page - 1);

  // Cambiar el filtro, el tamaño o el orden cambia qué libros caen en cada página: se vuelve a la 1.
  function changeFilter(next: BookFilter) {
    setFilter(next);
    setPage(1);
  }

  function changePageSize(next: number) {
    setPageSize(next);
    setPage(1);
  }

  // Clics en la misma columna: ascendente → descendente → sin orden (el de la API, por id).
  function changeSort(field: SortField) {
    setSort((current) =>
      current?.field !== field ? { field, desc: false } : current.desc ? null : { field, desc: true },
    );
    setPage(1);
  }

  function confirmDelete() {
    if (!toDelete) return;
    const { id } = toDelete;
    deleteBook.mutate(id, {
      // Solo se cierra si el diálogo sigue siendo el de este libro. Si era la última fila de la página,
      // la regla de arriba lleva a la anterior cuando la lista refrescada responde 404.
      onSuccess: () => setToDelete((current) => (current?.id === id ? null : current)),
    });
  }

  return (
    <main className="container">
      <nav>
        <ul><li><h1>Inventario de Librería</h1></li></ul>
        <ul><li><button onClick={() => setFormId("new")}>+ Nuevo libro</button></li></ul>
      </nav>

      <Filters filter={filter} onChange={changeFilter} />

      {books.isError ? (
        <p>
          No se pudieron cargar los libros.{" "}
          <button className="outline" onClick={() => books.refetch()}>Reintentar</button>
        </p>
      ) : !books.data ? (
        <p aria-busy="true">Cargando libros…</p>
      ) : (
        <>
          {/* Siempre ocupa su sitio: al refrescar solo se hace visible y la tabla no salta. */}
          <progress aria-label="Actualizando" style={{ visibility: books.isFetching ? "visible" : "hidden" }} />
          <BookTable
            books={books.data.results}
            sort={sort}
            onSort={changeSort}
            onDetail={setDetailId}
            onEdit={setFormId}
            onDelete={setToDelete}
          />
          <Pagination page={page} pageSize={pageSize} count={books.data.count} onPage={setPage} onPageSize={changePageSize} />
        </>
      )}

      <Modal open={formId !== null} title={formId === "new" ? "Nuevo libro" : "Editar libro"} onClose={() => setFormId(null)}>
        <BookForm bookId={formId === "new" ? null : formId} onDone={() => setFormId(null)} />
      </Modal>

      <Modal open={detailId !== null} title="Detalle del libro" onClose={() => setDetailId(null)}>
        {detailId !== null && <BookDetail bookId={detailId} />}
      </Modal>

      <ConfirmDialog
        open={toDelete !== null}
        title="Eliminar libro"
        message={`¿Seguro que deseas eliminar «${toDelete?.title}»? Esta acción no se puede deshacer.`}
        confirmLabel="Eliminar"
        busy={deleteBook.isPending && deleteBook.variables === toDelete?.id}
        onCancel={() => setToDelete(null)}
        onConfirm={confirmDelete}
      />
    </main>
  );
}
