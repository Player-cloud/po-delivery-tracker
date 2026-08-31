"""
Run once against a fresh database to create the first Administrator account —
there's no public "sign up" endpoint (POST /users is admin-only, on purpose),
so the very first user has to be created directly like this.

Usage (from backend/, with venv active and .env configured):
    python -m scripts.seed_admin
"""

from getpass import getpass

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User, UserRole


def main() -> None:
    db = SessionLocal()
    try:
        email = input("Admin email: ").strip()
        password = getpass("Admin password: ").strip()

        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"A user with email {email} already exists (id={existing.id}). Nothing to do.")
            return

        admin = User(
            email=email, password_hash=hash_password(password), role=UserRole.ADMINISTRATOR
        )
        db.add(admin)
        db.commit()
        print(f"Created administrator {email} (id={admin.id}).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
