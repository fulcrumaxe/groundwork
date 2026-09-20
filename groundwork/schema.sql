-- Groundwork SQLite schema: one process, one database file.
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS modules (
  id TEXT PRIMARY KEY,
  repo TEXT NOT NULL,
  commit_range TEXT NOT NULL DEFAULT '',
  task_summary TEXT NOT NULL DEFAULT '',
  learner_level TEXT NOT NULL DEFAULT 'intermediate',
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
  source_markdown TEXT NOT NULL DEFAULT '',
  lessons TEXT NOT NULL DEFAULT '[]',
  purpose TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS concepts (
  id TEXT PRIMARY KEY,
  module_id TEXT NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  kind TEXT NOT NULL DEFAULT 'function',
  file TEXT NOT NULL DEFAULT '',
  line INTEGER NOT NULL DEFAULT 0,
  file_hash TEXT NOT NULL DEFAULT '',
  bloom TEXT NOT NULL DEFAULT 'recall',
  mastery REAL NOT NULL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS cards (
  id TEXT PRIMARY KEY,
  concept_id TEXT NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
  exercise_type TEXT NOT NULL,
  front TEXT NOT NULL DEFAULT '',
  back TEXT NOT NULL DEFAULT '',
  payload TEXT NOT NULL DEFAULT '{}',
  stability REAL NOT NULL DEFAULT 1.0,
  difficulty REAL NOT NULL DEFAULT 0.5,
  retrievability REAL NOT NULL DEFAULT 1.0,
  due TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
  stale INTEGER NOT NULL DEFAULT 0,
  lapses INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS reviews (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  card_id TEXT NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
  grade INTEGER NOT NULL,
  confidence INTEGER NOT NULL DEFAULT 3,
  reviewed_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
  submission TEXT NOT NULL DEFAULT '',
  prev_stability REAL NOT NULL DEFAULT 0,
  prev_difficulty REAL NOT NULL DEFAULT 0,
  prev_retrievability REAL NOT NULL DEFAULT 0,
  prev_due TEXT NOT NULL DEFAULT '',
  prev_lapses INTEGER NOT NULL DEFAULT 0,
  prev_mastery REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS decisions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  repo TEXT NOT NULL,
  symbol TEXT NOT NULL DEFAULT '',
  chosen TEXT NOT NULL,
  rejected TEXT NOT NULL DEFAULT '',
  reason TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS holes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  repo TEXT NOT NULL,
  file TEXT NOT NULL,
  line INTEGER NOT NULL DEFAULT 0,
  spec TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'open',
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS clarity_ratings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  concept_id TEXT NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
  score INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS known_skips (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  concept_id TEXT NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
  verify_due TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS disputes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  card_id TEXT NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
  reason TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'open',
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE INDEX IF NOT EXISTS idx_cards_due ON cards(due);
CREATE INDEX IF NOT EXISTS idx_cards_concept ON cards(concept_id);
CREATE INDEX IF NOT EXISTS idx_concepts_module ON concepts(module_id);
