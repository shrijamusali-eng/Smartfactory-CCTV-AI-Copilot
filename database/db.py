import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime

# ==========================================================
# Database Location
# ==========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "factory.db")
PROJECT_ROOT = os.path.dirname(BASE_DIR)

print(f"📁 SQLite Database: {DB_PATH}")

# ==========================================================
# Connection Helper
# ==========================================================
@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ==========================================================
# Database Initialization
# ==========================================================
def init_db():
    with get_connection() as conn:

        # -----------------------------
        # Cameras Table
        # -----------------------------
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cameras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                zone TEXT,
                source_path TEXT,
                active INTEGER DEFAULT 1
            )
            """
        )

        # -----------------------------
        # Events Table
        # -----------------------------
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                camera TEXT,
                zone TEXT,
                worker_id INTEGER,
                event TEXT,
                severity TEXT,
                confidence REAL,
                start_time TEXT,
                end_time TEXT,
                image_path TEXT
            )
            """
        )

        # -----------------------------
        # Safe Migration: run_id Check
        # -----------------------------
        cursor = conn.execute("PRAGMA table_info(events)")
        columns = [row["name"] for row in cursor.fetchall()]
        
        if "run_id" not in columns:
            conn.execute("ALTER TABLE events ADD COLUMN run_id TEXT")
            print("🔧 Migration: Added 'run_id' column to 'events' table")

        # -----------------------------
        # Automatic Camera Seeding
        # -----------------------------
        default_cameras = [
            (
                "Camera 1", 
                "Assembly Line", 
                os.path.join(PROJECT_ROOT, "data", "factory1.mp4")
            ),
            (
                "Camera 2", 
                "Packing Area", 
                os.path.join(PROJECT_ROOT, "data", "factory2.mp4")
            ),
            (
                "Camera 3", 
                "Warehouse", 
                os.path.join(PROJECT_ROOT, "data", "factory3.mp4")
            ),
        ]

        for name, zone, source_path in default_cameras:
            # Only insert the record if the physical file exists on disk
            if os.path.exists(source_path):
                conn.execute(
                    """
                    INSERT OR IGNORE INTO cameras (name, zone, source_path)
                    VALUES (?, ?, ?)
                    """,
                    (name, zone, source_path),
                )
                print(f"✅ Camera ready: {name} -> {source_path}")
            else:
                print(f"⚠️ Camera source not found: {source_path}")

    print("✅ Database initialized")


# ==========================================================
# Camera Management
# ==========================================================
def add_camera(name, zone, source_path):
    """
    Register a camera if it does not already exist.
    """

    with get_connection() as conn:

        conn.execute(
            """
            INSERT OR IGNORE INTO cameras
            (
                name,
                zone,
                source_path
            )
            VALUES (?, ?, ?)
            """,
            (
                name,
                zone,
                source_path,
            ),
        )

    print(f"📷 Camera Registered: {name}")


def get_active_cameras():
    """
    Returns all active cameras.
    """

    with get_connection() as conn:

        cameras = conn.execute(
            """
            SELECT
                name,
                zone,
                source_path
            FROM cameras
            WHERE active = 1
            """
        ).fetchall()

    return cameras


# ==========================================================
# Save Event
# ==========================================================
def save_event(
    camera,
    zone,
    worker_id,
    event,
    severity,
    confidence,
    start_time,
    end_time,
    image_path="",
    run_id=None,
):

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:

        with get_connection() as conn:

            cursor = conn.execute(
                """
                INSERT INTO events
                (
                    timestamp,
                    camera,
                    zone,
                    worker_id,
                    event,
                    severity,
                    confidence,
                    start_time,
                    end_time,
                    image_path,
                    run_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    timestamp,
                    camera,
                    zone,
                    worker_id,
                    event,
                    severity,
                    confidence,
                    start_time,
                    end_time,
                    image_path,
                    run_id,
                ),
            )

            event_id = cursor.lastrowid

        print(
            f"✅ Event Saved | "
            f"ID={event_id} | "
            f"Camera={camera} | "
            f"Worker={worker_id} | "
            f"Violation={event} | "
            f"Zone={zone}"
        )

        return event_id

    except sqlite3.Error as e:

        print(f"❌ SQLite Error: {e}")

        return None


# ==========================================================
# Utility
# ==========================================================
def get_db_path():
    return DB_PATH