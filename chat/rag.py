import os
from google import genai
from pinecone import Pinecone
from pypdf import PdfReader
from dotenv import load_dotenv

load_dotenv()

# 1. Initialize Clients
def get_clients():
    google_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index("nexus-index") 
    return google_client, index

# 2. PDF Processor (Updated for Cloud)
def extract_text_from_pdf(pdf_file):
    # Pass the file object directly to PdfReader
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

# 3. Ingest (Save Session ID in Metadata)
def ingest_document(file_identifier, text_content):
    # file_identifier format: "SESSIONID_FILENAME" (e.g., "15_Resume.pdf")
    # We need to extract the session_id to save it as metadata for filtering later.
    try:
        session_id = file_identifier.split('_')[0] # Grab "15" from "15_Resume.pdf"
    except:
        session_id = "global"

    google_client, index = get_clients()
    
    chunk_size = 1000
    chunks = [text_content[i:i+chunk_size] for i in range(0, len(text_content), chunk_size)]
    
    vectors = []
    for i, chunk in enumerate(chunks):
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

    index.upsert(vectors=vectors)
    return len(vectors)

# 4. Retrieve (Filter by Session ID)
def retrieve_context(query, session_id=None):
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
        
    return context_text

# 5. Delete Vectors (The Cleaner)
def delete_session_vectors(session_id):
    google_client, index = get_clients()
    try:
        # Delete all vectors where metadata['session_id'] matches
        index.delete(filter={"session_id": {"$eq": str(session_id)}})
        print(f"🧹 Cleaned vectors for session {session_id}")
    except Exception as e:
        print(f"Error cleaning vectors: {e}")