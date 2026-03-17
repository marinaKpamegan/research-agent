from sqlalchemy.orm import Session
from app.db.models.feed import Feed
from app.schemas.feed import FeedCreate, FeedUpdate
from app.db.models.preferred_link import PreferredLink

def get_feed(db: Session, feed_id: int):
    return db.query(Feed).filter(Feed.id == feed_id).first()

def get_user_feeds(db: Session, user_id: int):
    return db.query(Feed).filter(Feed.user_id == user_id).all()

def create_feed(db: Session, feed: FeedCreate, user_id: int):
    # Extract interests as comma-separated string if provided
    interests_str = ",".join(feed.interests) if feed.interests else ""
    
    db_feed = Feed(
        title=feed.title,
        interests=interests_str,
        tag=feed.tag,
        ai_summary=feed.ai_summary,
        user_id=user_id
    )
    
    # Associate sources
    if feed.source_ids:
        sources = db.query(PreferredLink).filter(PreferredLink.id.in_(feed.source_ids)).all()
        db_feed.sources = sources
    
    db.add(db_feed)
    db.commit()
    db.refresh(db_feed)
    return db_feed

def update_feed(db: Session, db_feed: Feed, feed: FeedUpdate):
    feed_data = feed.dict(exclude_unset=True)
    
    if "interests" in feed_data:
        db_feed.interests = ",".join(feed_data["interests"]) if feed_data["interests"] else ""
        del feed_data["interests"]
        
    if "source_ids" in feed_data:
        sources = db.query(PreferredLink).filter(PreferredLink.id.in_(feed_data["source_ids"])).all()
        db_feed.sources = sources
        del feed_data["source_ids"]
        
    for key, value in feed_data.items():
        setattr(db_feed, key, value)
        
    db.commit()
    db.refresh(db_feed)
    return db_feed
