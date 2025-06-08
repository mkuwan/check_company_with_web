import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scraper import scrape_page, scrape_recursive
from tests.test_utils import get_test_logger

def test_scrape_page():
    logger = get_test_logger("test_scraper")
    url = "https://www.example.com/"
    result = scrape_page(url)
    logger.info(f"スクレイピング結果: {result}")
    assert isinstance(result, dict)
    assert result['url'] == url
    assert 'title' in result and result['title']
    assert 'content' in result and len(result['content']) > 0
    logger.info("単体テスト test_scraper: OK")

def test_scrape_recursive():
    logger = get_test_logger("test_scraper_recursive")
    url = "https://www.example.com/"
    results = scrape_recursive(url, max_depth=2)
    logger.info(f"再帰スクレイピング結果: {results}")
    assert isinstance(results, list)
    assert len(results) >= 1
    for page in results:
        assert 'url' in page and 'title' in page and 'content' in page
    logger.info("単体テスト test_scrape_recursive: OK")

if __name__ == "__main__":
    test_scrape_page()
    test_scrape_recursive()
