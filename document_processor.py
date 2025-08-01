import io
from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pinecone import Pinecone, ServerlessSpec
import pypdf
from docx import Document as DocxDocument
import uuid
import numpy as np
from config import Config


class DocumentProcessor:
    def __init__(self):
        self.pc = Pinecone(api_key=Config.PINECONE_API_KEY)
        # Use a simple TF-IDF approach instead of sentence transformers initially
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP,
            length_function=len,
        )
        self._ensure_index_exists()
    
    def _ensure_index_exists(self):
        """Create Pinecone index if it doesn't exist"""
        try:
            index_name = Config.PINECONE_INDEX_NAME
            if index_name not in self.pc.list_indexes().names():
                self.pc.create_index(
                    name=index_name,
                    dimension=384,  # Using 384 dimensions for compatibility
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',
                        region='us-east-1'
                    )
                )
            self.index = self.pc.Index(index_name)
        except Exception as e:
            print(f"Error setting up Pinecone index: {e}")
            raise
    
    def extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF file"""
        try:
            pdf_file = io.BytesIO(file_content)
            pdf_reader = pypdf.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error extracting PDF text: {e}")
            return ""
    
    def extract_text_from_docx(self, file_content: bytes) -> str:
        """Extract text from DOCX file"""
        try:
            docx_file = io.BytesIO(file_content)
            doc = DocxDocument(docx_file)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            print(f"Error extracting DOCX text: {e}")
            return ""
    
    def extract_text(self, file_content: bytes, file_type: str) -> str:
        """Extract text based on file type"""
        if file_type.lower() == 'pdf':
            return self.extract_text_from_pdf(file_content)
        elif file_type.lower() in ['docx', 'doc']:
            return self.extract_text_from_docx(file_content)
        else:
            # Assume text file
            return file_content.decode('utf-8', errors='ignore')
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks"""
        chunks = self.text_splitter.split_text(text)
        return chunks
    
    def create_simple_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create simple embeddings using basic text processing"""
        embeddings = []
        for text in texts:
            # Simple character-level embedding (for demo purposes)
            # In production, you would use proper sentence transformers
            chars = list(set(text.lower()))
            embedding = np.zeros(384)
            for i, char in enumerate(chars[:384]):
                embedding[i] = ord(char) / 127.0  # Normalize to 0-1
            embeddings.append(embedding.tolist())
        return embeddings
    
    def store_embeddings(
        self,
        embeddings: List[List[float]],
        chunks: List[str],
        document_id: int
    ) -> List[str]:
        """Store embeddings in Pinecone"""
        vector_ids = []
        vectors_to_upsert = []
        
        for i, (embedding, chunk) in enumerate(zip(embeddings, chunks)):
            vector_id = f"doc_{document_id}_chunk_{i}_{uuid.uuid4().hex[:8]}"
            vector_ids.append(vector_id)
            
            vectors_to_upsert.append({
                "id": vector_id,
                "values": embedding,
                "metadata": {
                    "document_id": document_id,
                    "chunk_index": i,
                    "text": chunk
                }
            })
        
        # Batch upsert vectors
        try:
            self.index.upsert(vectors=vectors_to_upsert)
        except Exception as e:
            print(f"Error storing embeddings: {e}")
            raise
        
        return vector_ids
    
    def search_similar_chunks(
        self,
        query: str,
        document_id: int = None,
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        """Search for similar chunks using simple text matching"""
        if top_k is None:
            top_k = Config.MAX_RETRIEVAL_RESULTS
        
        # Create simple query embedding
        query_embedding = self.create_simple_embeddings([query])[0]
        
        # Build filter if document_id is provided
        filter_dict = {}
        if document_id:
            filter_dict["document_id"] = document_id
        
        # Search in Pinecone
        try:
            search_results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict if filter_dict else None
            )
            
            results = []
            for match in search_results.matches:
                results.append({
                    "id": match.id,
                    "score": match.score,
                    "text": match.metadata.get("text", ""),
                    "document_id": match.metadata.get("document_id"),
                    "chunk_index": match.metadata.get("chunk_index")
                })
            
            return results
        except Exception as e:
            print(f"Error searching embeddings: {e}")
            return []
    
    def process_document(
        self,
        file_content: bytes,
        filename: str,
        document_id: int
    ) -> Dict[str, Any]:
        """Complete document processing pipeline"""
        try:
            # Extract file type
            file_type = filename.split('.')[-1].lower()
            
            # Extract text
            text = self.extract_text(file_content, file_type)
            if not text.strip():
                return {"success": False, "error": "No text extracted from document"}
            
            # Chunk text
            chunks = self.chunk_text(text)
            if not chunks:
                return {"success": False, "error": "No chunks created from text"}
            
            # Create embeddings
            embeddings = self.create_simple_embeddings(chunks)
            
            # Store in Pinecone
            vector_ids = self.store_embeddings(embeddings, chunks, document_id)
            
            return {
                "success": True,
                "text": text,
                "chunks_count": len(chunks),
                "vector_ids": vector_ids
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
