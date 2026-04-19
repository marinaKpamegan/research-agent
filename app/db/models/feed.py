from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

# Many-to-Many association between Feed and PreferredLink
feed_link_association = Table(
    "feed_link_association",
    Base.metadata,
    Column("feed_id", Integer, ForeignKey("feeds.id"), primary_key=True),
    Column("link_id", Integer, ForeignKey("preferred_links.id"), primary_key=True),
)

class Feed(Base):
    __tablename__ = "feeds"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    interests = Column(String)  # Stored as comma-separated string for simplicity
    tag = Column(String)
    ai_summary = Column(Text)
    ragas_faithfulness = Column(Float)
    ragas_answer_relevance = Column(Float)
    bm25_relevance = Column(Float)
    crawled_sources = Column(Text)
    date = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="feeds")
    sources = relationship("PreferredLink", secondary=feed_link_association, back_populates="feeds")
