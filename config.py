import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Pinecone Configuration
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "gcp-starter")

    # Legacy 384-dimensional index (existing data)
    PINECONE_INDEX_NAME = "hackrx-documents"

    # New 768-dimensional index (enhanced embeddings)
    PINECONE_INDEX_NAME_768 = "hackrx-documents-768"

    # Gemini API Configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")

    # Hugging Face API Configuration
    HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

    # Embedding Configuration
    EMBEDDING_MODEL = "intfloat/e5-large-v2"
    EMBEDDING_DIMENSION = 768  # Use 768 dimensions for better accuracy
    EMBEDDING_DIMENSION_LEGACY = 384  # Legacy dimension

    # PostgreSQL Configuration
    DATABASE_URL = os.getenv("DATABASE_URL")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 5432))
    DB_NAME = os.getenv("DB_NAME", "hackrx_db")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    # API Configuration
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", 8000))

    # Streamlit Configuration
    STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", 8501))

    # Document Processing
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    MAX_RETRIEVAL_RESULTS = 10
