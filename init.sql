-- Initial schema creation for research-agent

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR UNIQUE NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    password VARCHAR NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_users_id ON users (id);
CREATE INDEX IF NOT EXISTS ix_users_username ON users (username);
CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);

-- Preferences table
CREATE TABLE IF NOT EXISTS preferences (
    id SERIAL PRIMARY KEY,
    interests VARCHAR,
    --- preferred_links VARCHAR,
    user_id INTEGER REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_preferences_id ON preferences (id);

-- User-Preference association table
CREATE TABLE IF NOT EXISTS user_preference_association (
    user_id INTEGER REFERENCES users (id) ON DELETE CASCADE,
    preference_id INTEGER REFERENCES preferences (id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, preference_id)
);

-- Preferred Links (Sources) table
CREATE TABLE IF NOT EXISTS preferred_links (
    id SERIAL PRIMARY KEY,
    url VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    user_id INTEGER REFERENCES users (id) ON DELETE CASCADE,
    is_trusted BOOLEAN DEFAULT FALSE,
    UNIQUE (user_id, url)
);

CREATE INDEX IF NOT EXISTS ix_preferred_links_id ON preferred_links (id);

-- Feeds table
CREATE TABLE IF NOT EXISTS feeds (
    id SERIAL PRIMARY KEY,
    title VARCHAR NOT NULL,
    interests VARCHAR,
    tag VARCHAR,
    ai_summary TEXT,
    date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_feeds_id ON feeds (id);

-- Feed-Source association table (Many-to-Many)
CREATE TABLE IF NOT EXISTS feed_link_association (
    feed_id INTEGER REFERENCES feeds (id) ON DELETE CASCADE,
    link_id INTEGER REFERENCES preferred_links (id) ON DELETE CASCADE,
    PRIMARY KEY (feed_id, link_id)
);