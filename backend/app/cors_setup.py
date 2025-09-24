from fastapi.middleware.cors import CORSMiddleware

ALLOWED_ORIGINS = ["http://127.0.0.1:5501", "http://localhost:5501"]

def apply_cors(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
