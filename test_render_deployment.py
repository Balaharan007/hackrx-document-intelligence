"""
Test script for deployed HackRx webhook on Render
"""
import requests
import time

def test_deployed_webhook(base_url):
    """Test the deployed webhook URL"""
    url = f"{base_url}/hackrx/run"

    headers = {
        "Authorization": "Bearer 96551ec397634df93a1a2212b9b798324340321ef3c785ce9f4593c92d8f1544",
        "Content-Type": "application/json"
    }

    # Test data matching HackRx format
    test_data = {
        "document_url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
        "questions": [
            "What is this document about?",
            "What is the main topic discussed?"
        ]
    }

    print(f"🔗 Testing deployed webhook at: {url}")
    print(f"📝 Questions: {test_data['questions']}")

    try:
        start_time = time.time()
        response = requests.post(url, json=test_data, headers=headers, timeout=120)
        end_time = time.time()

        print(f"⏱️  Response time: {end_time - start_time:.2f} seconds")
        print(f"📊 Status code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! Response format correct:")
            print(f"📋 Answers: {result}")

            # Verify HackRx format
            if "answers" in result and isinstance(result["answers"], list):
                print("✅ HackRx format compliance: PASSED")
                print(f"🎯 Ready for submission to: https://dashboard.hackrx.in/submissions")
                return True
            else:
                print("❌ HackRx format compliance: FAILED")
                return False
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error testing webhook: {str(e)}")
        return False

if __name__ == "__main__":
    # Replace with your actual Render URL after deployment
    render_url = input("Enter your Render app URL (e.g., https://hackrx-document-intelligence-xxxx.onrender.com): ").strip()

    if render_url:
        test_deployed_webhook(render_url)
    else:
        print("Please provide the Render URL after deployment")
