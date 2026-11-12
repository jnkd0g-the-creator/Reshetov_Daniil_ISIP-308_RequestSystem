PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS Roles (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS Users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE CHECK(length(username) BETWEEN 3 AND 50),
    name TEXT NOT NULL CHECK(length(trim(name)) BETWEEN 1 AND 100),
    role_code TEXT NOT NULL REFERENCES Roles(code) ON DELETE RESTRICT,
    password_hash TEXT NOT NULL DEFAULT '!unset',
    active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0, 1))
);
CREATE TABLE IF NOT EXISTS Cafes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    address TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS Categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS Statuses (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    sort_order INTEGER NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS Requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL CHECK(length(trim(title)) BETWEEN 3 AND 120),
    description TEXT NOT NULL CHECK(length(trim(description)) BETWEEN 10 AND 4000),
    cafe_id INTEGER NOT NULL REFERENCES Cafes(id) ON DELETE RESTRICT,
    category_id INTEGER NOT NULL REFERENCES Categories(id) ON DELETE RESTRICT,
    status_code TEXT NOT NULL DEFAULT 'new' REFERENCES Statuses(code) ON DELETE RESTRICT,
    applicant_id INTEGER NOT NULL REFERENCES Users(id) ON DELETE RESTRICT,
    assignee_id INTEGER REFERENCES Users(id) ON DELETE RESTRICT,
    priority TEXT NOT NULL DEFAULT 'normal' CHECK(priority IN ('low','normal','high','urgent')),
    archived INTEGER NOT NULL DEFAULT 0 CHECK(archived IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE TABLE IF NOT EXISTS Comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL REFERENCES Requests(id) ON DELETE RESTRICT,
    author_id INTEGER NOT NULL REFERENCES Users(id) ON DELETE RESTRICT,
    body TEXT NOT NULL CHECK(length(trim(body)) BETWEEN 1 AND 2000),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE TABLE IF NOT EXISTS RequestHistory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL REFERENCES Requests(id) ON DELETE RESTRICT,
    actor_id INTEGER NOT NULL REFERENCES Users(id) ON DELETE RESTRICT,
    event TEXT NOT NULL CHECK(event IN ('created','updated','assigned','status_changed','archived','seeded')),
    old_value TEXT,
    new_value TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE TABLE IF NOT EXISTS Sessions (
    token_hash TEXT PRIMARY KEY,
    csrf_hash TEXT NOT NULL,
    user_id INTEGER NOT NULL REFERENCES Users(id) ON DELETE CASCADE,
    expires_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_requests_status_category ON Requests(archived, status_code, category_id);
CREATE INDEX IF NOT EXISTS idx_requests_applicant ON Requests(applicant_id, archived);
CREATE INDEX IF NOT EXISTS idx_requests_assignee ON Requests(assignee_id, archived);
CREATE INDEX IF NOT EXISTS idx_comments_request ON Comments(request_id, id);
CREATE INDEX IF NOT EXISTS idx_history_request ON RequestHistory(request_id, id);
CREATE INDEX IF NOT EXISTS idx_sessions_expiry ON Sessions(expires_at);
PRAGMA user_version = 1;
