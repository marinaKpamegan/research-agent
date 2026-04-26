from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(str(settings.DATABASE_URL))
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE feeds ADD COLUMN crawled_sources TEXT;"))
        conn.commit()
        print("Column 'crawled_sources' added successfully.")
    except Exception as e:
        print("Error:", e)
