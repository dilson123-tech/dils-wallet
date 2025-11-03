let audioCtx: AudioContext | null = null;

function ensureCtx() {
  if (typeof window === "undefined") return null;
  // @ts-ignore - webkit fallback em alguns navegadores
  const AC: typeof AudioContext = (window as any).AudioContext || (window as any).webkitAudioContext;
  if (!AC) return null;
  if (!audioCtx) audioCtx = new AC();
  return audioCtx;
}

function beep(freq: number, ms: number, type: OscillatorType = "sine", vol = 0.05) {
  const ctx = ensureCtx();
  if (!ctx) return;
  const o = ctx.createOscillator();
  const g = ctx.createGain();
  o.type = type;
  o.frequency.value = freq;
  g.gain.setValueAtTime(0, ctx.currentTime);
  g.gain.linearRampToValueAtTime(vol, ctx.currentTime + 0.005);         // ataque rápido
  g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + ms/1000); // release
  o.connect(g).connect(ctx.destination);
  o.start();
  o.stop(ctx.currentTime + ms/1000 + 0.01);
}

/** Clique curto pra UI */
export function playClick() {
  beep(320, 60, "square", 0.03);
}

/** Sucesso com arpejo rapidinho */
export function playSuccess() {
  beep(880, 90, "triangle", 0.04);
  setTimeout(() => beep(1320, 120, "triangle", 0.035), 80);
}

/** Erro grave em dois tons */
export function playError() {
  beep(200, 120, "sawtooth", 0.05);
  setTimeout(() => beep(140, 160, "sawtooth", 0.05), 90);
}
