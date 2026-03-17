import sys
from pathlib import Path
from urllib.parse import urlparse

# Add project root to sys.path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from app.db.models.user import User
from app.db.models.feed import Feed
from app.db.models.preferred_link import PreferredLink

def test_name_extraction():
    urls = [
        ("https://openai.com/fr-FR/news/", "openai"),
        ("https://www.google.com/search", "google"),
        ("http://github.com/marinaKpamegan", "github"),
        ("https://subdomain.example.co.uk/path", "subdomain"),
    ]

    for url, expected_name in urls:
        # Test with name=None
        link1 = PreferredLink(url=url, name=None)
        print(f"URL: {url} -> Extracted: {link1.name} (Expected: {expected_name})")
        assert link1.name == expected_name

        # Test with name=""
        link2 = PreferredLink(url=url, name="")
        assert link2.name == expected_name

        # Test with name provided
        link3 = PreferredLink(url=url, name="My Source")
        assert link3.name == "My Source"

    print("\n✅ Name extraction tests passed!")

if __name__ == "__main__":
    test_name_extraction()
