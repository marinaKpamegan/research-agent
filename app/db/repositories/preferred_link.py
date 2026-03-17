from sqlalchemy.orm import Session
from app.db.models.preferred_link import PreferredLink
from app.schemas.preferred_link import PreferredLinkCreate, PreferredLinkUpdate

class PreferredLinkRepository:
    def __init__(self, db: Session):
        self.db = db

    # def get_preferred_link(self, link_id: int):
    #     return self.db.query(PreferredLink).filter(PreferredLink.id == link_id).first()

    def get_user_preferred_links(self, user_id: int):
        return self.db.query(PreferredLink).filter(PreferredLink.user_id == user_id).all()

    def create_preferred_link(self, link: PreferredLinkCreate, user_id: int):
        # Check if the link already exists for this user
        existing_link = self.db.query(PreferredLink).filter(
            PreferredLink.user_id == user_id,
            PreferredLink.url == link.url
        ).first()
        
        if existing_link:
            # If it exists, update is_trusted if it changed, and return it
            if existing_link.is_trusted != link.is_trusted:
                existing_link.is_trusted = link.is_trusted
                self.db.commit()
                self.db.refresh(existing_link)
            return existing_link

        db_link = PreferredLink(**link.dict(), user_id=user_id)
        self.db.add(db_link)
        self.db.commit()
        self.db.refresh(db_link)
        return db_link

    def update_preferred_link(self, db_link: PreferredLink, link: PreferredLinkUpdate):
        for key, value in link.dict(exclude_unset=True).items():
            setattr(db_link, key, value)
        self.db.commit()
        self.db.refresh(db_link)
        return db_link

    def delete_preferred_link(self, link_id: int):
        db_link = self.db.query(PreferredLink).filter(PreferredLink.id == link_id).first()
        if db_link:
            self.db.delete(db_link)
            self.db.commit()
        return db_link
