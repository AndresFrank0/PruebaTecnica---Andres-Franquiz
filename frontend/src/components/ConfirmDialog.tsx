import { Modal } from "./Modal";

interface Props {
  open: boolean;
  title: string;
  message: string;
  confirmLabel: string;
  busy: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}

export function ConfirmDialog({ open, title, message, confirmLabel, busy, onCancel, onConfirm }: Props) {
  return (
    <Modal open={open} title={title} onClose={onCancel}>
      <p>{message}</p>
      <footer>
        <button className="secondary" onClick={onCancel}>Cancelar</button>
        <button className="contrast" onClick={onConfirm} aria-busy={busy} disabled={busy}>
          {confirmLabel}
        </button>
      </footer>
    </Modal>
  );
}
