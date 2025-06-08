import os
from datetime import datetime

from config import load_config

COUNT_FILE_TEMPLATE = "api_log/search_api_count_{date}.txt"
MAX_API_COUNT = 100


def get_today_count_file(date_str=None):
    if date_str is None:
        date_str = datetime.now().strftime("%Y%m%d")
    return COUNT_FILE_TEMPLATE.format(date=date_str)


def read_api_count(date_str=None):
    file = get_today_count_file(date_str)
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            try:
                return int(f.read().strip())
            except Exception:
                return 0
    return 0


def write_api_count(count, date_str=None):
    file = get_today_count_file(date_str)
    dir_path = os.path.dirname(file)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
    with open(file, 'w', encoding='utf-8') as f:
        f.write(str(count))


def check_and_confirm_api_count(add_count=1, max_count=None, date_str=None):
    # .envのMAX_API_COUNTを優先
    config = load_config()
    env_max = config.get("MAX_API_COUNT")
    if env_max is not None:
        try:
            max_count = int(env_max)
        except Exception:
            max_count = MAX_API_COUNT
    if max_count is None:
        max_count = MAX_API_COUNT
    current = read_api_count(date_str)
    if current + add_count > max_count:
        print(f"API使用回数が上限({max_count})に達しています。続けて検索しますか？ (yes/no): ", end="")
        ans = input().strip().lower()
        if ans != 'yes':
            print("処理を終了します。")
            exit(0)
    # カウントを加算して保存
    write_api_count(current + add_count, date_str)
    return current + add_count

# テスト関数

def test_api_count_reset():
    """
    日付が変わった場合のAPI回数リセット動作のテスト
    1. 前日分ファイルに値を書き込み
    2. 翌日分ファイルがなければ削除
    3. 翌日分でAPIカウント取得・加算し、リセットされていることを確認
    """
    prev_date = "20250607"
    next_date = "20250608"
    prev_file = get_today_count_file(prev_date)
    next_file = get_today_count_file(next_date)
    # 1. 前日分ファイルに値を書き込み
    write_api_count(5, prev_date)
    # 2. 翌日分ファイルがあれば削除
    if os.path.exists(next_file):
        os.remove(next_file)
    # 3. 翌日分でAPIカウント取得・加算
    before = read_api_count(next_date)
    after = check_and_confirm_api_count(add_count=1, date_str=next_date)
    # 4. 結果出力
    print(f"[テスト] {prev_file}の値: {read_api_count(prev_date)}")
    print(f"[テスト] {next_file}の初期値: {before}")
    print(f"[テスト] {next_file}の加算後: {after}")
    assert before == 0, "翌日分ファイルは初期値0であるべき"
    assert after == 1, "翌日分ファイルの加算後は1であるべき"
    print("[テスト] 日付が変わった場合のAPI回数リセット動作: OK")

def test_api_count_limit():
    """
    APIカウント上限超過時の挙動テスト
    1. MAX_API_COUNT=2に設定
    2. 2回加算し、3回目で上限超過時の挙動を確認
    """
    import builtins
    import sys
    test_date = "20991231"
    write_api_count(0, test_date)
    # 1回目: 0→1
    check_and_confirm_api_count(add_count=1, max_count=2, date_str=test_date)
    # 2回目: 1→2
    check_and_confirm_api_count(add_count=1, max_count=2, date_str=test_date)
    # 3回目: 上限超過、yes入力で継続
    print("[テスト] 上限超過時にyesを入力して継続するパターン")
    input_backup = builtins.input
    builtins.input = lambda: "yes"
    check_and_confirm_api_count(add_count=1, max_count=2, date_str=test_date)
    builtins.input = input_backup
    # 4回目: 上限超過、no入力で終了（exitをcatch）
    print("[テスト] 上限超過時にnoを入力して終了するパターン")
    write_api_count(2, test_date)
    builtins.input = lambda: "no"
    try:
        check_and_confirm_api_count(add_count=1, max_count=2, date_str=test_date)
    except SystemExit:
        print("[テスト] 正常にexit(0)で終了しました")
    finally:
        builtins.input = input_backup
    print("[テスト] 上限超過時の挙動テスト: OK")

if __name__ == "__main__":
    print(f"本日のAPI使用回数: {read_api_count()}")
    check_and_confirm_api_count()
    print(f"加算後のAPI使用回数: {read_api_count()}")
    # テスト実行
    test_api_count_reset()
    test_api_count_limit()
