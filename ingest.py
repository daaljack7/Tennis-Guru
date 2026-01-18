import os
import fitz  # PyMuPDF
import chromadb
from dotenv import load_dotenv
from together import Together

# Load your API key from the .env file
load_dotenv()
client = Together(api_key=os.getenv("TOGETHER_API_KEY"))

def ingest_docs(pdf_path):
    # 1. Read the PDF
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    
    # 2. Chunking: Split text into 1000-character pieces
    chunks = [text[i:i+1000] for i in range(0, len(text), 900)]
    
    # 3. Connect to ChromaDB (your local database folder)
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    collection = chroma_client.get_or_create_collection(name="pdf_knowledge")

    print(f"Starting ingestion for {len(chunks)} chunks...")

    for i, chunk in enumerate(chunks):
        # Generate embedding (mathematical vector) for this chunk
        res = client.embeddings.create(
            model="togethercomputer/m2-bert-80M-32k-retrieval",
            input=chunk
        )
        vector = res.data[0].embedding
        
        # Save to the database
        collection.add(
            ids=[f"chunk_{i}"],
            embeddings=[vector],
            documents=[chunk]
        )
    print("Done! Your database is ready.")

if __name__ == "__main__":
    # Put your actual PDF filename here!
    ingest_docs("Docs/the-inner-game-of-tennis.pdf")