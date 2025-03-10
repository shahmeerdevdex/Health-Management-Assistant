from sqlalchemy.orm import Session
from app.db.models.user import User
from app.core.security import verify_password

def authenticate_user(db: Session, email: str, password: str):
    """Authenticate a user by email and password."""
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password):
        return None
    return user
