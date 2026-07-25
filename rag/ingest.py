import os
import traceback
import chromadb
from chromadb.config import Settings

CHROMA_PATH = "database/chroma"
os.makedirs(CHROMA_PATH, exist_ok=True)

try:
    client = chromadb.PersistentClient(
        path=CHROMA_PATH,
        settings=Settings(anonymized_telemetry=False)
    )
    print("✅ Chroma client created successfully")
except Exception:
    print("❌ FAILED at PersistentClient init")
    traceback.print_exc()
    raise

try:
    print("Existing collections:")
    print(client.list_collections())
except Exception:
    print("❌ FAILED at list_collections()")
    traceback.print_exc()
    raise

try:
    collection = client.get_or_create_collection(name="factory_incidents")
    print("✅ Collection created successfully")
except Exception:
    print("❌ FAILED at get_or_create_collection()")
    traceback.print_exc()
    raise