"""
Script to test the deployed Render application
"""
import requests
import time
import json

def test_deployment():
    url = "https://hackrx-ixkk.onrender.com"
    
    print(f"Testing deployment at: {url}")
    
    # Test health endpoint
    try:
        health_response = requests.get(f"{url}/health", timeout=30)
        print(f"Health check status: {health_response.status_code}")
        if health_response.status_code == 200:
            print(f"Health response: {health_response.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")
    
    # Test HackRx endpoint
    hackrx_url = f"{url}/hackrx/run"
    headers = {
        "Authorization": "Bearer 96551ec397634df93a1a2212b9b798324340321ef3c785ce9f4593c92d8f1544",
        "Content-Type": "application/json"
    }
    
    test_data = {
        "questions": [
            "What is artificial intelligence?",
            "How does machine learning work?"
        ]
    }
    
    try:
        start_time = time.time()
        response = requests.post(hackrx_url, headers=headers, json=test_data, timeout=60)
        end_time = time.time()
        
        print(f"HackRx endpoint status: {response.status_code}")
        print(f"Response time: {end_time - start_time:.2f} seconds")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"Error response: {response.text}")
            return False
            
    except Exception as e:
        print(f"HackRx endpoint test failed: {e}")
        return False

if __name__ == "__main__":
    print("=== Render Deployment Test ===")
    success = test_deployment()
    
    if success:
        print("\n✅ Deployment is working! Ready for HackRx submission.")
        print("\nNext steps:")
        print("1. Go to https://dashboard.hackrx.in/submissions")
        print("2. Submit webhook URL: https://hackrx-ixkk.onrender.com/hackrx/run")
        print("3. Use Bearer token: 96551ec397634df93a1a2212b9b798324340321ef3c785ce9f4593c92d8f1544")
    else:
        print("\n❌ Deployment not ready yet. Wait for Render to finish deployment.")
