import { LOW_STOCK_THRESHOLD, type Book, type BookSort, type SortField } from "../api";
import { formatBs, formatUsd } from "../format";

// Columnas ordenables, en el orden de la tabla. El orden lo hace el backend (?ordering), así que vale
// para todas las páginas y no solo para la visible.
const COLUMNS: { field: SortField; label: string }[] = [
  { field: "title", label: "Título" },
  { field: "author", label: "Autor" },
  { field: "isbn", label: "ISBN" },
  { field: "category", label: "Categoría" },
  { field: "stock_quantity", label: "Stock" },
  { field: "cost_usd", label: "Costo (USD)" },
  { field: "selling_price_local", label: "Precio venta (Bs.)" },
];

interface Props {
  books: Book[];
  sort: BookSort | null;
  onSort: (field: SortField) => void;
  onDetail: (id: number) => void;
  onEdit: (id: number) => void;
  onDelete: (book: Book) => void;
}

export function BookTable({ books, sort, onSort, onDetail, onEdit, onDelete }: Props) {
  if (books.length === 0) return <p>No hay libros para mostrar.</p>;

  return (
    <div className="overflow-auto">
      <table className="striped">
        <thead>
          <tr>
            {COLUMNS.map(({ field, label }) => {
              const active = sort?.field === field;
              return (
                <th key={field} aria-sort={active ? (sort.desc ? "descending" : "ascending") : undefined}>
                  <button type="button" className="sort" onClick={() => onSort(field)}>
                    {label} <span aria-hidden="true">{active ? (sort.desc ? "▼" : "▲") : "↕"}</span>
                  </button>
                </th>
              );
            })}
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {books.map((book) => (
            <tr key={book.id}>
              <td>{book.title}</td>
              <td>{book.author}</td>
              <td>{book.isbn}</td>
              <td>{book.category}</td>
              <td>
                {book.stock_quantity <= LOW_STOCK_THRESHOLD ? <mark>{book.stock_quantity}</mark> : book.stock_quantity}
              </td>
              <td>{formatUsd(book.cost_usd)}</td>
              <td>{book.selling_price_local === null ? "—" : formatBs(book.selling_price_local)}</td>
              <td>
                <div role="group">
                  <button onClick={() => onDetail(book.id)}>Detalle</button>
                  <button className="secondary" onClick={() => onEdit(book.id)}>Editar</button>
                  <button className="contrast" onClick={() => onDelete(book)}>Eliminar</button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
