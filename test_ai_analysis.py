# Test AI analysis with debug output
import requests
import json
from analyzer import ai_analyze_content

# Test data
application_info = [
    "株式会社サンプル",
    "東京都千代田区1-1-1", 
    "03-1234-5678",
    "東京支店"
]

scraped_content = {
    "title": "株式会社サンプル - 会社概要",
    "url": "https://example.com/company",
    "content": "株式会社サンプルは東京都千代田区に本社を置く総合商社です。設立は1985年、従業員数は500名。主な事業は貿易業務、投資業務。",
    "links": ["https://example.com/about", "https://example.com/contact"]
}

ollama_url = "http://localhost:11434/api/chat"
ollama_model = "llama3.1:latest"

print("Testing AI analysis...")
try:
    # First test if Ollama is running
    test_response = requests.get("http://localhost:11434/api/tags", timeout=10)
    print(f"Ollama server status: {test_response.status_code}")
    
    # Now test the analysis function
    result = ai_analyze_content(application_info, scraped_content, ollama_url, ollama_model)
    print(f"Analysis result: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
except Exception as e:
    print(f"Error: {e}")
