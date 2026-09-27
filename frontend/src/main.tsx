import "@picocss/pico/css/pico.min.css";
import "./index.css";
import { MutationCache, QueryCache, QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { Toaster } from "sonner";
import { ApiError } from "./api";
import App from "./App";
import { notifyError } from "./hooks";

const isNotFound = (error: Error) => error instanceof ApiError && error.status === 404;
// El libro ya no existe (lo borraron en otra pestaña) y la lista todavía lo muestra.
const refreshList = () => void queryClient.invalidateQueries({ queryKey: ["books"] });

// Los errores de todas las queries y mutations se muestran como toast desde aquí.
const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: (error, query) => {
      // Una página de la lista (clave de useBooks: ["books", filtro, página, tamaño, orden]) que dejó de existir no es
      // un error para el usuario: App retrocede de página. La 1 siempre existe: si da 404, la URL de la
      // API está mal y sí hay que avisar.
      if (isNotFound(error) && query.queryKey[0] === "books" && query.queryKey[2] !== 1) return;
      notifyError(error);
      if (isNotFound(error) && query.queryKey[0] === "book") refreshList();
    },
  }),
  mutationCache: new MutationCache({
    onError: (error) => {
      notifyError(error);
      if (isNotFound(error)) refreshList();
    },
  }),
  // Un 4xx no cambia al reintentar: se muestra enseguida.
  defaultOptions: {
    queries: {
      retry: (failures, error) => failures < 1 && !(error instanceof ApiError && error.status >= 400 && error.status < 500),
    },
  },
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
      <Toaster richColors position="top-right" />
    </QueryClientProvider>
  </StrictMode>,
);
