import os
import sys
from dotenv import load_dotenv
from astrapy import DataAPIClient
import numpy 

# Add the project root to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from resume_processor_rag.core.embeddings_generator import generate_embeddings
dotenv_path = ".env"
load_dotenv(dotenv_path=dotenv_path)
astra_token = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
astra_api_endpoint = os.getenv("ASTRA_DB_API_ENDPOINT")


try:
    client = DataAPIClient(astra_token)
    db = client.get_database_by_api_endpoint(astra_api_endpoint)
    try:
        collection = db.get_collection("resume_embeddings")
    except Exception:
        # Try creating it if it doesn't exist? Or just fail soft.
        # Actually proper behavior is often just to get it. 
        # If get_collection fails, it means DB connection issue likely.
        collection = None 
        print("Warning: Could not get Astra DB collection 'resume_embeddings'.")
except Exception as e:
    print(f"Warning: Failed to connect to Astra DB: {e}")
    client = None
    db = None
    collection = None


def insert_embedding_record(data: dict):
    """Inserts a single resume embedding record into the AstraDB collection.
    
    Args:
      data: Dictionary containing the resume embedding data with fields like 
            'text', 'embedding', 'metadata', etc.
    
    Returns:
      The result object from the database insertion operation.
    """
    result = collection.insert_one(data)
    return result

def insert_embedding_batch(records: list):
    """Inserts multiple resume embedding records in a single batch operation.
    
    Args:
      records: List of dictionaries, where each dictionary contains resume 
              embedding data with fields like 'text', 'embedding', 'metadata', etc.
    
    Returns:
      The result object from the batch insertion operation.
    """
    # Each record should be a dict as shown above
    result = collection.insert_many(records)
    return result

def vector_search(query_text: str, limit=5, user_id=None):
    """Searches for the most similar resume embeddings using a text query.
    
    Args:
      query_text: The text query to search for similar resume content.
      limit: Maximum number of similar resume chunks to return (default: 5).
      user_id: Optional user_id to filter results.
    """
    
    print(f"Searching for: '{query_text}'")
    
    # 1. Generate the embedding from the text
    query_embedding = generate_embeddings(query_text)
    
    # 2. Use the generated embedding to find results (this returns the cursor)
    filter_query = {"user_id": user_id} if user_id else {}
    results_cursor = collection.find(
        filter=filter_query,
        sort={"$vector": query_embedding.tolist()},
        limit=limit,
    )
    
    # 3. THIS IS THE MISSING STEP: Loop over the cursor to print each document
    print("\n--- Search Results ---")
    found_results = False
    results = []
    for document in results_cursor:
        found_results = True
        results.append(document)
        print(document)
        print("-" * 20) # Add a separator for clarity
        
    if not found_results:
        print("No results found.")
        
    return results 

def get_candidate_context(user_id: str, limit: int = 10):
    """Retrieves the most relevant context for a candidate (e.g. summary or top chunks)."""
    # For now, we can just search for "resume summary skills experience" for this user
    return vector_search("detailed professional summary of skills and experience", limit=limit, user_id=user_id) 
if db:
    print(f"Connected to Astra DB: {db.list_collection_names()}")
else:
    print("Astra DB connection not available.")