#!/usr/bin/env python3
"""
Absolute minimal FastAPI app for HackRx deployment
"""
import os

try:
    from fastapi import FastAPI, HTTPException, Depends, Request
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    import uvicorn
    print("✅ FastAPI imports successful")
except Exception as e:
    print(f"❌ Import failed: {e}")
    exit(1)

app = FastAPI()
security = HTTPBearer()
TOKEN = "96551ec397634df93a1a2212b9b798324340321ef3c785ce9f4593c92d8f1544"

def verify_token(creds: HTTPAuthorizationCredentials = Depends(security)):
    if creds.credentials != TOKEN:
        raise HTTPException(401, "Invalid token")
    return creds

@app.get("/")
def read_root():
    return {"message": "HackRx Agent Running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/hackrx/run")
async def hackrx_run(request: Request, token=Depends(verify_token)):
    try:
        data = await request.json()
        questions = data.get("questions", [])
        answers = [f"Answer {i+1}: {len(q)} chars" for i, q in enumerate(questions)]
        return {"answers": answers}
    except Exception as e:
        return {"answers": [f"Error: {str(e)}"]}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
