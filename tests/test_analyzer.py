import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from analyzer import ai_generate_query
from tests.test_utils import get_test_logger

def test_ai_generate_query():
    logger = get_test_logger("test_ai_generate_query")
    application_info = [
        "株式会社サンプル",
        "東京都千代田区1-1-1",
        "03-1234-5678",
        "東京支店",
        "旧サンプル株式会社"
    ]
    ollama_url = "http://localhost:11434/api/chat"
    ollama_model = "llama3.1:latest"
    queries = ai_generate_query(application_info, ollama_url, ollama_model, max_queries=3)
    logger.info(f"AI生成クエリリスト: {queries}")
    assert isinstance(queries, list)
    assert 1 <= len(queries) <= 3
    for q in queries:
        assert '「' not in q and '」' not in q, "クエリに括弧が含まれている"
    logger.info("単体テスト test_ai_generate_query: OK")

if __name__ == "__main__":
    test_ai_generate_query()
