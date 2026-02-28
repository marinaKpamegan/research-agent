from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.core.security import get_password_hash


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    preferences = relationship("Preference", back_populates="owner")

    def verify_password(self, password: str) -> bool:
        return get_password_hash(password) == self.hashed_password
