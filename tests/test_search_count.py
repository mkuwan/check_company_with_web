import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from search_count import read_api_count, write_api_count, check_and_confirm_api_count
from tests.test_utils import get_test_logger
import builtins

def test_search_count():
    logger = get_test_logger("test_search_count")
    test_date = "20991231"  # テスト用未来日付で衝突回避
    # 初期値書き込み
    write_api_count(0, test_date)
    count = read_api_count(test_date)
    logger.info(f"初期値: {count}")
    assert count == 0
    # 1加算
    check_and_confirm_api_count(add_count=1, date_str=test_date)
    count2 = read_api_count(test_date)
    logger.info(f"加算後: {count2}")
    assert count2 == 1
    logger.info("単体テスト test_search_count: OK")

def test_api_count_limit_yes(monkeypatch):
    """
    MAX_API_COUNT=2で2回加算後、3回目でyesを入力して継続するテスト
    """
    logger = get_test_logger("test_search_count_limit_yes")
    os.environ["MAX_API_COUNT"] = "2"
    test_date = "20991231"
    write_api_count(2, test_date)
    # 3回目で上限超過、yesで継続
    monkeypatch.setattr(builtins, "input", lambda: "yes")
    result = check_and_confirm_api_count(add_count=1, date_str=test_date)
    assert result == 3
    logger.info("API上限超過時yesで継続: OK")

def test_api_count_limit_no(monkeypatch):
    """
    MAX_API_COUNT=2で2回加算後、3回目でnoを入力して終了するテスト
    """
    logger = get_test_logger("test_search_count_limit_no")
    os.environ["MAX_API_COUNT"] = "2"
    test_date = "20991230"
    write_api_count(2, test_date)
    # 3回目で上限超過、noで終了
    monkeypatch.setattr(builtins, "input", lambda: "no")
    try:
        check_and_confirm_api_count(add_count=1, date_str=test_date)
        assert False, "no入力時はexit(0)で終了すべき"
    except SystemExit:
        logger.info("API上限超過時noで終了: OK")

if __name__ == "__main__":
    test_search_count()
