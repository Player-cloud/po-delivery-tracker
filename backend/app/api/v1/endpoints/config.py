from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.crud.configuration import get_thresholds, set_thresholds
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.config import ThresholdsOut, ThresholdsUpdate

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/thresholds", response_model=ThresholdsOut)
def read_thresholds(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMINISTRATOR)),
):
    return ThresholdsOut(thresholds_days=get_thresholds(db))


@router.put("/thresholds", response_model=ThresholdsOut)
def update_thresholds(
    data: ThresholdsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMINISTRATOR)),
):
    updated = set_thresholds(db, data.thresholds_days)
    return ThresholdsOut(thresholds_days=updated)
