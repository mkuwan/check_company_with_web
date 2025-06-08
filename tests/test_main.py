import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from logger import LoggerManager
from main import main
from tests.test_utils import get_test_logger

def test_main_py():
    logger = get_test_logger("test_main_py")
    logger.info("main.py結合テスト開始")
    # テスト用のコマンドライン引数をセット
    sys.argv = [
        "main.py",
        "--company", "株式会社サンプル",
        "--address", "東京都千代田区1-1-1",
        "--tel", "03-1234-5678",
        "--other", "東京支店", "旧サンプル株式会社"
    ]
    try:
        main()
        logger.info("main.py結合テスト: OK")
    except Exception as e:
        logger.error(f"main.py結合テスト: NG {e}", exc_info=True)

if __name__ == "__main__":
    test_main_py()
