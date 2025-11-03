import React, { useEffect } from "react";
import { playSom } from "../../lib/som";

export default function Toast({
  kind = "success",
  msg,
  onDone,
  ttl = 2500,
}: {
  kind?: "success" | "error";
  msg: string;
  onDone: () => void;
  ttl?: number;
}) {
  useEffect(() => {
    playSom();
    const t = setTimeout(onDone, ttl);
    return () => clearTimeout(t);
  }, [kind, onDone, ttl]);

  return (
    <div className={`toast ${kind}`}>
      <span className="toast-dot" />
      <span className="toast-msg">{msg}</span>
    </div>
  );
}
