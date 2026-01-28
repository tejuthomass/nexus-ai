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
        # Use 2000 chars per chunk with 200-char overlap for semantic continuity
        chunk_size = 2000
        chunk_overlap = 200
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
                    model="text-embedding-004",
                    contents=batch_chunks
                )
                
                # Process embeddings for this batch
                for idx, (chunk_idx, chunk) in enumerate(enumerate(batch_chunks, batch_start)):
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
            model="text-embedding-004",
            contents=query
        )
        query_embedding = response.embeddings[0].values

        # Create Filter (Only look at vectors for THIS session)
        filter_dict = {}
        if session_id:
            filter_dict = {"session_id": {"$eq": str(session_id)}}

        search_results = index.query(
            vector=query_embedding,
            top_k=3,
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

# 5. Delete Vectors (The Cleaner)
def delete_session_vectors(session_id):
    try:
        google_client, index = get_clients()
        # Delete all vectors where metadata['session_id'] matches
        index.delete(filter={"session_id": {"$eq": str(session_id)}})
        logger.info(f"🧹 Cleaned vectors for session {session_id}")
    except Exception as e:
        logger.error(f"Error cleaning vectors for session {session_id}: {e}")

# 6. Delete Vectors for Specific Document (For Failed Uploads)
def delete_document_vectors(file_identifier):
    """Delete vectors for a specific document by file_identifier"""
    try:
        google_client, index = get_clients()
        # Delete all vectors where source matches the file_identifier
        index.delete(filter={"source": {"$eq": file_identifier}})
        logger.info(f"🧹 Cleaned vectors for document {file_identifier}")
    except Exception as e:
        logger.error(f"Error cleaning vectors for document {file_identifier}: {e}")