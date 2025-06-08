import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from search import google_search
from tests.test_utils import get_test_logger

def test_google_search():
    logger = get_test_logger("test_google_search")
    api_key = os.getenv("GOOGLE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")
    query = "株式会社サンプル 東京都千代田区"
    results = google_search(query, api_key, cse_id, num=3)
    logger.info(f"Google検索結果: {results}")
    assert isinstance(results, list)
    assert 1 <= len(results) <= 3
    for item in results:
        assert "title" in item and "link" in item
    logger.info("単体テスト test_google_search: OK")

if __name__ == "__main__":
    test_google_search()
