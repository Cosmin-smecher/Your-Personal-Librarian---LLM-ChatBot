#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ingest JSON/SQLite book summaries into ChromaDB and run semantic search (theme or context).
- Uses OpenAI embeddings (text-embedding-3-small) via chromadb embedding_functions.
- Persistent Chroma store is created in ./chroma_book_summaries

Prereq:
    pip install chromadb openai python-dotenv

Env:
    OPENAI_API_KEY=...   # in environment or a .env file in the project root

Usage:
    # 1) Ingest from SQLite (created previously by create_book_summaries_db.py)
    python load_to_chroma_and_search.py ingest --sqlite ./book_summaries.db

    # 2) Search by theme (semantic)
    python load_to_chroma_and_search.py search-theme --theme "aventură" -k 5

    # 3) Search by free context
    python load_to_chroma_and_search.py search --query "o poveste despre totalitarism și supraveghere" -k 5
"""

import argparse
import os
import sqlite3
import unicodedata
from pathlib import Path
from typing import List, Dict

from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions

# -------------------------- utils --------------------------

def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    clean = []
    for ch in value.lower():
        if ch.isalnum():
            clean.append(ch)
        elif ch in (" ", "-", "_"):
            clean.append("-")
    slug = "".join(clean).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "id"

def build_document_row(row: sqlite3.Row) -> Dict:
    """Return a dict with id, document (text), metadata"""
    title = row["title"]
    author = row["author"] or ""
    year = row["year"]
    language = row["language"] or "ro"
    summary = row["summary"] or ""
    themes = row["themes"] or ""
    # Document text that will be embedded (include summary + themes to help recall)
    doc = f"Titlu: {title}\nAutor: {author}\nAn: {year}\nLimbă: {language}\nTeme: {themes}\nRezumat: {summary}"
    meta = {
        "title": title,
        "author": author,
        "year": year,
        "language": language,
        "themes": ", ".join([t.strip() for t in themes.split(",") if t.strip()]),
    }
    return {"id": slugify(f"{title}-{author}"), "document": doc, "metadata": meta}

# -------------------------- chroma --------------------------

def get_collection(persist_dir: Path, collection_name: str = "books"):
    load_dotenv()  # allow .env
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing. Set it in your environment or .env file.")
    client = chromadb.PersistentClient(path=str(persist_dir))
    embedder = embedding_functions.OpenAIEmbeddingFunction(
        api_key=api_key,
        model_name="text-embedding-3-small",
    )
    col = client.get_or_create_collection(name=collection_name, embedding_function=embedder)
    return col

def ingest_sqlite(sqlite_path: Path, persist_dir: Path):
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM book_summaries ORDER BY id;")
    rows = cur.fetchall()
    if not rows:
        raise RuntimeError("No rows found in book_summaries. Run the DB creator first.")
    col = get_collection(persist_dir)
    ids, docs, metas = [], [], []
    for r in rows:
        item = build_document_row(r)
        ids.append(item["id"])
        docs.append(item["document"])
        metas.append(item["metadata"])
    # Chroma upsert
    col.upsert(ids=ids, documents=docs, metadatas=metas)
    print(f"Ingested {len(ids)} items into Chroma at {persist_dir.resolve()} in collection 'books'.")

def search_context(query: str, k: int, persist_dir: Path):
    col = get_collection(persist_dir)
    res = col.query(query_texts=[query], n_results=k, include=["documents", "metadatas", "distances"])
    show_results(res)

def search_theme(theme: str, k: int, persist_dir: Path):
    col = get_collection(persist_dir)
    # We let embeddings do the heavy lifting; enrich the query with a theme hint.
    q = f"cărți cu tema {theme}; recomandări bazate pe această temă"
    res = col.query(query_texts=[q], n_results=k, include=["documents", "metadatas", "distances"])
    show_results(res)

def show_results(res):
    ids = res.get("ids", [[]])[0]
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    dists = res.get("distances", [[]])[0]
    if not ids:
        print("No results.")
        return
    for i, (_id, doc, meta, dist) in enumerate(zip(ids, docs, metas, dists), start=1):
        print("-"*76)
        print(f"#{i}  {meta.get('title')} — {meta.get('author')}  (an: {meta.get('year')})")
        themes_val = meta.get("themes", "")
        themes_str = ", ".join(themes_val) if isinstance(themes_val, list) else str(themes_val)
        print(f"Teme: {themes_str}")
        print(f"Score(similarity≈1-distance): {1.0 - float(dist):.4f}")
        # Show a short preview from the summary portion
        preview = doc.split("Rezumat:", 1)[-1].strip().splitlines()
        preview = " ".join(preview)[:220] + ("…" if len(' '.join(preview)) > 220 else "")
        print(f"Rezumat: {preview}")

# -------------------------- CLI --------------------------

def main():
    parser = argparse.ArgumentParser(description="Ingest and search book summaries in ChromaDB")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ing = sub.add_parser("ingest", help="Ingest from SQLite into ChromaDB")
    p_ing.add_argument("--sqlite", type=Path, required=True, help="Path to book_summaries.db")
    p_ing.add_argument("--persist", type=Path, default=Path("./chroma_book_summaries"), help="Chroma persistence dir")

    p_search = sub.add_parser("search", help="Semantic search by free context")
    p_search.add_argument("--query", type=str, required=True, help="Free-text query")
    p_search.add_argument("-k", type=int, default=5, help="Number of results")
    p_search.add_argument("--persist", type=Path, default=Path("./chroma_book_summaries"))

    p_theme = sub.add_parser("search-theme", help="Semantic search by theme")
    p_theme.add_argument("--theme", type=str, required=True, help="Theme keyword (e.g., 'aventură')")
    p_theme.add_argument("-k", type=int, default=5, help="Number of results")
    p_theme.add_argument("--persist", type=Path, default=Path("./chroma_book_summaries"))

    args = parser.parse_args()

    if args.cmd == "ingest":
        ingest_sqlite(args.sqlite, args.persist)
    elif args.cmd == "search":
        search_context(args.query, args.k, args.persist)
    elif args.cmd == "search-theme":
        search_theme(args.theme, args.k, args.persist)

if __name__ == "__main__":
    main()
