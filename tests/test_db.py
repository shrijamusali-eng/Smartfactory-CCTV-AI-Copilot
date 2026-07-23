import sys
import os

# Fix paths so the test script can locate your database folder cleanly
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from database.db import init_db, save_event, get_connection

# 1. Initialize the database schema
print("Initializing database...")
init_db()

# 2. Insert a mock sample violation entry
print("Inserting mock safety event...")
save_event(
    timestamp="2026-06-22 10:00:00",
    camera="Cam-01",
    zone="Loading Dock",
    worker_id=101,
    event="NO-Hardhat",
    severity="High",
    image_path="database/alerts/mock.jpg"
)

# 3. Read it back out to verify success
print("Reading data back out to verify...")
with get_connection() as conn:
    cursor = conn.execute("SELECT * FROM events")
    rows = cursor.fetchall()
    
    print("\n--- Database Content ---")
    for row in rows:
        print(row)
    print("------------------------\n")
    
print("Database test completed successfully!")