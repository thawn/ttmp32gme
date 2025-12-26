"""Database update module for ttmp32gme."""

from packaging.version import Version

# Database update SQL statements
UPDATES = {
    "0.1.0": """
UPDATE "config" SET value='0.1.0' WHERE param='version';
""",
    "0.2.0": """
UPDATE "config" SET value='0.2.0' WHERE param='version';
""",
    "0.2.1": """
UPDATE "config" SET value='0.2.1' WHERE param='version';
""",
    "0.2.3": """
UPDATE "config" SET value='0.2.3' WHERE param='version';
INSERT INTO "config" ("param", "value") VALUES ('pen_language', 'GERMAN');
""",
    "0.3.0": """
UPDATE "config" SET value='0.3.0' WHERE param='version';
INSERT INTO "config" ("param", "value") VALUES ('library_path', '');
INSERT INTO "config" ("param", "value") VALUES ('player_mode', 'music');
""",
    "0.3.1": """
UPDATE "config" SET value='0.3.1' WHERE param='version';
DELETE FROM "config" WHERE param='player_mode';
ALTER TABLE "gme_library" ADD COLUMN "player_mode" TEXT DEFAULT 'music';
""",
    "1.0.0": """
UPDATE "config" SET value='1.0.0' WHERE param='version';
""",
}


def update(db_version: str, connection) -> bool:
    """Update database schema to latest version.
    
    Args:
        db_version: Current database version string
        connection: Database connection object
        
    Returns:
        True if update successful
    """
    current_version = Version(db_version)
    cursor = connection.cursor()
    
    for version_str in sorted(UPDATES.keys(), key=Version):
        update_version = Version(version_str)
        if update_version > current_version:
            try:
                cursor.executescript(UPDATES[version_str])
                connection.commit()
            except Exception as e:
                connection.rollback()
                raise RuntimeError(f"Can't update config file.\n\tError: {e}")
    
    return True
