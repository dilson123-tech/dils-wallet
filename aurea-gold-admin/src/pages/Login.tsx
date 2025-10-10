import { useState } from "react";
import API from "../lib/api";

export default function Login(){
  const [email,setEmail]=useState("admin@example.com");
  const [password,setPassword]=useState("");
  const [msg,setMsg]=useState(""); const [loading,setLoading]=useState(false);

  async function onSubmit(e:React.FormEvent){
    e.preventDefault(); setMsg(""); setLoading(true);
    try{
      const body=new URLSearchParams({username:email.trim(),password:password.trim()});
      const {data}=await API.post("/api/v1/auth/login", body, {headers:{'Content-Type':'application/x-www-form-urlencoded'}});
      if(!data?.access_token) throw new Error("Token ausente");
      localStorage.setItem("aurea_token",data.access_token);
      localStorage.setItem("aurea_user",email.trim());
      localStorage.removeItem("aurea_role");
      window.location.href="/admin";
    }catch(err:any){
      setMsg(err?.response?.data?.detail||err?.message||"Falha no login");
    }finally{ setLoading(false); }
  }

  return (
    <div style={{height:"100%",display:"grid",placeItems:"center"}}>
      <div className="card" style={{width:420}}>
        <h2 style={{margin:"0 0 6px 0",fontSize:24}}>Aurea Gold — Login</h2>
        <div style={{color:"var(--muted)",marginBottom:12}}>Acesse o console administrativo</div>
        <form onSubmit={onSubmit}>
          <label>Email</label>
          <input style={{width:"100%",margin:"6px 0 10px 0"}} type="email" value={email} onChange={e=>setEmail(e.target.value)} autoFocus />
          <label>Senha</label>
          <input style={{width:"100%",margin:"6px 0 10px 0"}} type="password" value={password} onChange={e=>setPassword(e.target.value)} />
          {msg && <div style={{color:"var(--danger)",marginBottom:8}}>{msg}</div>}
          <button disabled={loading} style={{width:"100%"}}>{loading? "Entrando..." : "Entrar"}</button>
        </form>
      </div>
    </div>
  );
}
