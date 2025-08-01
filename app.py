"""
Ultra-minimal FastAPI app for HackRx deployment
"""
import os
import sys
print(f"Starting app.py with Python {sys.version}")

try:
    from fastapi import FastAPI, HTTPException, Depends, status
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    import uvicorn
    print("FastAPI and uvicorn imported successfully")
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

app = FastAPI(title="HackRx Document Intelligence Agent")
security = HTTPBearer()

# HackRx token validation
HACKRX_TOKEN = "96551ec397634df93a1a2212b9b798324340321ef3c785ce9f4593c92d8f1544"

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != HACKRX_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    return credentials

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "HackRx Document Intelligence Agent"}

@app.post("/hackrx/run")
def hackrx_run(data: dict, token: str = Depends(verify_token)):
    """HackRx compliant endpoint with minimal processing"""
    try:
        questions = data.get("questions", [])
        if not questions:
            return {"answers": ["No questions provided"]}
        
        # Simple mock responses for now
        answers = []
        for i, question in enumerate(questions):
            answers.append(f"Answer {i+1}: Processed question about {len(question)} characters")
        
        return {"answers": answers}
    
    except Exception as e:
        print(f"Error in hackrx_run: {e}")
        return {"answers": [f"Error processing request: {str(e)}"]}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting uvicorn on port {port}")
    
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info"
        )
    except Exception as e:
        print(f"Error starting uvicorn: {e}")
        sys.exit(1)
