import os
import chromadb
from chromadb.config import Settings

# Ensure the database folder exists
os.makedirs("database/chroma", exist_ok=True)

# Initialize persistent Chroma client
client = chromadb.PersistentClient(
    path="database/chroma",
    settings=Settings(anonymized_telemetry=False)
)

# Create or load the collection
collection = client.get_or_create_collection(
    name="factory_incidents"
)

def add_incident(text, metadata):
    doc_id = f"{metadata['timestamp']}_{metadata['worker_id']}"

    collection.add(
        documents=[text],
        metadatas=[metadata],
        ids=[doc_id],
    )