import { NavLink } from "react-router-dom";

export default function Layout({children}:{children:React.ReactNode}){
  const email = localStorage.getItem("aurea_user") || "—";
  function logout(){
    localStorage.removeItem("aurea_token");
    localStorage.removeItem("aurea_user");
    localStorage.removeItem("aurea_role");
    window.location.href="/login";
  }
  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand"><span className="dot"></span><span>Aurea&nbsp;Gold</span></div>
        <div className="nav">
          <NavLink to="/admin" className={({isActive})=>isActive? "active": ""}>Dashboard</NavLink>
          <NavLink to="/admin#users" className={({isActive})=>isActive? "active": ""}>Usuários</NavLink>
          <NavLink to="/admin#system" className={({isActive})=>isActive? "active": ""}>Sistema</NavLink>
        </div>
        <div style={{marginTop:"auto",color:"var(--muted)",fontSize:12}}>
          <div className="badge">v0.1.0</div>
        </div>
      </aside>

      <main style={{display:"grid",gridTemplateRows:"auto 1fr"}}>
        <header className="header">
          <div style={{display:"flex",gap:8,alignItems:"center"}}>
            <div className="badge">Admin Console</div>
          </div>
          <div className="user">
            <span>{email}</span>
            <button className="ghost" onClick={logout}>Sair</button>
          </div>
        </header>
        <div className="content">{children}</div>
      </main>
    </div>
  );
}
