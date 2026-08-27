from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.rbac_middleware import require_authenticated_user
from app.auth.models import User
from app.history.chat_history import get_history_for_user, delete_history_entry

router = APIRouter(prefix="/history", tags=["history"])


@router.get("")
def get_my_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_authenticated_user),
):
    return get_history_for_user(current_user.id, page=page, page_size=page_size)


@router.delete("/{entry_id}")
def delete_my_history_entry(entry_id: int, current_user: User = Depends(require_authenticated_user)):
    deleted = delete_history_entry(current_user.id, entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entri riwayat tidak ditemukan.")
    return {"status": "deleted", "id": entry_id}
