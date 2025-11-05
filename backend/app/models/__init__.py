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
