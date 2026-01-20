from ..database import Base  # Base única do projeto

# auto-importa todos os submódulos para registrar tabelas no Base.metadata
import pkgutil, importlib, pathlib
_pkg_path = pathlib.Path(__file__).parent
for _m in pkgutil.iter_modules([str(_pkg_path)]):
    name = _m.name
    if name.startswith("_") or name == "__init__":
        continue
    importlib.import_module(f"{__name__}.{name}")

__all__ = ["Base"]
from .reservas import Reserva

# === Export explícito do modelo User para imports de alto nível ===
try:
    from .user_main import User as User  # type: ignore  # noqa: F401
except Exception:  # pragma: no cover
    User = None  # type: ignore

