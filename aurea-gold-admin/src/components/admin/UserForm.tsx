import { useState } from "react";
import type { UserCreate, UserUpdate, User } from "../../api/users";

export function UserForm({
  initial,
  mode,
  onSubmit,
  onCancel,
}: {
  initial?: Partial<User>;
  mode: "create" | "edit";
  onSubmit: (payload: UserCreate | UserUpdate) => Promise<void>;
  onCancel: () => void;
}) {
  const [email, setEmail] = useState(initial?.email ?? "");
  const [fullName, setFullName] = useState(initial?.full_name ?? "");
  const [isActive, setIsActive] = useState(initial?.is_active ?? true);
  const [role, setRole] = useState<"admin" | "manager" | "customer">(
    (initial?.role as any) ?? "customer"
  );
  const [password, setPassword] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (mode === "create") {
      await onSubmit({
        email,
        full_name: fullName || null,
        is_active: isActive,
        role,
        password,
      });
    } else {
      const p: UserUpdate = {
        email,
        full_name: fullName || null,
        is_active: isActive,
        role,
      };
      if (password) p.password = password;
      await onSubmit(p);
    }
  }

  return (
    <form className="space-y-4" onSubmit={submit}>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-xs text-gray-300">Email</label>
          <input
            className="mt-1 w-full rounded-xl bg-[#1a1a1a] border border-[#2a2a2a] p-2 text-sm text-white"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>

        <div>
          <label className="text-xs text-gray-300">Nome</label>
          <input
            className="mt-1 w-full rounded-xl bg-[#1a1a1a] border border-[#2a2a2a] p-2 text-sm text-white"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
          />
        </div>

        <div>
          <label className="text-xs text-gray-300">Role</label>
          <select
            className="mt-1 w-full rounded-xl bg-[#1a1a1a] border border-[#2a2a2a] p-2 text-sm text-white"
            value={role}
            onChange={(e) => setRole(e.target.value as any)}
          >
            <option value="admin">admin</option>
            <option value="manager">manager</option>
            <option value="customer">customer</option>
          </select>
        </div>

        <div>
          <label className="text-xs text-gray-300">Ativo</label>
          <div className="mt-1">
            <input
              id="active"
              type="checkbox"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
            />
            <label htmlFor="active" className="ml-2 text-sm">
              Usuário ativo
            </label>
          </div>
        </div>

        <div className="col-span-2">
          <label className="text-xs text-gray-300">
            {mode === "create" ? "Senha" : "Nova senha (opcional)"}
          </label>
          <input
            className="mt-1 w-full rounded-xl bg-[#1a1a1a] border border-[#2a2a2a] p-2 text-sm text-white"
            type="password"
            placeholder={
              mode === "edit" ? "Deixe vazio para manter" : "Mín. 6 caracteres"
            }
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            {...(mode === "create" ? { required: true } : {})}
          />
        </div>
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <button
          type="button"
          onClick={onCancel}
          className="rounded-xl px-4 py-2 text-sm border border-[#2a2a2a] hover:bg-white/5"
        >
          Cancelar
        </button>
        <button
          type="submit"
          className="rounded-xl px-4 py-2 text-sm font-semibold"
          style={{ backgroundColor: "#d4af37", color: "#111" }}
        >
          {mode === "create" ? "Criar" : "Salvar"}
        </button>
      </div>
    </form>
  );
}
