"""
Clear All Documents Script
Deletes all documents and chunks from database

Usage:
    cd backend
    python -m scripts.clear_all_documents
"""

import asyncio
import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.infrastructure.database import Database


async def clear_all():
    print("=" * 50)
    print("🗑️  Clearing all documents from CogniFy")
    print("=" * 50)

    await Database.connect()

    try:
        # Get counts before
        chunks = await Database.fetchrow("SELECT COUNT(*) as cnt FROM document_chunks")
        docs = await Database.fetchrow("SELECT COUNT(*) as cnt FROM documents")

        print(f"\n📊 Before: {docs['cnt']} documents, {chunks['cnt']} chunks")

        # Delete chunks first (foreign key)
        await Database.execute("DELETE FROM document_chunks")
        print("✅ Deleted all chunks")

        # Delete documents
        await Database.execute("DELETE FROM documents")
        print("✅ Deleted all documents")

        print("\n" + "=" * 50)
        print("🎉 Done! Database is clean.")
        print("=" * 50)

    finally:
        await Database.disconnect()


if __name__ == "__main__":
    asyncio.run(clear_all())
