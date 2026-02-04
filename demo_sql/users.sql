CREATE TABLE IF NOT EXISTS users (
    id        TEXT PRIMARY KEY NOT NULL,
    username  TEXT NOT NULL UNIQUE,
    email     TEXT NOT NULL UNIQUE,
    group_id  TEXT,
    FOREIGN KEY (group_id) REFERENCES groups(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);
