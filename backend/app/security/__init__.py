# Ponte de compatibilidade.
# Motivo: nossas rotas fazem `from app.security import get_current_user`,
# mas em runtime o Python resolve `app/security/__init__.py` (este arquivo)
# antes de olhar `app/security.py`.
#
# Então aqui a gente reexporta a função real do módulo security.py
# pra não quebrar import durante o boot.

from app.security import get_current_user as get_current_user  # type: ignore
