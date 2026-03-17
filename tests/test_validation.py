import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from app.schemas.preference import Preference
from app.schemas.feed import Feed
from datetime import datetime

def test_validation():
    print("Testing Preference validation...")
    pref_data = {
        "id": 1,
        "user_id": 1,
        "interests": "AI,Machine Learning"
    }
    pref = Preference.model_validate(pref_data)
    print(f"✅ Preference interests: {pref.interests} (Type: {type(pref.interests)})")
    assert pref.interests == ["AI", "Machine Learning"]

    print("\nTesting Feed validation...")
    feed_data = {
        "id": 1,
        "user_id": 1,
        "title": "Tech Feed",
        "date": datetime.now(),
        "interests": "Python,FastAPI",
        "sources": []
    }
    feed = Feed.model_validate(feed_data)
    print(f"✅ Feed interests: {feed.interests} (Type: {type(feed.interests)})")
    assert feed.interests == ["Python", "FastAPI"]

    print("\nAll validation tests passed!")

if __name__ == "__main__":
    try:
        test_validation()
    except Exception as e:
        print(f"❌ Validation failed: {e}")
