const API = import.meta.env.VITE_API_BASE || "";
export async function askAssist(msg: string){
  const r = await fetch(`${API}/api/v1/ai/assist`, {
    method:"POST", headers:{ "Content-Type":"application/json" },
    body: JSON.stringify({ msg })
  });
  if(!r.ok) throw new Error(`assist ${r.status}`);
  return r.json();
}
