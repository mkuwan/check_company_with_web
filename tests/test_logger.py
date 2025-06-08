import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from logger import Logger
from tests.test_utils import get_test_logger
from datetime import datetime

def test_logger():
    logger = get_test_logger("test_logger")
    logger.debug("デバッグメッセージ")
    logger.info("情報メッセージ")
    logger.warning("警告メッセージ")
    logger.error("エラーメッセージ")
    logger.info("extra_dataテスト", {
        "user_id": "test_user",
        "timestamp": datetime.now().isoformat()
    })
    try:
        1 / 0
    except Exception:
        logger.error("ゼロ除算エラー発生", exc_info=True)
    logger.info("単体テスト test_logger: OK")

if __name__ == "__main__":
    test_logger()
