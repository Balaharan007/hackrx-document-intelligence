"""
Absolutely minimal HackRx API - Just the essentials
"""
from fastapi import FastAPI, HTTPException
import os

app = FastAPI()

print("🚀 Minimal HackRx API starting...")

@app.get("/")
def read_root():
    return {"message": "HackRx Document Intelligence API", "status": "online"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/hackrx/run")
def hackrx_endpoint(request_data: dict):
    """
    HackRx endpoint - minimal version for testing deployment
    """
    try:
        # Extract data
        document_url = request_data.get("document_url", "")
        questions = request_data.get("questions", [])
        
        # Simple mock responses
        answers = []
        for question in questions:
            answers.append(f"Mock answer for: {question}")
        
        return {"answers": answers}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
