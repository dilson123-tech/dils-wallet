export function isSomAtivo(): boolean {
  return localStorage.getItem("aurea_som") !== "off";
}
export function toggleSom(): boolean {
  const atual = isSomAtivo();
  localStorage.setItem("aurea_som", atual ? "off" : "on");
  return !atual;
}
export function playSom(tipo: "success" | "error") {
  if (!isSomAtivo()) return;
  try {
    const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
    const now = ctx.currentTime;
    const gain = ctx.createGain();
    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.exponentialRampToValueAtTime(0.12, now + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.8);

    const osc1 = ctx.createOscillator();
    const osc2 = ctx.createOscillator();
    const osc3 = ctx.createOscillator();

    if (tipo === "success") {
      osc1.frequency.setValueAtTime(1046.5, now);
      osc2.frequency.setValueAtTime(1568, now);
      osc3.frequency.setValueAtTime(2093, now);
      osc1.type = "sine"; osc2.type = "triangle"; osc3.type = "square";
    } else {
      osc1.frequency.setValueAtTime(220, now);
      osc1.frequency.exponentialRampToValueAtTime(110, now + 0.4);
      osc1.type = "sawtooth";
      osc2.frequency.setValueAtTime(330, now);
      osc2.exponentialRampToValueAtTime(165, now + 0.4);
      osc2.type = "triangle";
    }

    osc1.connect(gain); osc2.connect(gain); osc3.connect(gain);
    gain.connect(ctx.destination);
    osc1.start(now); osc2.start(now); osc3.start(now);
    osc1.stop(now + 0.8); osc2.stop(now + 0.8); osc3.stop(now + 0.8);
  } catch {}
}
