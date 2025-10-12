import { useEffect, useState } from "react";
import api from "@/app/lib/api";

export type PixItem = {
  id: string;
  when: string;
  type: "IN" | "OUT";
  description?: string;
  amount: number;
};

export default function useRecentPix(limit: number = 10) {
  const [items, setItems] = useState<PixItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const r = await api.get(`/api/v1/pix/history`, { params: { limit } });
        if (!mounted) return;
        setItems(r.data?.items ?? r.data ?? []);
      } catch (e: any) {
        setError(e?.message ?? "Erro ao carregar extrato PIX");
      } finally {
        setLoading(false);
      }
    })();
    return () => { mounted = false; };
  }, [limit]);

  return { items, loading, error };
}
