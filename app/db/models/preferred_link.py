from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db.session import Base
from urllib.parse import urlparse

class PreferredLink(Base):
    __tablename__ = "preferred_links"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False)
    name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    is_trusted = Column(Boolean, default=False)

    owner = relationship("User", back_populates="preferred_links")
    feeds = relationship("Feed", secondary="feed_link_association", back_populates="sources")

    def __init__(self, **kwargs):
        # Extract domain name if name is missing or empty
        if ("name" not in kwargs or not kwargs["name"]) and "url" in kwargs:
            url = kwargs["url"]
            try:
                domain = urlparse(url).netloc
                if domain.startswith("www."):
                    domain = domain[4:]
                
                # Take the first part of the domain (e.g., 'openai' from 'openai.com')
                extracted_name = domain.split('.')[0] if domain else "unknown"
                kwargs["name"] = extracted_name.lower()
            except Exception:
                kwargs["name"] = "unknown"
                
        super().__init__(**kwargs)
