#!/usr/bin/env python3
"""
Quick deployment test for HackRx webhook
Run this after deploying to test your webhook URL
"""

import requests
import json
import sys
import time

def test_deployed_webhook(webhook_url):
    """Test the deployed webhook with HackRx format"""
    print(f"🔍 Testing HackRx webhook: {webhook_url}")
    
    if not webhook_url.startswith('https://'):
        print("❌ Error: Webhook URL must use HTTPS for HackRx submission")
        return False
    
    headers = {
        "Authorization": "Bearer 96551ec397634df93a1a2212b9b798324340321ef3c785ce9f4593c92d8f1544",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    test_data = {
        "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D",
        "questions": [
            "What is the grace period for premium payment under the National Parivar Mediclaim Plus Policy?",
            "What is the waiting period for pre-existing diseases (PED) to be covered?"
        ]
    }
    
    try:
        print("📤 Sending test request...")
        start_time = time.time()
        response = requests.post(webhook_url, headers=headers, json=test_data, timeout=60)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"⏱️ Response Time: {response_time:.2f} seconds")
        
        if response.status_code == 200:
            try:
                result = response.json()
                
                if "answers" in result:
                    answers = result["answers"]
                    print(f"✅ Response Format: Correct (has 'answers' key)")
                    print(f"📊 Number of Answers: {len(answers)}")
                    print(f"🎯 Expected Answers: {len(test_data['questions'])}")
                    
                    if len(answers) == len(test_data['questions']):
                        print("✅ Answer Count: Perfect match!")
                    else:
                        print("⚠️ Answer Count: Mismatch - check implementation")
                    
                    print("\\n📝 Sample Answers:")
                    for i, answer in enumerate(answers[:2]):
                        print(f"   {i+1}. {answer[:100]}{'...' if len(answer) > 100 else ''}")
                    
                    if response_time < 30:
                        print("✅ Response Time: Under 30 seconds")
                    else:
                        print("⚠️ Response Time: Over 30 seconds - may timeout on HackRx platform")
                    
                    print("\\n🎉 WEBHOOK TEST PASSED! Ready for HackRx submission!")
                    return True
                else:
                    print("❌ Response Format Error: Missing 'answers' key")
                    print(f"📄 Actual Response: {json.dumps(result, indent=2)}")
                    return False
                    
            except json.JSONDecodeError:
                print("❌ Response Format Error: Invalid JSON")
                print(f"📄 Raw Response: {response.text}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"📄 Error Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Timeout Error: Request took too long (>60s)")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Cannot reach the webhook URL")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

def main():
    """Main function"""
    print("🚀 HackRx Webhook Testing Tool")
    print("=" * 50)
    
    if len(sys.argv) != 2:
        print("Usage: python test_webhook.py YOUR_WEBHOOK_URL")
        print("\\nExample:")
        print("  python test_webhook.py https://myapp.railway.app/hackrx/run")
        print("  python test_webhook.py https://myapp.onrender.com/hackrx/run")
        print("  python test_webhook.py https://myapp.herokuapp.com/hackrx/run")
        sys.exit(1)
    
    webhook_url = sys.argv[1]
    
    # Validate URL format
    if not webhook_url.endswith('/hackrx/run'):
        print("⚠️ Warning: URL should end with '/hackrx/run'")
        confirm = input("Continue anyway? (y/N): ")
        if confirm.lower() != 'y':
            sys.exit(1)
    
    success = test_deployed_webhook(webhook_url)
    
    if success:
        print("\\n" + "=" * 50)
        print("🎯 READY FOR HACKRX SUBMISSION!")
        print("\\n📋 Next Steps:")
        print("1. Go to https://dashboard.hackrx.in/submissions")
        print(f"2. Enter webhook URL: {webhook_url}")
        print("3. Add submission notes (optional)")
        print("4. Click 'Run' to submit for evaluation")
        print("\\n🏆 Good luck with your submission!")
    else:
        print("\\n" + "=" * 50)
        print("❌ WEBHOOK TEST FAILED!")
        print("\\n🔧 Fix the issues before submitting to HackRx")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
