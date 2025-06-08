import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
import os
from logger import LoggerManager
from pathlib import Path

def get_test_logger(test_name: str):
    """
    tests/logs/配下にテストごとのログファイルを出力するロガーを返す
    """
    log_dir = Path("tests/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file_path = log_dir / f"{test_name}.log"
    logger = LoggerManager.get_logger(test_name, str(log_file_path), "INFO")
    return logger

def test_write_result_json():
    from utils import write_result_json
    import json
    import os
    test_result = {
        "company": "株式会社サンプル",
        "address": "東京都千代田区1-1-1",
        "tel": "03-1234-5678",
        "results": [
            {"url": "https://sample.co.jp", "score": 0.97, "is_real": True, "reason": "Web上の複数サイトで一致情報を確認"}
        ],
        "searched_url_count": 1,
        "found": True,
        "early_terminated": False
    }
    file_path = "tests/result_test.json"
    write_result_json(test_result, file_path)
    assert os.path.exists(file_path)
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)
    assert data["company"] == "株式会社サンプル"
    assert data["results"][0]["url"] == "https://sample.co.jp"
    os.remove(file_path)
    print("test_write_result_json: OK")

if __name__ == "__main__":
    test_write_result_json()
