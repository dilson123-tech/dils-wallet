import { useEffect, useState } from "react";
import { apiGet } from "../../lib/api";
const USER_EMAIL = (import.meta as any).env?.VITE_USER_EMAIL || "";

export default function BalanceLive() {
  const [balance, setBalance] = useState<number>(0);

  useEffect(() => {
    apiGet("/balance", { headers: { "X-User-Email": USER_EMAIL } })
      .then((j: any) => setBalance(j?.balance ?? 0))
      .catch(() => setBalance(0));
  }, []);

  return <div className="aurea-balance">Saldo: R$ {Number(balance).toFixed(2)}</div>;
}
