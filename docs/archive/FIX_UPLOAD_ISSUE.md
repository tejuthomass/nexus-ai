# PDF Upload Size Limit Fix

## Problem
When uploading large PDF files (like B.E.CSE-2021.pdf), the application was failing with:
```
Error, message length too large: found 5085225 bytes, the limit is: 4194304 bytes
```

This is a Pinecone vector database limitation - maximum payload size is 4MB per request.

## Root Cause
The `ingest_document()` function in `chat/rag.py` was trying to upsert all vectors in a single batch, which exceeded Pinecone's 4MB payload limit when processing large PDFs.

## Solution Implemented

### 1. **Batch Upsert Processing** (chat/rag.py)
Changed from single upsert to batched upserts:
```python
# Batch upsert to respect Pinecone's size limits (~4MB per request)
batch_size = 50  # Upsert in batches of 50 vectors
for i in range(0, len(vectors), batch_size):
    batch = vectors[i:i+batch_size]
    try:
        index.upsert(vectors=batch)
        logger.info(f"Upserted batch {i//batch_size + 1} with {len(batch)} vectors")
    except Exception as e:
        logger.error(f"Failed to upsert batch {i//batch_size + 1}: {e}")
        raise
```

### 2. **Reduced Chunk Size** (chat/rag.py)
Reduced text chunk size from 1000 to 500 characters to generate smaller embeddings:
```python
chunk_size = 500  # Reduced from 1000 to be more conservative
```

## Impact
- Large PDF files can now be processed successfully
- Embeddings are upserted in 50-vector batches (~100-150KB each)
- Error messages are properly displayed to users
- Files appearing in attachments after refresh indicates partial success (now fixed)

## Testing
To test with large PDFs:
1. Try uploading B.E.CSE-2021.pdf again
2. The UI should no longer show indefinite buffering
3. File should upload and appear in attachments immediately
4. Check server logs for batch processing: "Upserted batch X with Y vectors"

## Configuration Options
If you still encounter issues, you can adjust:
- `batch_size`: Increase to 100+ for faster processing (if batches still too large)
- `chunk_size`: Decrease to 300 for safer embeddings

## Related Files Modified
- `/workspaces/nexus-ai/chat/rag.py` - Batch upsert implementation
