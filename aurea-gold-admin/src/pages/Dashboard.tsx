import { useEffect, useState } from "react";
import API from "../lib/api";
import Layout from "../components/Layout";

type User = { id:number; email:string; role:string };

export default function Dashboard(){
  const [users,setUsers]=useState<User[]>([]);
  const [health,setHealth]=useState<string>("—");
  const [loading,setLoading]=useState(true);

  useEffect(()=>{(async()=>{
    try{
      // tabela de usuários (se a rota existir)
      try{
        const {data}=await API.get("/api/v1/users");
        const list=data?.items ?? data?.data ?? data;
        if(Array.isArray(list)) setUsers(list);
      }catch{}
      // health
      try{
        const {data}=await API.get("/health");
        setHealth(JSON.stringify(data));
      }catch{ setHealth("erro"); }
    }finally{ setLoading(false); }
  })()},[]);

  return (
    <Layout>
      <div>
        <div className="grid">
          <div className="card kpi">
            <div>
              <h3>Usuários</h3>
              <div className="value">{users.length||0}</div>
            </div>
            <div className="spark"></div>
          </div>
          <div className="card kpi">
            <div>
              <h3>Sessões ativas</h3>
              <div className="value">—</div>
            </div>
            <div className="spark"></div>
          </div>
          <div className="card kpi">
            <div>
              <h3>Status</h3>
              <div className="value" style={{color:"var(--gold)"}}>OK</div>
            </div>
            <div className="spark"></div>
          </div>
        </div>

        <h2 id="users" style={{marginTop:22}}>Usuários</h2>
        <div className="card" style={{padding:0}}>
          <table className="table">
            <thead><tr><th>ID</th><th>Email</th><th>Role</th></tr></thead>
            <tbody>
              {users.length>0 ? users.map(u=>(
                <tr key={u.id}><td>{u.id}</td><td>{u.email}</td><td>{u.role}</td></tr>
              )) : <tr><td colSpan={3} style={{color:"var(--muted)"}}>Sem dados</td></tr>}
            </tbody>
          </table>
        </div>

        <h2 id="system" style={{marginTop:22}}>Sistema</h2>
        <div className="card"><code>{health}</code></div>

        {loading && <div style={{marginTop:10,color:"var(--muted)"}}>Carregando…</div>}
      </div>
    </Layout>
  );
}
