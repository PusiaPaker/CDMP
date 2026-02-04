CREATE TABLE sessions (
    id        TEXT PRIMARY KEY NOT NULL,
    user_id   TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    ttl       INTEGER NOT NULL,
    active    INTEGER NOT NULL CHECK (active IN (0,1)), -- so sqlite doesn't like BOOL so this is how we do it
    FOREIGN KEY (user_id) REFERENCES users(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
));
