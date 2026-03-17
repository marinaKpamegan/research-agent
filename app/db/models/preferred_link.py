from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base
from urllib.parse import urlparse

class PreferredLink(Base):
    __tablename__ = "preferred_links"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False)
    name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="preferred_links")
    feeds = relationship("Feed", secondary="feed_link_association", back_populates="sources")

    def __init__(self, **kwargs):
        if "name" not in kwargs and "url" in kwargs:
            # Extract domain name if name is missing
            domain = urlparse(kwargs["url"]).netloc
            if domain.startswith("www."):
                domain = domain[4:]
            kwargs["name"] = domain.split('.')[0].capitalize() if domain else "Unknown Source"
        super().__init__(**kwargs)
