import { formatBs, formatRate, formatUsd } from "../format";
import { useBook, useCalculatePrice } from "../hooks";

// Ficha del libro (GET /books/{id}) y cálculo del precio de venta (POST /books/{id}/calculate-price).
// Al calcular, la mutación invalida las queries: "Precio de venta actual" y la tabla se actualizan solas.
export function BookDetail({ bookId }: { bookId: number }) {
  const { data: book, isLoading } = useBook(bookId);
  const calculate = useCalculatePrice();
  const result = calculate.data;

  if (!book) {
    return <p aria-busy={isLoading}>{isLoading ? "Cargando libro…" : "No se pudo cargar el libro."}</p>;
  }

  return (
    <>
      <table>
        <tbody>
          <tr><th scope="row">Título</th><td>{book.title}</td></tr>
          <tr><th scope="row">Autor</th><td>{book.author}</td></tr>
          <tr><th scope="row">ISBN</th><td>{book.isbn}</td></tr>
          <tr><th scope="row">Categoría</th><td>{book.category}</td></tr>
          <tr><th scope="row">Stock</th><td>{book.stock_quantity}</td></tr>
          <tr><th scope="row">País proveedor</th><td>{book.supplier_country}</td></tr>
          <tr><th scope="row">Costo</th><td>{formatUsd(book.cost_usd)}</td></tr>
          <tr>
            <th scope="row">Precio de venta actual</th>
            <td>{book.selling_price_local === null ? "Sin calcular" : formatBs(book.selling_price_local)}</td>
          </tr>
        </tbody>
      </table>

      <button onClick={() => calculate.mutate(book.id)} aria-busy={calculate.isPending} disabled={calculate.isPending}>
        Calcular precio de venta
      </button>

      {result && (
        <article>
          <header><strong>Desglose del cálculo</strong></header>
          <table>
            <tbody>
              <tr><th scope="row">Costo original</th><td>{formatUsd(result.cost_usd)}</td></tr>
              <tr>
                <th scope="row">Tasa BCV</th>
                <td>
                  1 USD = Bs. {formatRate(result.exchange_rate)}
                  {result.rate_source === "default" && <small> (tasa por defecto: DolarAPI no respondió)</small>}
                </td>
              </tr>
              <tr><th scope="row">Costo en bolívares</th><td>{formatBs(result.cost_local)}</td></tr>
              <tr><th scope="row">Margen de ganancia</th><td>{result.margin_percentage}%</td></tr>
              <tr>
                <th scope="row">Precio de venta sugerido</th>
                <td><strong>{formatBs(result.selling_price_local)}</strong></td>
              </tr>
              <tr><th scope="row">Calculado</th><td>{new Date(result.calculation_timestamp).toLocaleString("es-VE")}</td></tr>
            </tbody>
          </table>
        </article>
      )}
    </>
  );
}
