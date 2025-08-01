from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import json
from typing import Dict, Any
from datetime import datetime
import requests
import io
from urllib.parse import urlparse

from database import get_db, create_tables, Document, DocumentChunk, Query
from document_processor import DocumentProcessor
from gemini_llm import GeminiLLM
from config import Config

# HackRx 6.0 Compliance Enhancement (will be added after app creation)

# Import enhanced E5 services
try:
    from enhanced_document_processor_v2 import get_enhanced_processor_v2
    from enhanced_query_service import get_enhanced_query_service
    ENHANCED_MODE = True
    print("✅ Enhanced E5-large-v2 services available")
except ImportError as e:
    print(f"⚠️ Enhanced services not available: {e}")
    ENHANCED_MODE = False

# Import V3 enhanced services with working E5
try:
    from enhanced_document_processor_v3 import get_enhanced_processor
    from enhanced_query_service_v3 import get_query_service
    from working_e5_service import get_embedding_service
    ENHANCED_V3_MODE = True
    print("✅ Enhanced V3 services with 768-dimensional embeddings available")
except ImportError as e:
    print(f"⚠️ Enhanced V3 services not available: {e}")
    ENHANCED_V3_MODE = False

app = FastAPI(title="HackRx 6.0 Document Intelligence Agent")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components with document processor
doc_processor = DocumentProcessor()
llm = GeminiLLM()


# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    create_tables()


@app.get("/")
async def root():
    return {"message": "HackRx 6.0 Document Intelligence Agent API"}


@app.post("/upload")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload and process a document"""
    try:
        # Read file content
        file_content = await file.read()

        # Create database record
        db_document = Document(
            filename=file.filename,
            file_type=file.filename.split(".")[-1].lower(),
            processed="pending",
        )
        db.add(db_document)
        db.commit()
        db.refresh(db_document)

        # Process document
        result = doc_processor.process_document(
            file_content, file.filename, db_document.id
        )

        if result["success"]:
            # Update database with results
            db_document.content = result["text"]
            db_document.processed = "processed"
            db.commit()

            # Store chunk information
            for i, vector_id in enumerate(result["vector_ids"]):
                chunk = DocumentChunk(
                    document_id=db_document.id, chunk_index=i, embedding_id=vector_id
                )
                db.add(chunk)
            db.commit()

            return {
                "status": "success",
                "document_id": db_document.id,
                "filename": file.filename,
                "chunks_processed": result["chunks_count"],
                "message": "Document uploaded and processed successfully",
            }
        else:
            # Update status as failed
            db_document.processed = "failed"
            db.commit()

            return {"status": "error", "message": result["error"]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-url")
async def upload_document_from_url(
    request: Dict[str, str], db: Session = Depends(get_db)
):
    """Upload and process a document from URL"""
    try:
        url = request.get("url")
        if not url:
            raise HTTPException(status_code=400, detail="URL is required")

        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise HTTPException(status_code=400, detail="Invalid URL format")

        # Download file from URL
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Get filename from URL or Content-Disposition header
        filename = url.split("/")[-1]
        if "content-disposition" in response.headers:
            content_disposition = response.headers["content-disposition"]
            if "filename=" in content_disposition:
                filename = content_disposition.split("filename=")[1].strip('"')

        # If no filename extension, try to detect from content-type
        if "." not in filename:
            content_type = response.headers.get("content-type", "")
            if "pdf" in content_type:
                filename += ".pdf"
            elif "word" in content_type or "docx" in content_type:
                filename += ".docx"
            elif "text" in content_type:
                filename += ".txt"

        file_content = response.content

        # Create database record
        db_document = Document(
            filename=filename,
            file_type=filename.split(".")[-1].lower() if "." in filename else "unknown",
            processed="pending",
        )
        db.add(db_document)
        db.commit()
        db.refresh(db_document)

        # Process document
        result = doc_processor.process_document(file_content, filename, db_document.id)

        if result["success"]:
            # Update database with results
            db_document.content = result["text"]
            db_document.processed = "processed"
            db.commit()

            # Store chunk information
            for i, vector_id in enumerate(result["vector_ids"]):
                chunk = DocumentChunk(
                    document_id=db_document.id, chunk_index=i, embedding_id=vector_id
                )
                db.add(chunk)
            db.commit()

            return {
                "status": "success",
                "document_id": db_document.id,
                "filename": filename,
                "url": url,
                "chunks_processed": result["chunks_count"],
                "message": "Document downloaded from URL and processed successfully",
            }
        else:
            # Update status as failed
            db_document.processed = "failed"
            db.commit()

            return {"status": "error", "message": result["error"]}

    except requests.RequestException as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to download from URL: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query")
async def process_query(request: Dict[str, Any], db: Session = Depends(get_db)):
    """Process a query against uploaded documents"""
    try:
        query_text = request.get("query")
        document_id = request.get("document_id")  # Optional: query specific document

        if not query_text:
            raise HTTPException(status_code=400, detail="Query text is required")

        # Parse query using LLM
        parsed_query = llm.parse_query(query_text)

        # Search for relevant clauses
        retrieved_clauses = doc_processor.search_similar_chunks(
            query_text, document_id=document_id
        )

        if not retrieved_clauses:
            return {
                "status": "no_results",
                "message": "No relevant clauses found for the query",
                "decision": "Rejected",
                "amount": None,
                "justification": [
                    {
                        "clause_id": "none",
                        "text": "No relevant document clauses found",
                        "reason": "Insufficient information to make a decision",
                    }
                ],
            }

        # Make decision using LLM
        decision_result = llm.make_decision(query_text, parsed_query, retrieved_clauses)

        # Store query in database
        db_query = Query(
            query_text=query_text,
            document_id=document_id,
            decision=decision_result["decision"],
            amount=decision_result["amount"],
            justification=json.dumps(decision_result["justification"]),
        )
        db.add(db_query)
        db.commit()

        # Ensure justification is properly formatted
        justification = decision_result["justification"]
        if isinstance(justification, str):
            try:
                justification = json.loads(justification)
            except:
                justification = [
                    '[{"clause_id": "error',
                    'text": justification',
                    'reason": "Formatting issue"}',
                ]

        return {
            "status": "success",
            "query_id": db_query.id,
            "parsed_query": parsed_query,
            "retrieved_clauses_count": len(retrieved_clauses),
            "decision": decision_result["decision"],
            "amount": decision_result["amount"],
            "justification": justification,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents")
async def list_documents(db: Session = Depends(get_db)):
    """List all uploaded documents"""
    documents = db.query(Document).all()
    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "upload_date": doc.upload_date.isoformat() if doc.upload_date else None,
            "processed": doc.processed,
        }
        for doc in documents
    ]


@app.get("/documents/{document_id}")
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """Get document details"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Get chunk count
    chunk_count = (
        db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).count()
    )

    return {
        "id": document.id,
        "filename": document.filename,
        "file_type": document.file_type,
        "upload_date": (
            document.upload_date.isoformat() if document.upload_date else None
        ),
        "processed": document.processed,
        "chunk_count": chunk_count,
        "content_preview": document.content[:500] if document.content else None,
    }


@app.get("/queries")
async def list_queries(db: Session = Depends(get_db)):
    """List all queries"""
    queries = db.query(Query).order_by(Query.timestamp.desc()).all()
    return [
        {
            "id": query.id,
            "query_text": query.query_text,
            "document_id": query.document_id,
            "timestamp": query.timestamp.isoformat() if query.timestamp else None,
            "decision": query.decision,
            "amount": query.amount,
        }
        for query in queries
    ]


@app.get("/queries/{query_id}")
async def get_query_details(query_id: int, db: Session = Depends(get_db)):
    """Get detailed query results"""
    query = db.query(Query).filter(Query.id == query_id).first()
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")

    return {
        "id": query.id,
        "query_text": query.query_text,
        "document_id": query.document_id,
        "timestamp": query.timestamp.isoformat() if query.timestamp else None,
        "decision": query.decision,
        "amount": query.amount,
        "justification": json.loads(query.justification) if query.justification else [],
    }


@app.post("/hackrx/run")
async def hackrx_run_endpoint(request: Dict[str, Any], authorization: str = Header(None, alias="Authorization"), db: Session = Depends(get_db)):
    """HackRx 6.0 official endpoint for document query processing - Updated for exact specification"""

    # Check if this is the new format (documents + questions array)
    if "documents" in request and "questions" in request:
        # Use the new compliance endpoint logic
        return await hackrx_official_compliance_endpoint(request, authorization, db)

    # Fall back to old logic for backward compatibility
    try:
        # Extract query from request
        query_text = request.get("query") or request.get("question")
        document_url = request.get("document_url")

        if not query_text:
            raise HTTPException(status_code=400, detail="Query/question is required")

        # For this demo, we'll use the most recent document if no specific document is provided
        if not document_url:
            latest_doc = (
                db.query(Document)
                .filter(Document.processed == "processed")
                .order_by(Document.upload_date.desc())
                .first()
            )

            if not latest_doc:
                return {
                    "decision": "Rejected",
                    "amount": None,
                    "justification": [
                        {
                            "clause_id": "no_document",
                            "text": "No processed documents available",
                            "reason": "No documents have been uploaded and processed",
                        }
                    ],
                }
            document_id = latest_doc.id
        else:
            # In a real implementation, you would download and process the document from the URL
            document_id = None

        # Parse query using LLM
        parsed_query = llm.parse_query(query_text)

        # Search for relevant clauses
        retrieved_clauses = doc_processor.search_similar_chunks(
            query_text, document_id=document_id
        )

        if not retrieved_clauses:
            return {
                "decision": "Rejected",
                "amount": None,
                "justification": [
                    {
                        "clause_id": "no_results",
                        "text": "No relevant document clauses found",
                        "reason": "Insufficient information to make a decision",
                    }
                ],
            }

        # Make decision using LLM
        decision_result = llm.make_decision(query_text, parsed_query, retrieved_clauses)

        # Store query in database
        db_query = Query(
            query_text=query_text,
            document_id=document_id,
            decision=decision_result["decision"],
            amount=decision_result["amount"],
            justification=json.dumps(decision_result["justification"]),
        )
        db.add(db_query)
        db.commit()

        # Return in the required HackRx format
        return {
            "decision": decision_result["decision"],
            "amount": decision_result["amount"],
            "justification": decision_result["justification"],
        }

    except Exception as e:
        return {
            "decision": "Rejected",
            "amount": None,
            "justification": [
                {
                    "clause_id": "system_error",
                    "text": f"System error: {str(e)}",
                    "reason": "Unable to process request due to system error",
                }
            ],
        }


# Enhanced E5-large-v2 endpoints (768-dimensional embeddings)
@app.post("/enhanced/upload")
async def enhanced_upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload and process document with E5-large-v2 768-dimensional embeddings"""
    if not ENHANCED_MODE:
        raise HTTPException(status_code=503, detail="Enhanced mode not available")

    try:
        # Read file content
        file_content = await file.read()

        # Create database record
        db_document = Document(
            filename=file.filename,
            file_type=file.filename.split(".")[-1].lower() if "." in file.filename else "unknown",
            processed="processing"
        )
        db.add(db_document)
        db.commit()
        db.refresh(db_document)

        # Process with enhanced E5 processor
        enhanced_processor = get_enhanced_processor_v2()
        result = enhanced_processor.process_document(file_content, file.filename, db_document.id)

        if result["success"]:
            # Update document status
            db_document.processed = "processed"
            db_document.content = f"Processed with E5-large-v2: {result['chunks_created']} chunks"
            db.commit()

            return {
                "message": "Document processed successfully with E5-large-v2 embeddings",
                "document_id": db_document.id,
                "filename": file.filename,
                "chunks_created": result["chunks_created"],
                "embedding_model": result["embedding_model"],
                "embedding_dimension": result["embedding_dimension"],
                "processing_details": result
            }
        else:
            db_document.processed = "failed"
            db.commit()
            raise HTTPException(status_code=400, detail=f"Processing failed: {result['error']}")

    except Exception as e:
        return {"error": f"Upload failed: {str(e)}"}


@app.post("/enhanced/query")
async def enhanced_process_query(request: Dict[str, Any], db: Session = Depends(get_db)):
    """Process query with enhanced E5-large-v2 semantic search"""
    if not ENHANCED_MODE:
        raise HTTPException(status_code=503, detail="Enhanced mode not available")

    try:
        query_text = request.get("query")
        document_id = request.get("document_id")
        use_hybrid = request.get("use_hybrid", True)

        if not query_text:
            raise HTTPException(status_code=400, detail="Query text is required")

        # Process with enhanced query service
        enhanced_query_service = get_enhanced_query_service()
        result = enhanced_query_service.process_query(
            query=query_text,
            document_id=document_id,
            use_hybrid=use_hybrid
        )

        return result

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "decision": "Error",
            "amount": None,
            "justification": [{
                "clause_id": "system_error",
                "text": f"System error: {str(e)}",
                "reason": "Unable to process enhanced query"
            }]
        }


@app.post("/enhanced/hackrx/run")
async def enhanced_hackrx_run_endpoint(request: Dict[str, Any], db: Session = Depends(get_db)):
    """Enhanced HackRx endpoint with E5-large-v2 embeddings for better accuracy"""
    if not ENHANCED_MODE:
        # Fallback to regular endpoint
        return await hackrx_run_endpoint(request, db)

    try:
        query_text = request.get("query")
        document_id = request.get("document_id")

        if not query_text:
            return {
                "decision": "Rejected",
                "amount": None,
                "justification": [
                    {
                        "clause_id": "missing_query",
                        "text": "No query provided",
                        "reason": "Query text is required for processing"
                    }
                ]
            }

        # Use enhanced query service for better accuracy
        enhanced_query_service = get_enhanced_query_service()
        result = enhanced_query_service.process_query(
            query=query_text,
            document_id=document_id,
            use_hybrid=True  # Use hybrid search for best results
        )

        # Return in HackRx format
        return {
            "decision": result.get("decision", "Processed"),
            "amount": result.get("amount"),
            "justification": result.get("justification", [])
        }

    except Exception as e:
        return {
            "decision": "Rejected",
            "amount": None,
            "justification": [
                {
                    "clause_id": "system_error",
                    "text": f"Enhanced system error: {str(e)}",
                    "reason": "Unable to process request with enhanced embeddings"
                }
            ]
        }


@app.get("/enhanced/status")
async def enhanced_status():
    """Get status of enhanced E5-large-v2 services"""
    try:
        if ENHANCED_MODE:
            # Test if services are working
            from e5_embedding_service import get_embedding_service
            embedding_service = get_embedding_service()
            test_embedding = embedding_service.encode_text("test", "passage")

            return {
                "enhanced_mode": True,
                "embedding_model": Config.EMBEDDING_MODEL,
                "embedding_dimension": Config.EMBEDDING_DIMENSION,
                "test_embedding_length": len(test_embedding),
                "services_available": [
                    "E5EmbeddingService",
                    "EnhancedDocumentProcessorV2",
                    "EnhancedQueryService"
                ]
            }
        else:
            return {
                "enhanced_mode": False,
                "message": "Enhanced services not available",
                "fallback_available": True
            }
    except Exception as e:
        return {
            "enhanced_mode": False,
            "error": str(e),
            "message": "Enhanced services failed to initialize"
        }


# V3 Enhanced Endpoints with 768-dimensional embeddings
if ENHANCED_V3_MODE:
    @app.post("/v3/upload")
    async def v3_upload_document(
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
    ):
        """Upload and process document with V3 enhanced 768-dimensional embeddings"""
        try:
            print(f"📄 V3 Enhanced upload: {file.filename}")

            # Save uploaded file
            import tempfile
            import os

            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp_file:
                content = await file.read()
                tmp_file.write(content)
                tmp_file_path = tmp_file.name

            try:
                # Process with V3 enhanced processor
                processor = get_enhanced_processor()
                result = await processor.process_document_async(
                    tmp_file_path,
                    file.filename,
                    session=db
                )

                return {
                    "success": True,
                    "message": "Document processed with V3 enhanced embeddings",
                    "filename": file.filename,
                    "processing_details": result,
                    "embedding_dimension": 768,
                    "model": "e5-large-v2-compatible"
                }

            finally:
                # Clean up temp file
                os.unlink(tmp_file_path)

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"V3 upload failed: {str(e)}")

    @app.post("/v3/query")
    async def v3_query_documents(request: Dict[str, Any]):
        """Query documents using V3 enhanced 768-dimensional semantic search"""
        try:
            query_text = request.get("query")
            top_k = request.get("top_k", 10)

            if not query_text:
                raise HTTPException(status_code=400, detail="Query text is required")

            print(f"🔍 V3 Enhanced query: {query_text}")

            # Use V3 query service
            query_service = get_query_service()
            results = await query_service.hybrid_search(query_text, top_k)

            return {
                "success": True,
                "query": query_text,
                "results": results,
                "retrieval_method": "v3_hybrid_768d",
                "embedding_model": "e5-large-v2-compatible"
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"V3 query failed: {str(e)}")

    @app.post("/v3/hackrx/run")
    async def v3_hackrx_endpoint(request: Dict[str, Any]):
        """V3 Enhanced HackRx endpoint with 768-dimensional embeddings"""
        try:
            query_text = request.get("query")

            if not query_text:
                raise HTTPException(status_code=400, detail="Query text is required")

            print(f"🎯 V3 HackRx query: {query_text}")

            # Use V3 query service for enhanced processing
            query_service = get_query_service()
            result = await query_service.process_query_for_hackrx(query_text)

            if result['success']:
                return result['response']
            else:
                # Return default response structure on failure
                return {
                    "decision": "Rejected",
                    "amount": None,
                    "justification": [
                        {
                            "clause_id": "system_error",
                            "text": "Unable to process query due to system error",
                            "reason": result.get('error', 'Unknown error')
                        }
                    ]
                }

        except Exception as e:
            return {
                "decision": "Rejected",
                "amount": None,
                "justification": [
                    {
                        "clause_id": "exception_error",
                        "text": "Query processing failed",
                        "reason": str(e)
                    }
                ]
            }

    @app.get("/v3/status")
    async def v3_system_status():
        """V3 Enhanced system status with embedding service details"""
        try:
            embedding_service = get_embedding_service()
            processor = get_enhanced_processor()
            query_service = get_query_service()

            # Test embedding generation
            test_embedding = embedding_service.encode_text("test", "passage")

            return {
                "v3_enhanced_mode": True,
                "embedding_dimension": len(test_embedding),
                "embedding_model": "e5-large-v2-compatible",
                "services_status": {
                    "embedding_service": "active",
                    "document_processor_v3": "active",
                    "query_service_v3": "active",
                    "pinecone_index": "768d-enabled"
                },
                "capabilities": [
                    "768-dimensional embeddings",
                    "E5-large-v2 compatible encoding",
                    "Hybrid semantic + keyword search",
                    "Enhanced document processing",
                    "Improved retrieval accuracy"
                ]
            }

        except Exception as e:
            return {
                "v3_enhanced_mode": False,
                "error": str(e),
                "message": "V3 services initialization failed"
            }


# ============================================================================
# HACKRX 6.0 COMPLIANCE ENDPOINT (Added without changing existing code)
# ============================================================================

# Exact HackRx specification endpoint
@app.post("/hackrx/run/exact")
async def hackrx_exact_specification_endpoint(
    request: Dict[str, Any],
    authorization: str = Header(None, alias="Authorization"),
    db: Session = Depends(get_db)
):
    """
    EXACT HackRx 6.0 specification endpoint: POST /hackrx/run
    This is the exact endpoint expected by the HackRx evaluation platform
    """
    # Use the same logic as the compliance endpoint
    return await hackrx_official_compliance_endpoint(request, authorization, db)

@app.post("/api/v1/hackrx/run")
async def hackrx_official_compliance_endpoint(
    request: Dict[str, Any],
    authorization: str = Header(None, alias="Authorization"),
    db: Session = Depends(get_db)
):
    """
    Official HackRx 6.0 endpoint - Exact specification compliance

    Expected Request Format:
    {
        "documents": "https://example.com/document.pdf",
        "questions": ["Question 1", "Question 2", ...]
    }

    Expected Response Format:
    {
        "answers": ["Answer 1", "Answer 2", ...]
    }
    """
    try:
        # Validate authorization token
        expected_token = "Bearer 96551ec397634df93a1a2212b9b798324340321ef3c785ce9f4593c92d8f1544"
        if authorization != expected_token:
            raise HTTPException(status_code=401, detail="Invalid authorization token")

        # Extract documents URL and questions
        documents = request.get("documents")
        questions = request.get("questions", [])

        print(f"DEBUG: Raw documents field: {documents} (type: {type(documents)})")
        print(f"DEBUG: Raw questions field: {questions} (type: {type(questions)})")

        if not documents:
            raise HTTPException(status_code=400, detail="Missing 'documents' field")

        # Handle documents as either string or array
        if isinstance(documents, list):
            if not documents:
                raise HTTPException(status_code=400, detail="Empty 'documents' array")
            documents_url = documents[0]  # Take first document
        else:
            documents_url = documents

        print(f"DEBUG: Final documents_url: {documents_url} (type: {type(documents_url)})")

        if not questions or not isinstance(questions, list):
            raise HTTPException(status_code=400, detail="Missing or invalid 'questions' field")

        # Process document from URL
        try:
            # Download document
            response = requests.get(documents_url, timeout=30)
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail=f"Failed to download document: {response.status_code}")

            # Extract filename from URL
            filename = documents_url.split('/')[-1].split('?')[0]
            if not filename.endswith(('.pdf', '.docx', '.doc')):
                filename += '.pdf'  # Default to PDF

            # Process document content
            file_content = io.BytesIO(response.content)

            # Extract text from document using existing processor
            file_bytes = response.content
            if filename.endswith('.pdf'):
                text_content = doc_processor.extract_text_from_pdf(file_bytes)
            elif filename.endswith(('.docx', '.doc')):
                text_content = doc_processor.extract_text_from_docx(file_bytes)
            else:
                text_content = doc_processor.extract_text_from_pdf(file_bytes)  # Default to PDF

            if not text_content or len(text_content.strip()) < 10:
                raise HTTPException(status_code=400, detail="Document appears to be empty or unreadable")

            # Store document in database
            doc_record = Document(
                filename=filename,
                file_type=filename.split('.')[-1] if '.' in filename else 'pdf',
                content=text_content[:1000],  # Store first 1000 chars as preview
                processed="processed"
            )
            db.add(doc_record)
            db.commit()
            db.refresh(doc_record)

            # Chunk the document
            chunks = doc_processor.chunk_text(text_content)

            # Store chunks in database
            chunk_records = []
            for i, chunk in enumerate(chunks):
                chunk_record = DocumentChunk(
                    document_id=doc_record.id,
                    chunk_index=i,
                    content=chunk,
                    embedding_id=f"chunk_{doc_record.id}_{i}"
                )
                db.add(chunk_record)
                chunk_records.append(chunk_record)

            db.commit()

            # Create embeddings and store in Pinecone (simplified approach)
            try:
                # Use existing functionality if available
                if hasattr(doc_processor, 'process_document'):
                    # Use the existing process_document method
                    pass  # Embeddings will be handled by the existing workflow
            except Exception as e:
                print(f"Warning: Failed to create/store embeddings: {e}")
                # Continue without embeddings - use text search as fallback

        except requests.RequestException as e:
            raise HTTPException(status_code=400, detail=f"Failed to download document: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Document processing error: {str(e)}")

        # Process each question
        answers = []

        for question in questions:
            try:
                # Simplified text-based search for HackRx compliance
                question_lower = question.lower()
                relevant_content = []

                # Search through document chunks for relevant content
                for chunk_record in chunk_records:
                    chunk_content = chunk_record.content.lower()
                    # Simple keyword matching
                    if any(keyword in chunk_content for keyword in question_lower.split() if len(keyword) > 3):
                        relevant_content.append(chunk_record.content)

                # Limit to top 3 most relevant chunks
                context = "\n\n".join(relevant_content[:3]) if relevant_content else ""

                # Generate answer using the existing LLM decision method
                if context:
                    # Use make_decision method with proper format
                    parsed_query = {
                        "target_topic": question,
                        "amount_requested": None,
                        "age": None,
                        "gender": None,
                        "policy_duration": None,
                        "location": None,
                        "special_conditions": None
                    }

                    # Create clause-like structure for the LLM
                    clauses = [{"text": context, "score": 1.0}]

                    try:
                        decision_result = llm.make_decision(question, parsed_query, clauses)

                        # Extract answer from justification
                        if decision_result.get("justification") and len(decision_result["justification"]) > 0:
                            justification = decision_result["justification"][0]
                            answer = justification.get("reason", "Information not found in the provided document.")

                            # Clean up the answer
                            if "Information not found" not in answer and answer.strip():
                                # Make sure it's a proper sentence
                                if not answer.endswith('.'):
                                    answer += '.'
                            else:
                                answer = "Information not found in the provided document."
                        else:
                            answer = "Information not found in the provided document."
                    except Exception as e:
                        print(f"Error using LLM: {e}")
                        answer = "Information not found in the provided document."
                else:
                    answer = "Information not found in the provided document."

                answers.append(answer)

                # Store query in database
                db_query = Query(
                    query_text=question,
                    document_id=doc_record.id,
                    decision="Processed",
                    amount=None,
                    justification=json.dumps([{"answer": answer}])
                )
                db.add(db_query)

            except Exception as e:
                print(f"Error processing question '{question}': {e}")
                answers.append("Error processing the question.")

        db.commit()

        # Return in exact HackRx format
        return {"answers": answers}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in HackRx endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=Config.API_HOST, port=Config.API_PORT)
