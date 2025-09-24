from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse

def attach_static(app):
    """
    Serve o frontend em /app e redireciona / -> /app/
    Protegido com try/except para nunca derrubar a API.
    """
    try:
        app.mount("/app", StaticFiles(directory="app/static", html=True), name="static")

        @app.get("/", include_in_schema=False)
        def root():
            return RedirectResponse(url="/app/")
    except Exception as e:
        import logging
        logging.getLogger("uvicorn.error").warning(f"Static mount disabled: {e}")
