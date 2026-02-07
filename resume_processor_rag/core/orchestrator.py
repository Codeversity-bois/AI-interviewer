import os
import sys

# Add the project root to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from resume_processor_rag.core.resume_data_extraction import text_extraction
from resume_processor_rag.core.section_chunking import chunk_resume_sections
from resume_processor_rag.core.embeddings_generator import generate_embeddings
from resume_processor_rag.core.astra_db_manager import insert_embedding_batch, vector_search
import json

def resume_extraction_and_chunking(file_name):
    resume_text = text_extraction(file_name)
    chunks = chunk_resume_sections(resume_text)
    json_data = []
    for chunk in chunks:
        embeddings = generate_embeddings(chunk)
        comp_emb = embeddings.tolist()
        print(type(comp_emb))
        print(type(comp_emb[0]))
        print(len(comp_emb))
        data={
            "user_id": "abc",
            "username":"user123", 
            "chunk_id":chunk[0],
            "section_type":chunk[3],
            "content":chunk[4],
            "$vector":comp_emb  # Use $vector instead of embedding
        }
        # Don't convert to JSON string - keep as dict
        json_data.append(data)
    return json_data

def push_into_astradb(json_data):
    try:
        insert_embedding_batch(json_data)
        return True
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

res = push_into_astradb(resume_extraction_and_chunking("resume_processor_rag/core/resume.pdf"))
if res==True:
    print("yes")
else:
    print("no")




