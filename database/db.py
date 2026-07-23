import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime

# ==========================================================
# Database Location
# ==========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "factory.db")

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
                    image_path
                )

                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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