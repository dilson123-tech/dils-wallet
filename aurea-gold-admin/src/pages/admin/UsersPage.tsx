import { useEffect, useState } from "react";
import axios from "axios";
import API from "../../lib/api";
import { errorMessage } from "../../lib/auth";

type AdminUser = {
  id: number;
  email: string;
  full_name: string | null;
  role: string;
};

type AdminUsersPage = {
  items: AdminUser[];
  total: number;
};

const PAGE_SIZE = 50;

export default function UsersPage() {
  const [skip, setSkip] = useState(0);
  const [data, setData] = useState<AdminUsersPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const ctrl = new AbortController();
    setLoading(true);
    setError(null);
    API.get<AdminUsersPage>("/api/v1/admin/users", {
      params: { skip, limit: PAGE_SIZE },
      signal: ctrl.signal,
    })
      .then((r) => setData(r.data))
      .catch((err) => {
        if (axios.isCancel(err)) return;
        setData(null);
        setError(errorMessage(err));
      })
      .finally(() => {
        if (!ctrl.signal.aborted) setLoading(false);
      });
    return () => ctrl.abort();
  }, [skip]);

  const rows = data?.items ?? [];
  const total = data?.total ?? 0;
  const from = rows.length ? skip + 1 : 0;
  const to = skip + rows.length;

  return (
    <div className="carbon-bg min-h-screen pt-24 pb-10">
      <div className="max-w-7xl mx-auto px-4">
        <header className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight gold-title">Aurea Gold · Usuários</h1>
            <p className="text-slate-400">Gestão de contas e perfis</p>
          </div>
          <button className="gold-button gold-shine opacity-60 cursor-not-allowed" disabled title="Em breve">
            Novo usuário
          </button>
        </header>

        <div className="glass-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-white/5">
                <tr className="[&>th]:px-4 [&>th]:py-3 text-left text-slate-300">
                  <th>ID</th><th>Nome</th><th>E-mail</th><th>Perfil</th>
                </tr>
              </thead>
              <tbody className="[&>tr>*]:px-4 [&>tr>*]:py-3">
                {loading && (
                  <tr><td colSpan={4} className="text-center text-slate-400">Carregando usuários...</td></tr>
                )}
                {!loading && error && (
                  <tr><td colSpan={4} role="alert" className="text-center text-red-400">{error}</td></tr>
                )}
                {!loading && !error && rows.length === 0 && (
                  <tr><td colSpan={4} className="text-center text-slate-400">Nenhum usuário encontrado.</td></tr>
                )}
                {!loading && !error && rows.map((r) => (
                  <tr key={r.id} className="border-t border-white/10 hover:bg-white/5 transition">
                    <td className="font-mono text-slate-400">#{r.id}</td>
                    <td className="font-medium">{r.full_name || "—"}</td>
                    <td className="text-slate-300">{r.email}</td>
                    <td>
                      <span className="px-2 py-1 rounded-lg bg-yellow-500/15 text-yellow-300 border border-yellow-400/20">
                        {r.role}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {!error && total > 0 && (
          <div className="mt-4 flex items-center justify-between text-sm text-slate-400">
            <span>Mostrando {from}–{to} de {total}</span>
            <div className="flex gap-2">
              <button
                className="gold-button gold-shine disabled:opacity-50"
                disabled={loading || skip === 0}
                onClick={() => setSkip((s) => Math.max(0, s - PAGE_SIZE))}
              >
                Anterior
              </button>
              <button
                className="gold-button gold-shine disabled:opacity-50"
                disabled={loading || skip + PAGE_SIZE >= total}
                onClick={() => setSkip((s) => s + PAGE_SIZE)}
              >
                Próxima
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
