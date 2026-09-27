import { useState } from "react";
import { LOW_STOCK_THRESHOLD, type BookFilter } from "../api";

interface Props {
  filter: BookFilter;
  onChange: (filter: BookFilter) => void;
}

export function Filters({ filter, onChange }: Props) {
  const [category, setCategory] = useState("");
  // Texto, como la categoría: un number controlado no deja vaciar el campo (saltaba a 0 y quedaba "05").
  const [threshold, setThreshold] = useState(String(LOW_STOCK_THRESHOLD));

  return (
    <article>
      <div className="grid">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            const value = category.trim();
            onChange(value ? { kind: "category", category: value } : { kind: "all" });
          }}
        >
          <fieldset role="group">
            <input
              type="search"
              placeholder="Buscar por categoría"
              aria-label="Categoría"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            />
            <button type="submit">Buscar</button>
          </fieldset>
        </form>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            setCategory("");
            onChange({ kind: "lowStock", threshold: Number(threshold) });
          }}
        >
          <fieldset role="group">
            <input
              type="number"
              min={0}
              required
              aria-label="Umbral de stock bajo"
              value={threshold}
              onChange={(e) => setThreshold(e.target.value)}
            />
            <button type="submit" className="secondary">Ver stock bajo</button>
          </fieldset>
        </form>
      </div>
      {filter.kind !== "all" && (
        <button
          className="outline"
          onClick={() => {
            setCategory("");
            setThreshold(String(LOW_STOCK_THRESHOLD));
            onChange({ kind: "all" });
          }}
        >
          Limpiar filtros
        </button>
      )}
    </article>
  );
}
