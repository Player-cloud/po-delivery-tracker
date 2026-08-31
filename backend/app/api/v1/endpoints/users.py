from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.crud import user as user_crud
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.user import AssignableUser, UserCreate, UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMINISTRATOR)),
):
    return user_crud.list_users(db)


@router.get("/assignable", response_model=list[AssignableUser])
def list_assignable_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.STAFF, UserRole.MANAGER, UserRole.ADMINISTRATOR)
    ),
):
    """Active users only — for the 'Assigned To' picker on the PO line forms.
    Available to anyone who can create or edit a PO line, not just Administrators."""
    return user_crud.list_active_users(db)


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMINISTRATOR)),
):
    if user_crud.get_user_by_email(db, data.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    return user_crud.create_user(db, data)


@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMINISTRATOR)),
):
    user = user_crud.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # An admin can't lock themselves out. (Any other admin remains free to act,
    # so there's always at least one active administrator left.)
    fields = data.model_dump(exclude_unset=True)
    self_losing_admin = user.id == current_user.id and (
        ("role" in fields and fields["role"] != UserRole.ADMINISTRATOR)
        or fields.get("active") is False
    )
    if self_losing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot remove your own administrator access or deactivate yourself",
        )

    return user_crud.update_user(db, user, data)
