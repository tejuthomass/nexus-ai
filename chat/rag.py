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
        index = pc.Index("nexus-index") 
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
        
        chunk_size = 1000
        chunks = [text_content[i:i+chunk_size] for i in range(0, len(text_content), chunk_size)]
        
        if not chunks:
            raise ValueError("No text chunks to process")
        
        vectors = []
        for i, chunk in enumerate(chunks):
            try:
                response = google_client.models.embed_content(
                    model="text-embedding-004",
                    contents=chunk
                )
                embedding = response.embeddings[0].values
                
                vector_id = f"{file_identifier}_{i}"
                
                vectors.append({
                    "id": vector_id,
                    "values": embedding,
                    "metadata": {
                        "text": chunk, 
                        "source": file_identifier,
                        "session_id": session_id  # <--- CRITICAL: Save Session ID
                    }
                })
            except Exception as e:
                logger.warning(f"Failed to embed chunk {i}: {e}")
                continue

        if not vectors:
            raise ValueError("No vectors were successfully created")
            
        index.upsert(vectors=vectors)
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