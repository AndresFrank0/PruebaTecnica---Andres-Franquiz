import { PAGE_SIZES } from "../api";

interface Props {
  page: number;
  pageSize: number;
  count: number;
  onPage: (page: number) => void;
  onPageSize: (pageSize: number) => void;
}

export function Pagination({ page, pageSize, count, onPage, onPageSize }: Props) {
  const pages = Math.max(1, Math.ceil(count / pageSize));
  return (
    <nav>
      <ul>
        <li><small>{count} libros · Página {page} de {pages}</small></li>
      </ul>
      <ul>
        <li>
          <select aria-label="Libros por página" value={pageSize} onChange={(e) => onPageSize(Number(e.target.value))}>
            {PAGE_SIZES.map((size) => <option key={size} value={size}>{size} por página</option>)}
          </select>
        </li>
        <li><button className="outline" disabled={page <= 1} onClick={() => onPage(page - 1)}>Anterior</button></li>
        <li><button className="outline" disabled={page >= pages} onClick={() => onPage(page + 1)}>Siguiente</button></li>
      </ul>
    </nav>
  );
}
