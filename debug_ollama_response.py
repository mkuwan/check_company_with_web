# Debug Ollama response to understand JSON parsing issue
import requests
import json

def debug_ollama_response():
    """Debug what Ollama is actually returning"""
    
    ollama_url = "http://localhost:11434/api/chat"
    ollama_model = "llama3.1:latest"
    
    prompt = """
以下のJSON形式のみで回答してください：
{
    "score": 0.85,
    "reasoning": "テスト用の応答です",
    "matched_info": ["テスト"],
    "confidence": 0.9
}

重要: JSON以外の文字は一切出力しないでください。
"""

    payload = {
        "model": ollama_model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }
    
    try:
        print("Sending request to Ollama...")
        response = requests.post(ollama_url, json=payload, timeout=120)
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        print("\n--- Raw response content ---")
        print(repr(response.text))
        
        print("\n--- Processing line by line ---")
        content = ""
        for i, line in enumerate(response.iter_lines()):
            if not line:
                print(f"Line {i}: Empty line")
                continue
            
            line_text = line.decode('utf-8')
            print(f"Line {i}: {repr(line_text)}")
            
            try:
                line_data = json.loads(line_text)
                print(f"  Parsed JSON: {line_data}")
                
                if line_data.get("done", False):
                    print("  -> Done flag detected")
                    break
                    
                message_content = line_data.get("message", {}).get("content", "")
                if message_content:
                    print(f"  -> Adding content: {repr(message_content)}")
                    content += message_content
                    
            except json.JSONDecodeError as e:
                print(f"  -> JSON decode error: {e}")
        
        print(f"\n--- Final accumulated content ---")
        print(f"Content: {repr(content)}")
        
        if content.strip():
            print("\n--- Attempting to parse final JSON ---")
            try:
                result = json.loads(content.strip())
                print(f"Successfully parsed: {result}")
                return result
            except json.JSONDecodeError as e:
                print(f"Final JSON parse error: {e}")
                return None
        else:
            print("No content accumulated!")
            return None
            
    except Exception as e:
        print(f"Request error: {e}")
        return None

if __name__ == "__main__":
    debug_ollama_response()
