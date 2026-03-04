from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.core.security import verify_password as _verify_password


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)

    preferences = relationship("Preference", back_populates="owner")

    def verify_password(self, plain_password: str) -> bool:
        return _verify_password(plain_password, self.password)
