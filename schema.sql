DROP TABLE IF EXISTS challenges;

CREATE TABLE challenges (
  id TEXT PRIMARY KEY,
  text TEXT NOT NULL,
  expires_at INTEGER NOT NULL
);
