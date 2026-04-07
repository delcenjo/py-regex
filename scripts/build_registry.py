#!/usr/bin/env python3
import os
import yaml
import sqlite3
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

DB_PATH = "registry.db"
CATALOG_ROOT = "catalog"

def create_schema(db):
    cursor = db.cursor()
    cursor.execute("DROP TABLE IF EXISTS patterns")
    cursor.execute("""
        CREATE TABLE patterns (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            l1          TEXT NOT NULL,
            l2          TEXT NOT NULL,
            l3          TEXT NOT NULL,
            l4          TEXT NOT NULL,
            full_path   TEXT NOT NULL UNIQUE,
            title       TEXT,
            description TEXT,
            data_json   TEXT,  -- The full YAML object as JSON
            tags        TEXT,  -- JSON list of tags
            priority    INTEGER DEFAULT 100
        )
    """)
    cursor.execute("CREATE INDEX idx_full_path ON patterns(full_path)")
    cursor.execute("CREATE INDEX idx_hierarchical ON patterns(l1, l2, l3)")
    db.commit()

def build_registry():
    if not os.path.exists(CATALOG_ROOT):
        logger.error(f"Catalog root '{CATALOG_ROOT}' not found.")
        return

    db = sqlite3.connect(DB_PATH)
    create_schema(db)
    cursor = db.cursor()

    count = 0
    for root, dirs, files in os.walk(CATALOG_ROOT):
        if "wizard.yaml" in files:
            yaml_path = os.path.join(root, "wizard.yaml")
            
            # Extract hierarchy from relative path
            # catalog/communication/telecom/mobile_cellular_phone_numbers/wizard.yaml
            rel_path = os.path.relpath(root, CATALOG_ROOT)
            parts = rel_path.split(os.sep)
            
            if len(parts) < 4:
                logger.warning(f"Skipping {yaml_path}: Incomplete hierarchy depth.")
                continue
                
            l1, l2, l3, l4 = parts[0], parts[1], parts[2], parts[3]
            full_path = ".".join(parts)

            try:
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    
                if not data:
                    logger.warning(f"Empty YAML at {yaml_path}")
                    continue

                metadata = data.get('metadata', {})
                tags = json.dumps(metadata.get('tags', []))
                
                cursor.execute("""
                    INSERT INTO patterns (l1, l2, l3, l4, full_path, title, description, data_json, tags, priority)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    l1, l2, l3, l4, 
                    full_path, 
                    metadata.get('title'), 
                    metadata.get('description'), 
                    json.dumps(data), 
                    tags,
                    metadata.get('priority', 100)
                ))
                count += 1
                logger.debug(f"Indexed: {full_path}")

            except Exception as e:
                logger.error(f"Error parsing {yaml_path}: {e}")

    db.commit()
    db.close()
    logger.info(f"Registry build complete! Indexed {count} wizards into {DB_PATH}.")

if __name__ == "__main__":
    build_registry()
