import { useEffect, useState } from "react";
import { decodeJwt } from "../lib/jwt";

type Props = { allowed: Array<"admin"|"manager"|"customer">, children: JSX.Element };

export default function IfRole({ allowed, children }: Props) {
  const [role, setRole] = useState<string | null>(localStorage.getItem("aurea_role"));

  useEffect(() => {
    if (role) return;
    const token = localStorage.getItem("aurea_token");
    if (!token) return;
    const p = decodeJwt<any>(token);
    const r = p?.role || p?.claims?.role;
    if (r) {
      localStorage.setItem("aurea_role", r);
      setRole(r);
    }
  }, [role]);

  if (!role) return null;       // evita flicker até saber
  return allowed.includes(role as any) ? children : null;
}
