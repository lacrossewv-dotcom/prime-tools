#!/usr/bin/env python3
"""
Chroma Helper CLI — Vector database for semantic search across PRIME ecosystem.

Usage:
    py -3.13 chroma_helper.py --task add --collection athena --input "path/to/file.txt"
    py -3.13 chroma_helper.py --task add-folder --collection athena --input "path/to/folder" --pattern "*.txt"
    py -3.13 chroma_helper.py --task search --collection athena --query "Nasser's strategic miscalculation"
    py -3.13 chroma_helper.py --task search --collection athena --query "friction in war" --limit 10
    py -3.13 chroma_helper.py --task list
    py -3.13 chroma_helper.py --task info --collection athena
    py -3.13 chroma_helper.py --task delete --collection athena

Requires: py -3.13 (Python 3.14 not compatible with chromadb)
Data stored at: ~/.google_workspace_mcp/chroma_data/
"""

import argparse
import os
import sys
import glob as glob_module
import json
import time as _time
from pathlib import Path

# Usage logging
sys.path.insert(0, str(Path(__file__).resolve().parent))
from usage_logger import log_usage

# Chroma data directory
CHROMA_DATA_DIR = os.path.join(os.path.expanduser("~"), ".google_workspace_mcp", "chroma_data")

def get_client():
    """Get persistent Chroma client."""
    import chromadb
    os.makedirs(CHROMA_DATA_DIR, exist_ok=True)
    return chromadb.PersistentClient(path=CHROMA_DATA_DIR)


def read_file_content(filepath: str) -> str:
    """Read a text file, handling common encodings."""
    for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
        try:
            with open(filepath, "r", encoding=encoding) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    print(f"  WARNING: Could not decode {filepath}, skipping")
    return ""


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """Split text into overlapping chunks for better retrieval."""
    if len(text) <= chunk_size:
        return [text] if text.strip() else []
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start = end - overlap
    return chunks


def task_add(args):
    """Add a single file to a collection."""
    t0 = _time.time()
    client = get_client()
    collection = client.get_or_create_collection(name=args.collection)
    filepath = args.input

    if not os.path.isfile(filepath):
        print(f"ERROR: File not found: {filepath}")
        sys.exit(1)

    content = read_file_content(filepath)
    if not content.strip():
        print(f"ERROR: File is empty: {filepath}")
        sys.exit(1)

    filename = os.path.basename(filepath)
    chunks = chunk_text(content, chunk_size=args.chunk_size, overlap=args.overlap)

    ids = []
    documents = []
    metadatas = []
    for i, chunk in enumerate(chunks):
        doc_id = f"{filename}::chunk_{i}"
        ids.append(doc_id)
        documents.append(chunk)
        metadatas.append({
            "source": filepath,
            "filename": filename,
            "chunk_index": i,
            "total_chunks": len(chunks),
        })

    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    duration_ms = int((_time.time() - t0) * 1000)
    log_usage("chroma", "local", "add",
              input_tokens=len(chunks), output_tokens=0, cost_estimate=0.0,
              metadata={"duration_ms": duration_ms, "collection": args.collection, "file": filename})
    print(f"Added {len(chunks)} chunks from '{filename}' to collection '{args.collection}'")
    print(f"  Collection now has {collection.count()} total documents")


def task_add_folder(args):
    """Add all matching files from a folder to a collection."""
    t0 = _time.time()
    client = get_client()
    collection = client.get_or_create_collection(name=args.collection)
    folder = args.input
    pattern = args.pattern or "*.txt"

    if not os.path.isdir(folder):
        print(f"ERROR: Folder not found: {folder}")
        sys.exit(1)

    search_pattern = os.path.join(folder, "**", pattern)
    files = glob_module.glob(search_pattern, recursive=True)

    if not files:
        print(f"No files matching '{pattern}' found in {folder}")
        return

    total_chunks = 0
    for filepath in sorted(files):
        content = read_file_content(filepath)
        if not content.strip():
            continue

        filename = os.path.basename(filepath)
        rel_path = os.path.relpath(filepath, folder)
        chunks = chunk_text(content, chunk_size=args.chunk_size, overlap=args.overlap)

        ids = []
        documents = []
        metadatas = []
        for i, chunk in enumerate(chunks):
            doc_id = f"{rel_path}::chunk_{i}"
            ids.append(doc_id)
            documents.append(chunk)
            metadatas.append({
                "source": filepath,
                "filename": filename,
                "relative_path": rel_path,
                "chunk_index": i,
                "total_chunks": len(chunks),
            })

        if ids:
            collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
            total_chunks += len(chunks)
            print(f"  + {filename}: {len(chunks)} chunks")

    duration_ms = int((_time.time() - t0) * 1000)
    log_usage("chroma", "local", "add-folder",
              input_tokens=total_chunks, output_tokens=0, cost_estimate=0.0,
              metadata={"duration_ms": duration_ms, "collection": args.collection,
                        "file_count": len(files)})
    print(f"\nAdded {total_chunks} chunks from {len(files)} files to '{args.collection}'")
    print(f"Collection now has {collection.count()} total documents")


def task_search(args):
    """Search a collection with a natural language query."""
    t0 = _time.time()
    client = get_client()

    try:
        collection = client.get_collection(name=args.collection)
    except Exception:
        print(f"ERROR: Collection '{args.collection}' not found")
        print(f"Available collections: {[c.name for c in client.list_collections()]}")
        sys.exit(1)

    results = collection.query(
        query_texts=[args.query],
        n_results=min(args.limit, collection.count()),
    )

    duration_ms = int((_time.time() - t0) * 1000)
    result_count = len(results["documents"][0]) if results["documents"][0] else 0
    log_usage("chroma", "local", "search",
              input_tokens=1, output_tokens=result_count, cost_estimate=0.0,
              metadata={"duration_ms": duration_ms, "collection": args.collection,
                        "query": args.query[:100]})

    if not results["documents"][0]:
        print("No results found.")
        return

    print(f"Search: \"{args.query}\" in '{args.collection}' ({collection.count()} docs)")
    print(f"Top {len(results['documents'][0])} results:\n")

    for i, (doc, meta, dist) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    )):
        score = 1 - dist  # Convert distance to similarity
        source = meta.get("filename", meta.get("source", "unknown"))
        chunk_idx = meta.get("chunk_index", "?")
        total = meta.get("total_chunks", "?")

        print(f"--- Result {i + 1} (similarity: {score:.3f}) ---")
        print(f"Source: {source} (chunk {chunk_idx}/{total})")
        preview = doc[:500].replace("\n", " ")
        if len(doc) > 500:
            preview += "..."
        print(f"{preview}\n")

    if args.json_output:
        output = {
            "query": args.query,
            "collection": args.collection,
            "results": [
                {
                    "rank": i + 1,
                    "similarity": round(1 - dist, 4),
                    "source": meta.get("filename", "unknown"),
                    "chunk_index": meta.get("chunk_index"),
                    "text": doc,
                }
                for i, (doc, meta, dist) in enumerate(zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0],
                ))
            ],
        }
        print("\n--- JSON ---")
        print(json.dumps(output, indent=2))


def task_list(args):
    """List all collections."""
    client = get_client()
    collections = client.list_collections()

    if not collections:
        print("No collections found.")
        print(f"Data directory: {CHROMA_DATA_DIR}")
        return

    print(f"Collections ({len(collections)}):\n")
    for coll in collections:
        c = client.get_collection(name=coll.name)
        print(f"  {coll.name}: {c.count()} documents")

    print(f"\nData directory: {CHROMA_DATA_DIR}")


def task_info(args):
    """Show detailed info about a collection."""
    client = get_client()

    try:
        collection = client.get_collection(name=args.collection)
    except Exception:
        print(f"ERROR: Collection '{args.collection}' not found")
        sys.exit(1)

    count = collection.count()
    print(f"Collection: {args.collection}")
    print(f"Documents: {count}")

    if count > 0:
        sample = collection.get(limit=min(10, count), include=["metadatas"])
        sources = set()
        for meta in sample["metadatas"]:
            sources.add(meta.get("filename", meta.get("source", "unknown")))
        print(f"Sample sources: {', '.join(sorted(sources))}")

        # Count unique source files
        all_meta = collection.get(include=["metadatas"])
        unique_files = set()
        for meta in all_meta["metadatas"]:
            unique_files.add(meta.get("source", meta.get("filename", "unknown")))
        print(f"Unique source files: {len(unique_files)}")


def task_delete(args):
    """Delete a collection."""
    client = get_client()

    try:
        client.delete_collection(name=args.collection)
        print(f"Deleted collection '{args.collection}'")
    except Exception:
        print(f"ERROR: Collection '{args.collection}' not found")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Chroma Vector DB Helper for PRIME ecosystem")
    parser.add_argument("--task", required=True,
                        choices=["add", "add-folder", "search", "list", "info", "delete"],
                        help="Task to perform")
    parser.add_argument("--collection", "-c", help="Collection name (e.g., athena, atlas, semper)")
    parser.add_argument("--input", "-i", help="File or folder path")
    parser.add_argument("--query", "-q", help="Search query")
    parser.add_argument("--pattern", "-p", default="*.txt", help="File pattern for add-folder (default: *.txt)")
    parser.add_argument("--limit", "-n", type=int, default=5, help="Number of search results (default: 5)")
    parser.add_argument("--chunk-size", type=int, default=1000, help="Characters per chunk (default: 1000)")
    parser.add_argument("--overlap", type=int, default=200, help="Chunk overlap in characters (default: 200)")
    parser.add_argument("--json", dest="json_output", action="store_true", help="Also output JSON for search results")

    args = parser.parse_args()

    # Validate required args per task
    if args.task in ("add", "add-folder") and not args.collection:
        parser.error("--collection is required for add/add-folder")
    if args.task in ("add", "add-folder") and not args.input:
        parser.error("--input is required for add/add-folder")
    if args.task == "search" and not args.collection:
        parser.error("--collection is required for search")
    if args.task == "search" and not args.query:
        parser.error("--query is required for search")
    if args.task in ("info", "delete") and not args.collection:
        parser.error("--collection is required for info/delete")

    tasks = {
        "add": task_add,
        "add-folder": task_add_folder,
        "search": task_search,
        "list": task_list,
        "info": task_info,
        "delete": task_delete,
    }
    tasks[args.task](args)


if __name__ == "__main__":
    main()
