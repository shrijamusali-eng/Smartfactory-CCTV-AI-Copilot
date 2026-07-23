import os
import sys

# Add project root to Python path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from database.db import add_camera

VIDEO = "data/factory.mp4"

add_camera(
    "Camera 1",
    "Assembly Line",
    VIDEO,
)

add_camera(
    "Camera 2",
    "Packing Area",
    VIDEO,
)

add_camera(
    "Camera 3",
    "Warehouse",
    VIDEO,
)

print("✅ Cameras added successfully.")