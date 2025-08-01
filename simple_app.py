#!/usr/bin/env python3
"""
Ultra-minimal FastAPI app for HackRx deployment - Version 2
"""
import sys
import os

# Print startup info
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Working directory: {os.getcwd()}")
print(f"PORT environment variable: {os.environ.get('PORT', 'Not set')}")

# Import required packages
try:
    from fastapi import FastAPI, HTTPException, Depends, Request
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    import uvicorn
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Create FastAPI app
app = FastAPI(
    title="HackRx Document Intelligence Agent",
    description="Ultra-minimal version for deployment testing",
    version="1.0.0"
)

# Security
security = HTTPBearer()
HACKRX_TOKEN = "96551ec397634df93a1a2212b9b798324340321ef3c785ce9f4593c92d8f1544"

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != HACKRX_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials

@app.on_event("startup")
async def startup_event():
    print("🚀 FastAPI app startup complete")

@app.get("/")
async def root():
    return {
        "status": "running",
        "service": "HackRx Document Intelligence Agent",
        "version": "ultra-minimal-v2"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "HackRx Document Intelligence Agent",
        "python_version": sys.version,
        "environment": "production"
    }

@app.post("/hackrx/run")
async def hackrx_run(request: Request, token: str = Depends(verify_token)):
    try:
        # Get JSON data
        data = await request.json()
        questions = data.get("questions", [])
        
        if not questions:
            return {"answers": ["No questions provided"]}
        
        # Simple processing
        answers = []
        for i, question in enumerate(questions):
            answers.append(f"Response {i+1}: Processed {len(question)} characters from question")
        
        print(f"✅ Processed {len(questions)} questions successfully")
        return {"answers": answers}
    
    except Exception as e:
        print(f"❌ Error in hackrx_run: {e}")
        return {"answers": [f"Error: {str(e)}"]}

# Main execution
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    print(f"🌟 Starting server on {host}:{port}")
    
    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
