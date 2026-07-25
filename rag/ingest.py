import os
import shutil
import chromadb
from chromadb.config import Settings

CHROMA_PATH = "database/chroma"

os.makedirs(CHROMA_PATH, exist_ok=True)

try:
    client = chromadb.PersistentClient(
        path=CHROMA_PATH,
        settings=Settings(anonymized_telemetry=False)
    )
    collection = client.get_or_create_collection(
        name="factory_incidents"
    )

except Exception as e:
    print(f"ChromaDB initialization failed: {e}")
    print("Recreating Chroma database...")

    shutil.rmtree(CHROMA_PATH, ignore_errors=True)
    os.makedirs(CHROMA_PATH, exist_ok=True)

    client = chromadb.PersistentClient(
        path=CHROMA_PATH,
        settings=Settings(anonymized_telemetry=False)
    )

    collection = client.get_or_create_collection(
        name="factory_incidents"
    )


def add_incident(text, metadata):
    doc_id = f"{metadata['timestamp']}_{metadata['worker_id']}"

    # Avoid duplicate ID errors
    try:
        collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[doc_id],
        )
    except Exception:
        collection.upsert(
            documents=[text],
            metadatas=[metadata],
            ids=[doc_id],
        )