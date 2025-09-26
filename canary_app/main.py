from fastapi import FastAPI

app = FastAPI(title="dils-wallet-canary")

@app.get("/")
def root():
    return {"ok": True, "service": "dils-wallet-canary"}

@app.get("/api/v1/health")
def health():
    return {"status": "ok"}
