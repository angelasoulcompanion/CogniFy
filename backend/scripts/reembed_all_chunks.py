"""
Re-embed All Chunks Migration Script
=====================================
Re-generates embeddings for all existing chunks with enriched context
(document title, section, page number)

Usage:
    cd backend
    python -m scripts.reembed_all_chunks

Created by Angela for CogniFy RAG Enhancement - 4 January 2026
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.infrastructure.database import Database
from app.services.embedding_service import get_embedding_service, build_embedding_text


async def reembed_all_chunks():
    """Re-embed all chunks with enriched context"""

    print("=" * 60)
    print("🔄 CogniFy RAG Enhancement - Re-embedding Migration")
    print("=" * 60)

    # Connect to database
    print("\n📡 Connecting to database...")
    await Database.connect()

    embedding_service = get_embedding_service()

    try:
        # Get all chunks with document info
        print("\n📊 Fetching chunks from database...")
        chunks = await Database.fetch(
            """
            SELECT
                dc.chunk_id,
                dc.content,
                dc.page_number,
                dc.section_title,
                d.original_filename as document_title
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.document_id
            ORDER BY d.document_id, dc.chunk_index
            """
        )

        total = len(chunks)
        print(f"   Found {total} chunks to re-embed")

        if total == 0:
            print("\n✅ No chunks to process!")
            return

        # Process in batches
        batch_size = 10
        success_count = 0
        error_count = 0

        print(f"\n🚀 Starting re-embedding (batch size: {batch_size})...")
        print("-" * 60)

        for i in range(0, total, batch_size):
            batch = chunks[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total + batch_size - 1) // batch_size

            print(f"\n📦 Batch {batch_num}/{total_batches} ({len(batch)} chunks)")

            for chunk in batch:
                chunk_id = chunk["chunk_id"]

                # Build enriched text
                enriched_text = build_embedding_text(
                    content=chunk["content"],
                    document_title=chunk["document_title"],
                    section_title=chunk["section_title"],
                    page_number=chunk["page_number"]
                )

                # Generate new embedding
                embedding = await embedding_service.get_embedding(
                    enriched_text,
                    use_cache=False  # Force regeneration
                )

                if embedding is None:
                    print(f"   ❌ Failed: chunk {chunk_id}")
                    error_count += 1
                    continue

                # Update in database
                embedding_str = "[" + ",".join(str(float(x)) for x in embedding) + "]"
                await Database.execute(
                    """
                    UPDATE document_chunks
                    SET embedding = $1::vector
                    WHERE chunk_id = $2
                    """,
                    embedding_str, chunk_id
                )
                success_count += 1

            # Progress
            progress = min(100, int((i + len(batch)) / total * 100))
            print(f"   ✅ Progress: {progress}% ({success_count}/{total})")

            # Small delay between batches
            if i + batch_size < total:
                await asyncio.sleep(0.1)

        print("\n" + "=" * 60)
        print("📊 Migration Complete!")
        print("=" * 60)
        print(f"   ✅ Success: {success_count}")
        print(f"   ❌ Errors:  {error_count}")
        print(f"   📈 Total:   {total}")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        await embedding_service.close()
        await Database.disconnect()
        print("\n👋 Database connection closed")


if __name__ == "__main__":
    asyncio.run(reembed_all_chunks())
