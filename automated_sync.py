# automated_sync.py
import json
import os
import sys
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_chroma import Chroma
import chromadb

# Global Configurations
MANIFEST_FILE = "manifest.json"
CHROMA_HOST = "localhost"
CHROMA_PORT = 8000
COLLECTION_NAME = "local_knowledge_base"

# Connect to Ollama (running locally on Mac Mini)
embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://localhost:11434"
)

# Connect to the Chroma instance running inside Docker via HttpClient
chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
vector_store = Chroma(
    client=chroma_client,
    collection_name=COLLECTION_NAME,
    embedding_function=embeddings
)

def get_loader(file_path: str):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        return PyPDFLoader(file_path)
    elif ext == '.txt':
        return TextLoader(file_path)
    elif ext in ['.md', '.markdown']:
        return UnstructuredMarkdownLoader(file_path)
    else:
        raise ValueError(f"Unsupported file extension: {ext}")

def delete_document(doc_id: str):
    """Removes existing entries safely by source_id metadata filter."""
    try:
        # Chroma client allows explicit metadata deletion filtering
        vector_store.delete(where={"source_id": doc_id})
        print(f"[-] Successfully purged document ID: {doc_id} from Docker Chroma.")
    except Exception as e:
        print(f"[!] Target ID {doc_id} wasn't found or couldn't be deleted: {e}")

def add_or_update_document(doc_id: str, file_path: str, description: str):
    if not os.path.exists(file_path):
        print(f"[!] Error: Tracked file path does not exist: {file_path}")
        return

    print(f"[*] Extracting and embedding document ID {doc_id} -> {file_path}")
    try:
        loader = get_loader(file_path)
        docs = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        chunks = text_splitter.split_documents(docs)
        
        # Inject custom payload tags for downstream client applications (like Claude)
        for chunk in chunks:
            chunk.metadata["source_id"] = doc_id
            chunk.metadata["description"] = description
            chunk.metadata["file_path"] = file_path

        # Clear old vectors under this ID first to guarantee clean updating without stale data duplication
        delete_document(doc_id)
        
        # Upsert new vectors into the Dockerized server instance
        vector_store.add_documents(chunks)
        print(f"[+] Successfully synchronized document ID: {doc_id} ({len(chunks)} chunks).")
    except Exception as e:
        print(f"[!] Error processing document ID {doc_id}: {e}")

def run_sync_cycle():
    """Reads the JSON manifest file and processes actions."""
    print(f"\n[*] Manifest file change detected. Re-syncing database...")
    if not os.path.exists(MANIFEST_FILE):
        print(f"[!] Manifest missing at {MANIFEST_FILE}")
        return

    # Add a slight delay to allow the text editor/saving process to finalize writing to disk
    time.sleep(0.5)

    try:
        with open(MANIFEST_FILE, 'r') as f:
            manifest = json.load(f)
    except json.JSONDecodeError:
        print("[!] Failed to decode JSON. The file might still be writing. Retrying next file-save event.")
        return

    for item in manifest:
        doc_id = item.get("id")
        action = item.get("action", "").lower()
        file_path = item.get("file_path")
        description = item.get("description", "")

        if not doc_id:
            continue

        if action in ["add", "update"]:
            add_or_update_document(doc_id, file_path, description)
        elif action == "delete":
            delete_document(doc_id)
        else:
            print(f"[!] Unknown action protocol '{action}' for ID: {doc_id}")

# Watchdog Event Handler Setup
class ManifestWatchHandler(FileSystemEventHandler):
    def on_modified(self, event):
        # We only care about explicit updates targeting our strict manifest filename
        if not event.is_directory and os.path.basename(event.src_path) == MANIFEST_FILE:
            run_sync_cycle()

if __name__ == "__main__":
    print(f"[*] Starting automated file watcher on '{MANIFEST_FILE}'...")
    print(f"[*] Docker Vector Database target -> http://{CHROMA_HOST}:{CHROMA_PORT}")
    
    # Run an initial full sync execution cycle upon starting the script
    run_sync_cycle()

    event_handler = ManifestWatchHandler()
    observer = Observer()
    # Monitor current working directory containing the manifest file
    observer.schedule(event_handler, path=os.path.dirname(os.path.abspath(MANIFEST_FILE)) or '.', recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Stopping file watcher daemon...")
        observer.stop()
    observer.join()