import { useState, useEffect } from "react";
import { useSession } from "../context/SessionContext";

type Props = { open: boolean; onClose: () => void };

export default function LoginModal({ open, onClose }: Props){
  const { login } = useSession();
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("admin");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(()=>{
    const onEsc = (e: KeyboardEvent)=>{ if(e.key === "Escape") onClose(); };
    document.addEventListener("keydown", onEsc);
    return ()=> document.removeEventListener("keydown", onEsc);
  }, [onClose]);

  if(!open) return null;

  const submit = async (e: React.FormEvent)=>{
    e.preventDefault();
    setErr(null); setLoading(true);
    try{
      await login(email, password);
      onClose();
      alert("✅ Login efetuado!");
    }catch(ex:any){
      setErr(ex?.message || "Falha no login");
    }finally{
      setLoading(false);
    }
  };

  // estilos inline para não depender de CSS extra agora
  const overlay: React.CSSProperties = {
    position:"fixed", inset:0, background:"rgba(0,0,0,.55)", display:"grid", placeItems:"center", zIndex:50
  };
  const card: React.CSSProperties = {
    width:"min(92vw, 420px)", borderRadius:16, padding:20,
    background:"linear-gradient(180deg, rgba(255,193,7,.10) 0%, rgba(255,193,7,.03) 100%), #111114",
    border:"1px solid rgba(255,255,255,.10)", boxShadow:"0 20px 60px rgba(0,0,0,.6)", color:"#EAECEF"
  };
  const label: React.CSSProperties = { fontSize:13, color:"#AEB4C2", marginBottom:6 };
  const input: React.CSSProperties = {
    width:"100%", padding:"12px 14px", borderRadius:12, background:"#16181D",
    border:"1px solid rgba(255,255,255,.12)", color:"#EAECEF"
  };
  const actions: React.CSSProperties = { display:"flex", gap:12, marginTop:14, justifyContent:"flex-end" };
  const btn: React.CSSProperties = {
    padding:"10px 16px", borderRadius:12, border:"1px solid rgba(255,255,255,.12)", background:"#23262F", cursor:"pointer"
  };
  const btnGold: React.CSSProperties = {
    ...btn, border:"none",
    background:"linear-gradient(135deg,#FFE082 0%,#FFC107 35%,#FF8F00 70%,#FFD54F 100%)",
    color:"#1A1200", fontWeight:800
  };

  return (
    <div style={overlay} onClick={onClose}>
      <div style={card} onClick={(e)=>e.stopPropagation()}>
        <h3 style={{margin:"0 0 4px", fontWeight:800}}>Entrar</h3>
        <p style={{margin:"0 0 16px", color:"#AEB4C2"}}>Acesse sua conta Aurea Gold.</p>

        {err && <div style={{marginBottom:12, color:"#ff6b6b", fontSize:13}}>⚠ {err}</div>}

        <form onSubmit={submit}>
          <div style={{display:"grid", gap:12}}>
            <div>
              <div style={label}>E-mail</div>
              <input style={input} type="email" value={email} onChange={e=>setEmail(e.target.value)} required />
            </div>
            <div>
              <div style={label}>Senha</div>
              <input style={input} type="password" value={password} onChange={e=>setPassword(e.target.value)} required />
            </div>
          </div>
          <div style={actions}>
            <button type="button" style={btn} onClick={onClose}>Cancelar</button>
            <button type="submit" style={btnGold} className="glow-gold" disabled={loading}>{loading ? "Entrando..." : "Entrar"}</button>
          </div>
        </form>
      </div>
    </div>
  );
}
