import os
import logging
from google import genai
from pinecone import Pinecone
from pypdf import PdfReader
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# 1. Initialize Clients
def get_clients():
    try:
        google_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index_name = os.getenv("PINECONE_INDEX_NAME", "nexus-index")
        index = pc.Index(index_name) 
        return google_client, index
    except Exception as e:
        logger.error(f"Failed to initialize clients: {e}")
        raise

# 2. PDF Processor (Updated for Cloud)
def extract_text_from_pdf(pdf_file):
    try:
        # Pass the file object directly to PdfReader
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        if not text.strip():
            raise ValueError("PDF contains no extractable text")
        return text
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")

# 3. Ingest (Save Session ID in Metadata)
def ingest_document(file_identifier, text_content):
    # file_identifier format: "SESSIONID_FILENAME" (e.g., "15_Resume.pdf")
    # We need to extract the session_id to save it as metadata for filtering later.
    try:
        session_id = file_identifier.split('_')[0] # Grab "15" from "15_Resume.pdf"
    except:
        session_id = "global"

    try:
        google_client, index = get_clients()
        
        # Split text into chunks with overlap to prevent context fragmentation
        # OPTIMIZED: Reduced chunk size from 2000 to 800 characters for better precision
        # Smaller chunks improve answer accuracy for specific questions by reducing context dilution
        # Overlap of 100 chars maintains semantic continuity between chunks
        chunk_size = 800
        chunk_overlap = 100
        chunks = []
        for i in range(0, len(text_content), chunk_size - chunk_overlap):
            chunk = text_content[i:i+chunk_size]
            if chunk.strip():  # Only add non-empty chunks
                chunks.append(chunk)
        
        if not chunks:
            raise ValueError("No text chunks to process")
        
        # Use batch embedding API for efficiency (up to 100 texts per request)
        vectors = []
        batch_size_for_embedding = 10  # Embed 10 chunks at a time
        
        for batch_start in range(0, len(chunks), batch_size_for_embedding):
            batch_end = min(batch_start + batch_size_for_embedding, len(chunks))
            batch_chunks = chunks[batch_start:batch_end]
            
            try:
                # Batch embed multiple chunks in one API call
                response = google_client.models.embed_content(
                    model="gemini-embedding-001",
                    contents=batch_chunks,
                    config={
                        'output_dimensionality': 768
                    },
                )
                
                # Process embeddings for this batch
                for idx, chunk in enumerate(batch_chunks):
                    chunk_idx = batch_start + idx
                    embedding = response.embeddings[idx].values
                    vector_id = f"{file_identifier}_{chunk_idx}"
                    
                    vectors.append({
                        "id": vector_id,
                        "values": embedding,
                        "metadata": {
                            "text": chunk,
                            "source": file_identifier,
                            "session_id": session_id
                        }
                    })
                
                logger.info(f"Embedded batch {batch_start//batch_size_for_embedding + 1}: chunks {batch_start}-{batch_end-1}")
            except Exception as e:
                logger.error(f"Failed to embed batch starting at chunk {batch_start}: {e}")
                raise

        if not vectors:
            raise ValueError("No vectors were successfully created")
        
        # Batch upsert to respect Pinecone's size limits (~4MB per request)
        pinecone_batch_size = 50  # Upsert in batches of 50 vectors
        for i in range(0, len(vectors), pinecone_batch_size):
            batch = vectors[i:i+pinecone_batch_size]
            try:
                index.upsert(vectors=batch)
                logger.info(f"Upserted batch {i//pinecone_batch_size + 1} with {len(batch)} vectors for {file_identifier}")
            except Exception as e:
                logger.error(f"Failed to upsert batch {i//pinecone_batch_size + 1}: {e}")
                raise
        
        logger.info(f"Successfully ingested {len(vectors)} vectors for {file_identifier}")
        return len(vectors)
    except Exception as e:
        logger.error(f"Document ingestion failed for {file_identifier}: {e}")
        raise

# 4. Retrieve (Filter by Session ID)
def retrieve_context(query, session_id=None):
    try:
        google_client, index = get_clients()

        response = google_client.models.embed_content(
            model="gemini-embedding-001",
            contents=query,
            config={
                'output_dimensionality': 768
            },
        )
        query_embedding = response.embeddings[0].values

        # Create Filter (Only look at vectors for THIS session)
        filter_dict = {}
        if session_id:
            filter_dict = {"session_id": {"$eq": str(session_id)}}

        # Retrieve more chunks with optimized chunk size for better context coverage
        # Increased from top_k=3 to top_k=5 to compensate for smaller chunk sizes
        search_results = index.query(
            vector=query_embedding,
            top_k=5,
            include_metadata=True,
            filter=filter_dict # <--- Apply the filter here
        )

        context_text = ""
        for match in search_results['matches']:
            context_text += match['metadata']['text'] + "\n\n"
        
        logger.info(f"Retrieved context for query (session: {session_id})")
        return context_text
    except Exception as e:
        logger.error(f"Context retrieval failed: {e}")
        return ""  # Return empty string instead of crashing

# 5. Delete Vectors (The Cleaner) - Enhanced with retry logic
def delete_session_vectors(session_id, max_retries=3):
    """
    Delete all vectors for a session with retry logic for reliability.
    Ensures orphaned vectors don't accumulate even when API calls fail.
    
    Args:
        session_id: ID of the session to clean
        max_retries: Number of retry attempts (default: 3)
    
    Returns:
        bool: True if deletion succeeded, False otherwise
    """
    import time
    
    for attempt in range(max_retries):
        try:
            google_client, index = get_clients()
            # Delete all vectors where metadata['session_id'] matches
            index.delete(filter={"session_id": {"$eq": str(session_id)}})
            logger.info(f"🧹 Successfully cleaned vectors for session {session_id} (attempt {attempt + 1})")
            return True
        except Exception as e:
            logger.error(f"Attempt {attempt + 1}/{max_retries} - Error cleaning vectors for session {session_id}: {e}")
            
            # If this isn't the last retry, wait before trying again
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                logger.info(f"Retrying vector cleanup in {wait_time}s...")
                time.sleep(wait_time)
            else:
                # Final attempt failed - log critical error for manual cleanup
                logger.critical(
                    f"⚠️ CRITICAL: Failed to delete vectors for session {session_id} after {max_retries} attempts. "
                    f"Manual cleanup required to prevent orphaned vectors. Error: {e}"
                )
                return False
    
    return False

# 6. Delete Vectors for Specific Document (For Failed Uploads) - Enhanced with retry logic
def delete_document_vectors(file_identifier, max_retries=3):
    """
    Delete vectors for a specific document with retry logic.
    
    Args:
        file_identifier: Identifier of the document to clean
        max_retries: Number of retry attempts (default: 3)
    
    Returns:
        bool: True if deletion succeeded, False otherwise
    """
    import time
    
    for attempt in range(max_retries):
        try:
            google_client, index = get_clients()
            # Delete all vectors where source matches the file_identifier
            index.delete(filter={"source": {"$eq": file_identifier}})
            logger.info(f"🧹 Successfully cleaned vectors for document {file_identifier} (attempt {attempt + 1})")
            return True
        except Exception as e:
            logger.error(f"Attempt {attempt + 1}/{max_retries} - Error cleaning vectors for document {file_identifier}: {e}")
            
            # If this isn't the last retry, wait before trying again
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                logger.info(f"Retrying document vector cleanup in {wait_time}s...")
                time.sleep(wait_time)
            else:
                # Final attempt failed - log critical error
                logger.critical(
                    f"⚠️ CRITICAL: Failed to delete vectors for document {file_identifier} after {max_retries} attempts. "
                    f"Manual cleanup required. Error: {e}"
                )
                return False
    
    return False