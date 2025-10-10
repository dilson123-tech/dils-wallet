import { useAuth } from "../store/auth";
export default function Nav(){
  const { user, logout } = useAuth();
  return (
    <div className="flex items-center justify-between p-4 border-b border-[#2a2a2a]">
      <div className="font-bold text-xl"><span className="text-gold">Aurea</span> Gold Admin</div>
      <div className="flex items-center gap-4">
        <span className="text-sm opacity-80">{user?.email}</span>
        <button className="btn-gold" onClick={logout}>Sair</button>
      </div>
    </div>
  );
}
