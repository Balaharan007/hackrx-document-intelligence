# HackRx 6.0 Complete Submission Guide

## 📋 Pre-Submission Checklist

### ✅ Required Endpoint Verification
- [x] POST `/hackrx/run` endpoint exists
- [x] Bearer token authentication implemented
- [x] Accepts `documents` (string) and `questions` (array)
- [x] Returns `{"answers": ["answer1", "answer2", ...]}` format
- [x] HTTPS capability for deployment
- [x] Response time under 30 seconds

## 🚀 Step-by-Step Submission Process

### Step 1: Local Testing
```bash
# 1. Start your FastAPI server
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 2. Test the endpoint locally
curl -X POST "http://localhost:8000/hackrx/run" \
  -H "Authorization: Bearer 96551ec397634df93a1a2212b9b798324340321ef3c785ce9f4593c92d8f1544" \
  -H "Content-Type: application/json" \
  -d '{
    "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D",
    "questions": ["What is the grace period for premium payment?"]
  }'
```

### Step 2: Deploy to Cloud Platform

#### Option A: Railway (Recommended)
1. **Create Railway Account**: Go to https://railway.app
2. **Connect GitHub**: Link your repository
3. **Deploy**: Railway will auto-detect your Python app
4. **Set Environment Variables**:
   ```
   PINECONE_API_KEY=your_pinecone_key
   GEMINI_API_KEY=your_gemini_key
   DATABASE_URL=your_postgres_url
   ```
5. **Your webhook URL**: `https://your-app-name.railway.app/hackrx/run`

#### Option B: Render
1. **Create Render Account**: Go to https://render.com
2. **New Web Service**: Connect your repository
3. **Configure**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn main:app --host 0.0.0.0 --port $PORT`
4. **Set Environment Variables** in Render dashboard
5. **Your webhook URL**: `https://your-app-name.onrender.com/hackrx/run`

#### Option C: Heroku
1. **Install Heroku CLI**: Download from https://devcenter.heroku.com/articles/heroku-cli
2. **Create Heroku App**:
   ```bash
   heroku create your-app-name
   heroku config:set PINECONE_API_KEY=your_key
   heroku config:set GEMINI_API_KEY=your_key
   heroku config:set DATABASE_URL=your_postgres_url
   git push heroku main
   ```
3. **Your webhook URL**: `https://your-app-name.herokuapp.com/hackrx/run`

### Step 3: Verify Deployment
```bash
# Test your deployed webhook
curl -X POST "https://your-deployed-url.com/hackrx/run" \
  -H "Authorization: Bearer 96551ec397634df93a1a2212b9b798324340321ef3c785ce9f4593c92d8f1544" \
  -H "Content-Type: application/json" \
  -d '{
    "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D",
    "questions": ["What is the grace period for premium payment?"]
  }'
```

### Step 4: Submit to HackRx Platform

1. **Go to Submissions Page**: https://dashboard.hackrx.in/submissions

2. **Fill the Form**:
   - **Webhook URL**: `https://your-deployed-url.com/hackrx/run`
   - **Submission Notes** (Optional): 
     ```
     FastAPI + Pinecone + Gemini 2.5 Pro Document Intelligence Agent.
     Features: PDF/DOCX processing, semantic search, LLM reasoning.
     Response time: <30s, HTTPS enabled, Bearer auth implemented.
     ```

3. **Click "Run"**: The platform will test your endpoint

4. **Monitor Results**: Check the evaluation results and scores

## 🔧 Technical Implementation Details

### Webhook Endpoint Structure
```python
@app.post("/hackrx/run")
async def hackrx_run_endpoint(
    request: Dict[str, Any], 
    authorization: str = Header(None, alias="Authorization"), 
    db: Session = Depends(get_db)
):
    # Validate Bearer token
    expected_token = "Bearer 96551ec397634df93a1a2212b9b798324340321ef3c785ce9f4593c92d8f1544"
    if authorization != expected_token:
        raise HTTPException(status_code=401, detail="Invalid authorization token")
    
    # Extract and process documents URL and questions
    documents_url = request.get("documents")
    questions = request.get("questions", [])
    
    # Process document and generate answers
    answers = []
    for question in questions:
        # Your document processing and LLM logic here
        answer = process_question(documents_url, question)
        answers.append(answer)
    
    # Return exact format required by HackRx
    return {"answers": answers}
```

### How the Webhook Works After Submission

1. **HackRx Platform Sends Request**:
   ```json
   POST https://your-app.com/hackrx/run
   Authorization: Bearer 96551ec397634df93a1a2212b9b798324340321ef3c785ce9f4593c92d8f1544
   Content-Type: application/json
   
   {
     "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf?...",
     "questions": ["Question 1", "Question 2", ...]
   }
   ```

2. **Your API Processes**:
   - Downloads document from provided URL
   - Extracts text content
   - Chunks and processes with embeddings
   - Uses LLM to answer each question
   - Returns structured response

3. **Platform Evaluates**:
   - Checks response format compliance
   - Evaluates answer quality and accuracy
   - Measures response time
   - Generates score and feedback

## 🔍 Troubleshooting Common Issues

### Issue 1: Timeout Errors
**Solution**: Optimize document processing and use async operations

### Issue 2: Invalid Response Format
**Solution**: Ensure response has exact `{"answers": [...]}` structure

### Issue 3: Authentication Failures
**Solution**: Verify Bearer token matches exactly

### Issue 4: Document Download Failures
**Solution**: Handle various URL formats and add proper error handling

## 📊 Success Metrics

- ✅ **Response Time**: Under 30 seconds
- ✅ **Format Compliance**: Exact JSON structure
- ✅ **Authentication**: Proper Bearer token validation
- ✅ **HTTPS**: Secure connection required
- ✅ **Reliability**: Handles various document formats
- ✅ **Accuracy**: Relevant and accurate answers

## 🎯 Final Checklist Before Submission

- [ ] Local testing passes
- [ ] Deployed to cloud platform
- [ ] HTTPS enabled
- [ ] Bearer token authentication works
- [ ] Response format is `{"answers": [...]}`
- [ ] Handles PDF document processing
- [ ] Response time under 30 seconds
- [ ] Error handling implemented
- [ ] Environment variables configured
- [ ] Webhook URL accessible publicly

## 🚀 Quick Deployment Commands

### For Railway:
```bash
# Connect to Railway and deploy
railway login
railway link
railway up
```

### For Render:
```bash
# Push to GitHub, then connect in Render dashboard
git add .
git commit -m "Ready for HackRx submission"
git push origin main
```

### For Heroku:
```bash
# Deploy to Heroku
heroku create your-hackrx-app
git push heroku main
heroku ps:scale web=1
```

---

**Ready to Submit!** 🎉

Once deployed, your webhook URL will be: `https://your-app-domain.com/hackrx/run`

Submit this URL at: https://dashboard.hackrx.in/submissions
