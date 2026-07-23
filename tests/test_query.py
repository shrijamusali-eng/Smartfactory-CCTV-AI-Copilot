import sys
import os

# Align local paths so the script looks at the root folders seamlessly
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

import chromadb

# Point directly to your active vector database storage folder on disk
client = chromadb.PersistentClient(path="database/chroma")
collection = client.get_collection("factory_incidents")

# Define a flexible, natural language query sentence
query_text = "Show me a list of human related incidents"
print(f"Querying ChromaDB with phrase: '{query_text}'...\n")

# Request the top 2 matching semantic records from the database
results = collection.query(
    query_texts=[query_text],
    n_results=2
)

print("--- Matching Results Located ---")
for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
    print(f"📄 Record Found: {doc}")
    print(f"⚙️ Metadata Context: {metadata}")
    print("-" * 32)