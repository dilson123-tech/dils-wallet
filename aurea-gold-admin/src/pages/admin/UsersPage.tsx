export default function UsersPage() {
  const rows = [
    { id: 1, name: "Maria Souza", email: "maria@exemplo.com", role: "ADMIN" },
    { id: 2, name: "João Lima", email: "joao@exemplo.com", role: "USER" },
    { id: 3, name: "Carla Dias", email: "carla@exemplo.com", role: "MANAGER" },
  ];

  return (
    <div className="carbon-bg min-h-screen pt-24 pb-10">
      <div className="max-w-7xl mx-auto px-4">
        <header className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight gold-title">Aurea Gold · Usuários</h1>
            <p className="text-slate-400">Gestão de contas e perfis</p>
          </div>
          <button className="gold-button gold-shine">Novo usuário</button>
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
                {rows.map((r) => (
                  <tr key={r.id} className="border-t border-white/10 hover:bg-white/5 transition">
                    <td className="font-mono text-slate-400">#{r.id}</td>
                    <td className="font-medium">{r.name}</td>
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
      </div>
    </div>
  );
}
