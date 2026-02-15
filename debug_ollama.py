import ollama
import sys

try:
    client = ollama.Client(host='http://localhost:11434')
    response = client.list()
    print("Raw response type:", type(response))
    print("Raw response:", response)
    
    if hasattr(response, 'models'):
        print("Models attribute found.")
        for m in response.models:
             print("Model:", m)
    elif isinstance(response, dict) and 'models' in response:
        print("Models key found in dict.")
        for m in response['models']:
             print("Model:", m)
    else:
        print("Could not parse models.")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
