from sqlalchemy.orm import Session
from app.db.models.preferred_link import PreferredLink
from app.schemas.preferred_link import PreferredLinkCreate, PreferredLinkUpdate

def get_preferred_link(db: Session, link_id: int):
    return db.query(PreferredLink).filter(PreferredLink.id == link_id).first()

def get_user_preferred_links(db: Session, user_id: int):
    return db.query(PreferredLink).filter(PreferredLink.user_id == user_id).all()

def create_preferred_link(db: Session, link: PreferredLinkCreate, user_id: int):
    db_link = PreferredLink(**link.dict(), user_id=user_id)
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    return db_link

def update_preferred_link(db: Session, db_link: PreferredLink, link: PreferredLinkUpdate):
    for key, value in link.dict(exclude_unset=True).items():
        setattr(db_link, key, value)
    db.commit()
    db.refresh(db_link)
    return db_link

def delete_preferred_link(db: Session, link_id: int):
    db_link = db.query(PreferredLink).filter(PreferredLink.id == link_id).first()
    if db_link:
        db.delete(db_link)
        db.commit()
    return db_link
