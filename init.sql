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
    preferred_links VARCHAR,
    owner_id INTEGER REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_preferences_id ON preferences (id);

-- User-Preference association table (Many-to-Many if needed, though models show One-to-Many as well)
CREATE TABLE IF NOT EXISTS user_preference_association (
    user_id INTEGER REFERENCES users (id) ON DELETE CASCADE,
    preference_id INTEGER REFERENCES preferences (id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, preference_id)
);