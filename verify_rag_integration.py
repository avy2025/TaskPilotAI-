import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_rag_mode():
    print("\n--- Testing RAG Mode ---")
    payload = {
        "query": "What is TaskPilotAI?",
        "use_rag": True
    }
    
    try:
        response = requests.post(f"{BASE_URL}/run-agent", json=payload)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Response Keys:", data.keys())
            print("Answer Preview:", data.get("answer", "")[:100] + "...")
            print("Sources Count:", len(data.get("sources", [])))
            
            if "answer" in data and "sources" in data:
                print("✅ RAG Mode Test Passed")
                return True
            else:
                print("❌ RAG Mode Test Failed: Missing keys")
                return False
        else:
            print(f"❌ RAG Mode Test Failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error during RAG Mode Test: {e}")
        return False

def test_agent_mode_sse():
    print("\n--- Testing Agent Mode (SSE) ---")
    payload = {
        "task": "Research the latest iPhone model",
        "use_rag": False
    }
    
    try:
        # stream=True for SSE
        response = requests.post(f"{BASE_URL}/run-agent", json=payload, stream=True)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            first_event = False
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith("data: "):
                        event_data = json.loads(line_str[6:])
                        print(f"Received event: {event_data.get('type')}")
                        first_event = True
                        break # Just check if we get anything
            
            if first_event:
                print("✅ Agent Mode (SSE) Test Passed")
                return True
            else:
                print("❌ Agent Mode (SSE) Test Failed: No events received")
                return False
        else:
            print(f"❌ Agent Mode (SSE) Test Failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error during Agent Mode (SSE) Test: {e}")
        return False

if __name__ == "__main__":
    # Note: Ensure server is running on localhost:8000 before running this
    print("Starting Verification...")
    rag_success = test_rag_mode()
    agent_success = test_agent_mode_sse()
    
    if rag_success and agent_success:
        print("\n✨ ALL VERIFICATIONS PASSED ✨")
    else:
        print("\n⚠️ SOME VERIFICATIONS FAILED ⚠️")
