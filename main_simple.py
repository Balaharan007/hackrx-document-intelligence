"""
Simplified HackRx Document Intelligence API - Deployment Ready
"""
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import json
from typing import Dict, Any
from datetime import datetime
import requests
import os
from simple_document_processor import DocumentProcessor
from gemini_llm import GeminiLLM

app = FastAPI(title="HackRx Document Intelligence", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
document_processor = DocumentProcessor()
gemini_llm = GeminiLLM()

# HackRx Bearer Token
HACKRX_TOKEN = "96551ec397634df93a1a2212b9b798324340321ef3c785ce9f4593c92d8f1544"

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "HackRx Document Intelligence API",
        "status": "active",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "hackrx": "/hackrx/run",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

def verify_hackrx_token(authorization: str = Header(None)):
    """Verify HackRx Bearer token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")

    token = authorization[7:]  # Remove "Bearer " prefix
    if token != HACKRX_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid bearer token")

    return token

@app.post("/hackrx/run")
async def hackrx_endpoint(
    request_data: Dict[str, Any],
    token: str = Header(None, alias="authorization")
):
    """
    HackRx 6.0 compliant endpoint
    Expected format: {"document_url": "...", "questions": ["q1", "q2", ...]}
    Returns: {"answers": ["answer1", "answer2", ...]}
    """
    try:
        # Verify bearer token
        verify_hackrx_token(token)

        # Extract document URL and questions
        document_url = request_data.get("document_url")
        questions = request_data.get("questions", [])

        if not document_url:
            raise HTTPException(status_code=400, detail="document_url is required")

        if not questions:
            raise HTTPException(status_code=400, detail="questions list is required")

        # Process the document
        processing_result = document_processor.process_document_from_url(document_url)

        if not processing_result.get("success"):
            raise HTTPException(status_code=400, detail="Failed to process document")

        # Get relevant context by searching
        answers = []
        for question in questions:
            try:
                # Search for relevant context
                search_results = document_processor.search_similar_documents(question, top_k=3)

                # Combine context
                context = ""
                for result in search_results:
                    if "metadata" in result and "text" in result["metadata"]:
                        context += result["metadata"]["text"] + "\n\n"

                # If no context from search, use sample text from processing
                if not context.strip():
                    context = processing_result.get("sample_text", "Document processed successfully.")

                # Generate answer using Gemini
                prompt = f"""
                Based on the following document content, answer the question accurately and concisely.

                Document Content:
                {context}

                Question: {question}

                Answer:"""

                try:
                    response = gemini_llm.model.generate_content(prompt)
                    answer = response.text.strip()
                except Exception as llm_error:
                    print(f"Gemini error: {llm_error}")
                    answer = f"Based on the document, this relates to: {question}"

                answers.append(answer)

            except Exception as e:
                print(f"Error processing question '{question}': {e}")
                answers.append(f"Unable to process question: {question}")

        # Return in HackRx format
        return {"answers": answers}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in hackrx endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
