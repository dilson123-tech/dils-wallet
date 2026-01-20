const API = String(import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000").replace(/\/+$/, "");
export async function askAssist(msg: string){
  const r = await fetch(`${API}/api/v1/ai/assist`, {
    method:"POST", headers:{ "Content-Type":"application/json" },
    body: JSON.stringify({ msg })
  });
  if(!r.ok) throw new Error(`assist ${r.status}`);
  return r.json();
}
