import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd

# Configuration
API_BASE_URL = "http://localhost:8000"

st.set_page_config(
    page_title="HackRx 6.0 Document Intelligence Agent",
    page_icon="📄",
    layout="wide"
)

st.title("📄 HackRx 6.0 Document Intelligence Agent")
st.markdown("*An intelligent system for document processing and query answering*")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox(
    "Choose a page:",
    ["Document Upload", "Query Documents", "View History", "API Testing"]
)

# Helper functions
def upload_document(file):
    """Upload document to API"""
    try:
        files = {"file": (file.name, file.getvalue(), file.type)}
        response = requests.post(f"{API_BASE_URL}/upload", files=files)
        return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}

def upload_document_from_url(url):
    """Upload document from URL to API"""
    try:
        payload = {"url": url}
        response = requests.post(f"{API_BASE_URL}/upload-url", json=payload)
        return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}

def query_documents(query_text, document_id=None):
    """Send query to API"""
    try:
        payload = {"query": query_text}
        if document_id:
            payload["document_id"] = document_id
        response = requests.post(f"{API_BASE_URL}/query", json=payload)
        return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_documents():
    """Get list of documents"""
    try:
        response = requests.get(f"{API_BASE_URL}/documents")
        return response.json()
    except Exception as e:
        return []

def get_queries():
    """Get list of queries"""
    try:
        response = requests.get(f"{API_BASE_URL}/queries")
        return response.json()
    except Exception as e:
        return []

def test_hackrx_endpoint(query_text):
    """Test the official HackRx endpoint"""
    try:
        payload = {"query": query_text}
        response = requests.post(f"{API_BASE_URL}/hackrx/run", json=payload)
        return response.json()
    except Exception as e:
        return {"decision": "Error", "amount": None, "justification": [{"clause_id": "error", "text": str(e), "reason": "API Error"}]}

# Page: Document Upload
if page == "Document Upload":
    st.header("📤 Upload Documents")
    
    # Create tabs for different upload methods
    tab1, tab2 = st.tabs(["📁 Upload File", "🌐 Upload from URL"])
    
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Upload New Document")
            uploaded_file = st.file_uploader(
                "Choose a file", 
                type=['pdf', 'docx', 'doc', 'txt'],
                help="Supported formats: PDF, DOCX, DOC, TXT"
            )
            
            if uploaded_file is not None:
                st.write("File details:")
                st.write(f"- Name: {uploaded_file.name}")
                st.write(f"- Size: {len(uploaded_file.getvalue())} bytes")
                st.write(f"- Type: {uploaded_file.type}")
                
                if st.button("🚀 Process Document", type="primary", key="upload_file"):
                    with st.spinner("Processing document..."):
                        result = upload_document(uploaded_file)
                    
                    if result.get("status") == "success":
                        st.success("✅ Document processed successfully!")
                        st.json(result)
                    else:
                        st.error(f"❌ Error: {result.get('message', 'Unknown error')}")
    
    with tab2:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Upload Document from URL")
            
            # URL input
            document_url = st.text_input(
                "Enter document URL",
                placeholder="https://example.com/document.pdf",
                help="Enter a direct URL to a PDF, DOCX, DOC, or TXT file"
            )
            
            # URL examples
            with st.expander("📋 URL Examples"):
                st.markdown("""
                **Supported URL formats:**
                - Direct file links: `https://example.com/document.pdf`
                - Google Drive: Use direct download links
                - Dropbox: Use direct download links
                - OneDrive: Use direct download links
                
                **Supported file types:**
                - PDF: `.pdf`
                - Word Documents: `.docx`, `.doc`
                - Text Files: `.txt`
                """)
            
            if document_url:
                st.write("URL details:")
                st.write(f"- URL: {document_url}")
                
                # Basic URL validation
                if document_url.startswith(('http://', 'https://')):
                    st.write("- Status: ✅ Valid URL format")
                else:
                    st.write("- Status: ❌ Invalid URL format (must start with http:// or https://)")
                
                if st.button("🌐 Process Document from URL", type="primary", key="upload_url", 
                           disabled=not document_url.startswith(('http://', 'https://'))):
                    with st.spinner("Downloading and processing document from URL..."):
                        result = upload_document_from_url(document_url)
                    
                    if result.get("status") == "success":
                        st.success("✅ Document downloaded and processed successfully!")
                        st.json(result)
                    else:
                        st.error(f"❌ Error: {result.get('message', 'Unknown error')}")
    
    with col2:
        st.subheader("📋 Uploaded Documents")
        documents = get_documents()
        
        if documents:
            for doc in documents:
                status_icon = "✅" if doc["processed"] == "processed" else "⏳" if doc["processed"] == "pending" else "❌"
                st.write(f"{status_icon} **{doc['filename']}**")
                st.write(f"   - ID: {doc['id']}")
                st.write(f"   - Type: {doc['file_type']}")
                st.write(f"   - Status: {doc['processed']}")
                st.write("---")
        else:
            st.info("No documents uploaded yet.")

# Page: Query Documents
elif page == "Query Documents":
    st.header("🔍 Query Documents")
    
    # Get available documents
    documents = get_documents()
    processed_docs = [doc for doc in documents if doc["processed"] == "processed"]
    
    if not processed_docs:
        st.warning("⚠️ No processed documents available. Please upload and process documents first.")
    else:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Ask a Question")
            
            # Document selection
            doc_options = {"All Documents": None}
            doc_options.update({f"{doc['filename']} (ID: {doc['id']})": doc['id'] for doc in processed_docs})
            
            selected_doc = st.selectbox(
                "Select Document (optional):",
                options=list(doc_options.keys())
            )
            
            # Query input
            query_text = st.text_area(
                "Enter your question:",
                placeholder="e.g., Does this policy cover maternity expenses? What are the waiting periods?",
                height=100
            )
            
            if st.button("🔍 Submit Query", type="primary"):
                if query_text.strip():
                    with st.spinner("Processing query..."):
                        document_id = doc_options[selected_doc]
                        result = query_documents(query_text, document_id)
                    
                    if result.get("status") == "success":
                        st.success("✅ Query processed successfully!")
                        
                        # Display results
                        col_decision, col_amount = st.columns(2)
                        
                        with col_decision:
                            decision = result["decision"]
                            if decision == "Approved":
                                st.success(f"**Decision:** {decision}")
                            else:
                                st.error(f"**Decision:** {decision}")
                        
                        with col_amount:
                            amount = result["amount"]
                            if amount is not None:
                                st.info(f"**Amount:** ${amount:,.2f}")
                            else:
                                st.info("**Amount:** Not applicable")
                        
                        # Display justification
                        st.subheader("📋 Justification")
                        for i, justification in enumerate(result["justification"], 1):
                            with st.expander(f"Clause {i}: {justification['clause_id']}"):
                                st.write("**Clause Text:**")
                                st.write(justification["text"])
                                st.write("**Reasoning:**")
                                st.write(justification["reason"])
                        
                        # Show parsed query
                        with st.expander("🔍 Parsed Query Details"):
                            st.json(result.get("parsed_query", {}))
                    
                    else:
                        st.error(f"❌ Error: {result.get('message', 'Unknown error')}")
                else:
                    st.warning("Please enter a query.")
        
        with col2:
            st.subheader("💡 Query Examples")
            example_queries = [
                "Does this policy cover maternity expenses?",
                "What is the waiting period for pre-existing conditions?",
                "Is dental treatment covered under this plan?",
                "What are the exclusions for this policy?",
                "Can I claim for outpatient consultations?",
                "What is the maximum coverage amount?"
            ]
            
            for example in example_queries:
                if st.button(f"📝 {example}", key=f"example_{example}"):
                    st.experimental_rerun()

# Page: View History
elif page == "View History":
    st.header("📊 Query History")
    
    queries = get_queries()
    
    if queries:
        # Create dataframe for display
        df_data = []
        for query in queries:
            df_data.append({
                "ID": query["id"],
                "Query": query["query_text"][:50] + "..." if len(query["query_text"]) > 50 else query["query_text"],
                "Decision": query["decision"],
                "Amount": f"${query['amount']:,.2f}" if query["amount"] else "N/A",
                "Timestamp": query["timestamp"]
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True)
        
        # Detailed view
        st.subheader("📋 Detailed View")
        selected_query_id = st.selectbox(
            "Select a query to view details:",
            options=[q["id"] for q in queries],
            format_func=lambda x: f"Query {x}: {next(q['query_text'][:30] for q in queries if q['id'] == x)}..."
        )
        
        if selected_query_id:
            try:
                response = requests.get(f"{API_BASE_URL}/queries/{selected_query_id}")
                query_details = response.json()
                
                st.write(f"**Query:** {query_details['query_text']}")
                st.write(f"**Decision:** {query_details['decision']}")
                st.write(f"**Amount:** ${query_details['amount']:,.2f}" if query_details['amount'] else "**Amount:** N/A")
                st.write(f"**Timestamp:** {query_details['timestamp']}")
                
                st.subheader("Justification Details")
                for i, justification in enumerate(query_details["justification"], 1):
                    with st.expander(f"Clause {i}: {justification['clause_id']}"):
                        st.write("**Text:**", justification["text"])
                        st.write("**Reason:**", justification["reason"])
            
            except Exception as e:
                st.error(f"Error loading query details: {e}")
    
    else:
        st.info("No queries found. Start by querying some documents!")

# Page: API Testing
elif page == "API Testing":
    st.header("🧪 API Testing")
    st.write("Test the official HackRx `/hackrx/run` endpoint")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Test Query")
        test_query = st.text_area(
            "Enter test query:",
            placeholder="Enter your test query here...",
            height=100
        )
        
        if st.button("🚀 Test HackRx Endpoint", type="primary"):
            if test_query.strip():
                with st.spinner("Testing API endpoint..."):
                    result = test_hackrx_endpoint(test_query)
                
                st.subheader("📋 API Response")
                st.json(result)
            else:
                st.warning("Please enter a test query.")
    
    with col2:
        st.subheader("📚 API Documentation")
        st.markdown("""
        **Endpoint:** `POST /hackrx/run`
        
        **Request Format:**
        ```json
        {
            "query": "Your question here",
            "document_url": "optional_document_url"
        }
        ```
        
        **Response Format:**
        ```json
        {
            "decision": "Approved/Rejected",
            "amount": numeric_or_null,  
            "justification": [
                {
                    "clause_id": "...",
                    "text": "...",
                    "reason": "..."
                }
            ]
        }
        ```
        """)

# Footer
st.markdown("---")
st.markdown("*HackRx 6.0 Document Intelligence Agent - Built with Streamlit, FastAPI, Pinecone, and Gemini*")
