from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.db.session import Base

user_preference_association = Table(
    "user_preference_association",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("preference_id", Integer, ForeignKey("preferences.id")),
)


class Preference(Base):
    __tablename__ = "preferences"

    id = Column(Integer, primary_key=True, index=True)
    interests = Column(String)  # Storing as comma-separated string
    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="preferences")
