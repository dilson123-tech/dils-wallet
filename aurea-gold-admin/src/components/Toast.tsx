import { useEffect, useState } from "react";

export function Toast({ message, type="success", onClose }:{
  message: string;
  type?: "success" | "error";
  onClose?: () => void;
}) {
  const [open, setOpen] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setOpen(false);
      onClose?.();
    }, 2200);
    return () => clearTimeout(timer);
  }, [onClose]);

  if (!open) return null;

  return (
    <div
      className={`fixed right-4 top-4 z-50 rounded-2xl px-4 py-3 shadow-lg text-sm ${
        type === "success"
          ? "bg-emerald-600 text-white"
          : "bg-rose-600 text-white"
      }`}
    >
      {message}
    </div>
  );
}
