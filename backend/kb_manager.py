import os
import json
import chromadb
from sentence_transformers import SentenceTransformer
from chromadb.utils import embedding_functions

BASE_DIR = os.path.dirname(__file__)
KB_FILE = os.path.join(BASE_DIR, "C:\\Users\\Anmol Upadhyay\\nullaxis_assesment\\backend\\knowledge_base.json")

# Initialize ChromaDB
client = chromadb.PersistentClient(path=os.path.join(BASE_DIR, "chroma_db"))
embedder = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)
collection = client.get_or_create_collection(
    name="tech_kb", 
    embedding_function=embedder
)

def load_kb_and_embed():
    try:
        with open(KB_FILE) as f:
            kb_data = json.load(f)
        
        # Check existing documents
        existing = collection.get(include=["metadatas"])
        existing_ids = [m["id"] for m in existing["metadatas"]] if existing["metadatas"] else []
        
        # Add new entries
        new_docs = []
        new_metas = []
        new_ids = []
        
        for entry in kb_data:
            if str(entry["id"]) not in existing_ids:
                content = f"Issue: {entry['issue']}\nSolution: {entry['solution']}"
                new_docs.append(content)
                new_metas.append({"id": entry["id"], "category": entry["category"]})
                new_ids.append(str(entry["id"]))
        
        if new_docs:
            collection.add(
                documents=new_docs,
                metadatas=new_metas,
                ids=new_ids
            )
    except Exception as e:
        print(f"Knowledge base loading failed: {str(e)}")

def search_kb(query: str, n_results: int = 5):
    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            include=["documents", "distances"]
        )
        return {
            "documents": results["documents"],
            "distances": results["distances"]
        }
    except Exception as e:
        print(f"KB search failed: {str(e)}")
        return {"documents": [], "distances": []}