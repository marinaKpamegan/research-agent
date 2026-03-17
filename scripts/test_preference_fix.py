import asyncio
import sys
import os

# Add project root to sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine, Base
from app.db.repositories.preference import create_user_preferences
from app.schemas.preference import PreferenceCreate
from app.db.models.user import User

async def test_create_preferences():
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Create a test user if not exists
        test_user = db.query(User).filter(User.username == "test_pref_user").first()
        if not test_user:
            test_user = User(username="test_pref_user", email="test@pref.com", password="hashed_password")
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            print(f"Created test user with id {test_user.id}")
        
        pref_data = PreferenceCreate(
            interests=["AI", "Python", "Space"],
            preferred_links=["https://google.com"]
        )
        
        print(f"Attempting to create preferences for user {test_user.id}...")
        prefs = create_user_preferences(db=db, preferences=pref_data, user_id=test_user.id)
        
        print(f"Success! Created preferences with id {prefs.id}")
        print(f"Interests saved: {prefs.interests}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_create_preferences())
