from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def get_user(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.email)))


def list_active_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).where(User.active.is_(True)).order_by(User.email)))


def create_user(db: Session, data: UserCreate) -> User:
    user = User(email=data.email, password_hash=hash_password(data.password), role=data.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User, data: UserUpdate) -> User:
    updates = data.model_dump(exclude_unset=True)
    password = updates.pop("password", None)
    if password:
        user.password_hash = hash_password(password)
    for field, value in updates.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user
