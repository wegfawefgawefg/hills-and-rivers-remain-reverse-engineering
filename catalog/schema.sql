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
