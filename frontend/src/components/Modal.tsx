import { useEffect, useRef, type ReactNode } from "react";
import { Toaster } from "sonner";

interface Props {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
}

// <dialog> nativo: showModal() da el fondo, atrapa el foco y cierra con Esc.
export function Modal({ open, title, onClose, children }: Props) {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = ref.current;
    if (open && !dialog?.open) {
      dialog?.showModal();
      // showModal() enfoca lo primero enfocable (el enlace Cerrar o el <article> con scroll): mejor el primer campo.
      dialog?.querySelector<HTMLElement>("input, select, textarea")?.focus();
    }
    if (!open && dialog?.open) dialog.close();
  }, [open]);

  return (
    <dialog ref={ref} onClose={onClose}>
      <article>
        <header>
          <a
            href="#close"
            aria-label="Cerrar"
            rel="prev"
            onClick={(e) => {
              e.preventDefault();
              onClose();
            }}
          />
          <h3>{title}</h3>
        </header>
        {/* Los hijos se montan solo mientras está abierto: cada apertura empieza de cero. */}
        {open && children}
      </article>
      {/* showModal() sube el diálogo a la top layer y el Toaster global queda detrás del fondo
          (ningún z-index lo saca). Este segundo Toaster muestra encima los toasts de mientras
          está abierto; el global también los recibe, así que siguen visibles al cerrarlo. */}
      {open && <Toaster richColors position="top-right" />}
    </dialog>
  );
}
