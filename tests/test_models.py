import sys
from pathlib import Path

# Add app directory to sys.path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine, Base
from app.db.models.user import User
from app.db.models.preferred_link import PreferredLink
from app.db.models.feed import Feed
from app.db.repositories import preferred_link as source, feed as feed_crud
from app.schemas.preferred_link import PreferredLinkCreate
from app.schemas.feed import FeedCreate
import logging

# Ensure tables are created (in case of local sqlite or if DB is reachable)
# Note: In a real environment, we'd use migrations.
Base.metadata.create_all(bind=engine)

def test_models():
    db = SessionLocal()
    try:
        print("Testing models and CRUD...")
        
        # 1. Get or create a test user
        user = db.query(User).filter(User.username == "testuser").first()
        if not user:
            user = User(username="testuser", email="test@example.com", password="hash")
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # 2. Create PreferredLinks
        link1_data = PreferredLinkCreate(url="https://google.com", name="Google")
        link2_data = PreferredLinkCreate(url="https://github.com") # Name should be extracted
        
        l1 = source.create_preferred_link(db, link1_data, user.id)
        l2 = source.create_preferred_link(db, link2_data, user.id)
        
        print(f"✅ Created PreferredLink 1: {l1.name} ({l1.url})")
        print(f"✅ Created PreferredLink 2 (extracted name): {l2.name} ({l2.url})")
        
        # 3. Create a Feed
        feed_data = FeedCreate(
            title="Tech Watch",
            interests=["AI", "Python"],
            tag="High",
            ai_summary="Summary of tech trends",
            source_ids=[l1.id, l2.id]
        )
        
        f = feed_crud.create_feed(db, feed_data, user.id)
        print(f"✅ Created Feed: {f.title} with {len(f.sources)} sources")
        
        # 4. Verify relationships
        db.refresh(f)
        source_names = [s.name for s in f.sources]
        print(f"✅ Feed sources: {source_names}")
        
        if "Google" in source_names and "Github" in source_names:
            print("✅ Relationships verified successfully!")
        else:
             print("❌ Relationships mismatch.")

        # Cleanup test data (optional, but good for repeatability)
        db.delete(f)
        db.delete(l1)
        db.delete(l2)
        # We keep the user for other tests
        db.commit()
        print("✅ Cleanup done.")

    except Exception as e:
        print(f"❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_models()
