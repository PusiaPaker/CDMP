CREATE TABLE IF NOT EXISTS groups (
    id          TEXT PRIMARY KEY NOT NULL,
    project_id  TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
)
