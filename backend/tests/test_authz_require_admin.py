from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.utils.authz import require_admin


def test_require_admin_allows_role_admin():
    user = SimpleNamespace(role="admin")
    assert require_admin(current_user=user) is user


def test_require_admin_blocks_role_customer():
    user = SimpleNamespace(role="customer")
    with pytest.raises(HTTPException) as exc:
        require_admin(current_user=user)
    assert exc.value.status_code == 403


def test_require_admin_blocks_role_manager():
    user = SimpleNamespace(role="manager")
    with pytest.raises(HTTPException) as exc:
        require_admin(current_user=user)
    assert exc.value.status_code == 403


def test_require_admin_blocks_missing_role():
    user = SimpleNamespace()
    with pytest.raises(HTTPException) as exc:
        require_admin(current_user=user)
    assert exc.value.status_code == 403
