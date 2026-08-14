PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS builds (
    id TEXT PRIMARY KEY,
    bundle_id TEXT NOT NULL,
    version TEXT NOT NULL,
    executable_name TEXT NOT NULL,
    minimum_os TEXT,
    app_path TEXT NOT NULL,
    executable_size INTEGER NOT NULL,
    executable_sha256 TEXT NOT NULL,
    catalogued_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS slices (
    build_id TEXT NOT NULL REFERENCES builds(id),
    architecture TEXT NOT NULL,
    machine TEXT,
    bits INTEGER NOT NULL,
    size INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    encrypted INTEGER NOT NULL,
    stripped INTEGER,
    PRIMARY KEY (build_id, architecture)
);

CREATE TABLE IF NOT EXISTS sections (
    build_id TEXT NOT NULL,
    architecture TEXT NOT NULL,
    name TEXT NOT NULL,
    virtual_address INTEGER NOT NULL,
    physical_address INTEGER NOT NULL,
    size INTEGER NOT NULL,
    permissions TEXT,
    PRIMARY KEY (build_id, architecture, name),
    FOREIGN KEY (build_id, architecture)
        REFERENCES slices(build_id, architecture)
);

CREATE TABLE IF NOT EXISTS libraries (
    build_id TEXT NOT NULL,
    architecture TEXT NOT NULL,
    path TEXT NOT NULL,
    PRIMARY KEY (build_id, architecture, path),
    FOREIGN KEY (build_id, architecture)
        REFERENCES slices(build_id, architecture)
);

CREATE TABLE IF NOT EXISTS symbols (
    build_id TEXT NOT NULL,
    architecture TEXT NOT NULL,
    ordinal INTEGER NOT NULL,
    name TEXT NOT NULL,
    demangled_name TEXT,
    bind TEXT,
    symbol_type TEXT,
    virtual_address INTEGER,
    physical_address INTEGER,
    size INTEGER,
    imported INTEGER NOT NULL,
    PRIMARY KEY (build_id, architecture, ordinal),
    FOREIGN KEY (build_id, architecture)
        REFERENCES slices(build_id, architecture)
);

CREATE INDEX IF NOT EXISTS symbols_by_name
    ON symbols(build_id, architecture, name);

CREATE TABLE IF NOT EXISTS objc_classes (
    build_id TEXT NOT NULL,
    architecture TEXT NOT NULL,
    name TEXT NOT NULL,
    superclass TEXT,
    address INTEGER,
    PRIMARY KEY (build_id, architecture, name),
    FOREIGN KEY (build_id, architecture)
        REFERENCES slices(build_id, architecture)
);

CREATE TABLE IF NOT EXISTS objc_methods (
    build_id TEXT NOT NULL,
    architecture TEXT NOT NULL,
    class_name TEXT NOT NULL,
    selector TEXT NOT NULL,
    address INTEGER,
    is_class_method INTEGER NOT NULL,
    PRIMARY KEY (build_id, architecture, class_name, selector, is_class_method),
    FOREIGN KEY (build_id, architecture, class_name)
        REFERENCES objc_classes(build_id, architecture, name)
);

CREATE TABLE IF NOT EXISTS objc_fields (
    build_id TEXT NOT NULL,
    architecture TEXT NOT NULL,
    class_name TEXT NOT NULL,
    name TEXT NOT NULL,
    address INTEGER,
    PRIMARY KEY (build_id, architecture, class_name, name),
    FOREIGN KEY (build_id, architecture, class_name)
        REFERENCES objc_classes(build_id, architecture, name)
);

CREATE TABLE IF NOT EXISTS object_files (
    build_id TEXT NOT NULL REFERENCES builds(id),
    name TEXT NOT NULL,
    PRIMARY KEY (build_id, name)
);

CREATE TABLE IF NOT EXISTS resources (
    build_id TEXT NOT NULL REFERENCES builds(id),
    relative_path TEXT NOT NULL,
    extension TEXT NOT NULL,
    size INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    PRIMARY KEY (build_id, relative_path)
);

CREATE INDEX IF NOT EXISTS resources_by_extension
    ON resources(build_id, extension);

CREATE TABLE IF NOT EXISTS content_entries (
    build_id TEXT NOT NULL REFERENCES builds(id),
    id TEXT NOT NULL,
    kind TEXT NOT NULL,
    source_path TEXT NOT NULL,
    source_offset INTEGER,
    source_size INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    label TEXT NOT NULL,
    confidence TEXT NOT NULL CHECK (
        confidence IN ('confirmed', 'probable', 'editorial', 'unknown')
    ),
    extracted INTEGER NOT NULL DEFAULT 0,
    linked INTEGER NOT NULL DEFAULT 0,
    understood INTEGER NOT NULL DEFAULT 0,
    presented INTEGER NOT NULL DEFAULT 0,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    PRIMARY KEY (build_id, id)
);

CREATE INDEX IF NOT EXISTS content_entries_by_kind
    ON content_entries(build_id, kind);

CREATE TABLE IF NOT EXISTS content_relationships (
    build_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    relation TEXT NOT NULL,
    target_id TEXT NOT NULL,
    evidence TEXT NOT NULL,
    PRIMARY KEY (build_id, source_id, relation, target_id),
    FOREIGN KEY (build_id, source_id)
        REFERENCES content_entries(build_id, id),
    FOREIGN KEY (build_id, target_id)
        REFERENCES content_entries(build_id, id)
);

CREATE TABLE IF NOT EXISTS consumer_callsites (
    build_id TEXT NOT NULL,
    content_id TEXT NOT NULL,
    architecture TEXT NOT NULL,
    address INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    relationship TEXT NOT NULL,
    evidence TEXT NOT NULL,
    PRIMARY KEY (build_id, content_id, architecture, address, relationship),
    FOREIGN KEY (build_id, content_id)
        REFERENCES content_entries(build_id, id),
    FOREIGN KEY (build_id, architecture)
        REFERENCES slices(build_id, architecture)
);

CREATE TABLE IF NOT EXISTS map_pack_records (
    build_id TEXT NOT NULL,
    entry_id TEXT NOT NULL,
    pack_path TEXT NOT NULL,
    pack_version INTEGER NOT NULL,
    record_index INTEGER NOT NULL,
    PRIMARY KEY (build_id, entry_id),
    UNIQUE (build_id, pack_path, record_index),
    FOREIGN KEY (build_id, entry_id)
        REFERENCES content_entries(build_id, id)
);

CREATE TABLE IF NOT EXISTS localized_strings (
    build_id TEXT NOT NULL,
    entry_id TEXT NOT NULL,
    locale TEXT NOT NULL,
    table_name TEXT NOT NULL,
    string_key TEXT NOT NULL,
    value TEXT NOT NULL,
    PRIMARY KEY (build_id, entry_id),
    UNIQUE (build_id, locale, table_name, string_key),
    FOREIGN KEY (build_id, entry_id)
        REFERENCES content_entries(build_id, id)
);

CREATE TABLE IF NOT EXISTS yas_headers (
    build_id TEXT NOT NULL,
    entry_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    header_words_json TEXT NOT NULL,
    texture_name TEXT,
    PRIMARY KEY (build_id, entry_id),
    FOREIGN KEY (build_id, entry_id)
        REFERENCES content_entries(build_id, id)
);

CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY,
    build_id TEXT NOT NULL REFERENCES builds(id),
    subsystem TEXT NOT NULL,
    evidence_level TEXT NOT NULL CHECK (
        evidence_level IN ('fact', 'observed', 'inferred', 'hypothesis')
    ),
    summary TEXT NOT NULL,
    evidence TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open'
);
