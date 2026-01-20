const CLICK = new Audio("/click.mp3"); // coloque o mp3 na /public
export function playClick(){
  try{
    const on = localStorage.getItem("aurea_sfx") === "on";
    if(on){ CLICK.currentTime = 0; CLICK.play().catch(()=>{}); }
  }catch{}
}
export function toggleSfx(){
  const cur = localStorage.getItem("aurea_sfx")==="on";
  localStorage.setItem("aurea_sfx", cur ? "off" : "on");
  return !cur;
}
