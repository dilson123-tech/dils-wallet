import { ReactNode, useState } from "react";
import LoginModal from "../components/LoginModal";
// -ignore - relax props durante restauração
const LoginModalAny:any = LoginModal;
import { useSession } from "../context/SessionContext";

export default function Shell({ children }: { children: ReactNode }) {
  const { isAuthed, logout } = useSession();
  const [loginOpen, setLoginOpen] = useState(false);

  const onSupport = () => alert("Suporte Aurea Gold Premium — em breve chat e WhatsApp integrado.");
  const onLogin  = () => setLoginOpen(true);
  const onLogout = () => { logout(); alert("✅ Sessão encerrada."); };

  return (
    <div className="min-h-screen">
      <nav className="aurea-nav">
        <div className="brand">
          <div className="brand-badge" />
          <div className="brand-text">Aurea <strong>Gold</strong> Premium</div>
        </div>
        <div style={{display:"flex", gap:12}}>
          <button className="btn" onClick={onSupport}>Suporte</button>
          {!isAuthed ? (
            <button className="btn btn-primary glow-gold" onClick={onLogin}>Entrar</button>
          ) : (
            <button className="btn btn-primary glow-gold" onClick={onLogout}>Sair</button>
          )}
        </div>
      </nav>

      <main className="aurea-container">{children}</main>

        // -ignore
      <LoginModalAny open={loginOpen} onClose={() => setLoginOpen(false)} />
    </div>
  );
}
