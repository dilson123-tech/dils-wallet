// shim opcional que existia pra colocar um helper no window.
// a versão atual da API não expõe readJsonSafe.
// vamos colocar um fallback inofensivo só pra não quebrar o bundle.

function readJsonSafeDummy(res: Response): Promise<any> {
  return res.json().catch(() => null);
}

if (typeof window !== "undefined") {
  (window as any).readJson = readJsonSafeDummy;
}

export {};
