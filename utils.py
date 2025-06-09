import json
import signal
import threading
from functools import wraps
from typing import Any, Callable
import os
from datetime import datetime
import logging
import time

class TimeoutException(Exception):
    """タイムアウト例外"""
    pass

def timeout_decorator(timeout_seconds: int):
    """
    関数にタイムアウトを設定するデコレータ
    :param timeout_seconds: タイムアウト時間（秒）
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = [TimeoutException("タイムアウトが発生しました")]
            
            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    result[0] = e
            
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(timeout_seconds)
            
            if thread.is_alive():
                raise TimeoutException(f"処理がタイムアウトしました ({timeout_seconds}秒)")
            
            if isinstance(result[0], Exception):
                raise result[0]
            
            return result[0]
        
        return wrapper
    return decorator

def write_result_json(result: dict, file_path: str = "result.json"):
    """
    判定結果をJSONファイルに出力する
    :param result: 出力するdict
    :param file_path: 出力先ファイル名
    """
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

def write_result_markdown(result: dict, file_path: str = "result.md"):
    """
    判定結果をMarkdownファイルに出力する
    :param result: 出力するdict
    :param file_path: 出力先ファイル名
    """
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("# 企業情報チェック結果\n\n")
        
        # 基本情報
        f.write("## 申請情報\n\n")
        f.write(f"- **会社名**: {result.get('company', 'N/A')}\n")
        f.write(f"- **住所**: {result.get('address', 'N/A')}\n")
        f.write(f"- **電話番号**: {result.get('tel', 'N/A')}\n")
        f.write(f"- **その他情報**: {', '.join(result.get('other', []))}\n\n")
        
        # 判定結果
        f.write("## 判定結果\n\n")
        f.write(f"- **マッチング結果**: {'✅ 一致' if result.get('found', False) else '❌ 不一致'}\n")
        f.write(f"- **検索URL数**: {result.get('searched_url_count', 0)}\n")
        f.write(f"- **早期終了**: {'はい' if result.get('early_terminated', False) else 'いいえ'}\n\n")
        
        # 詳細結果
        f.write("## 詳細結果\n\n")
        results = result.get('results', [])
        if results:
            for i, res in enumerate(results, 1):
                f.write(f"### {i}. {res.get('title', 'タイトル不明')}\n\n")
                f.write(f"- **URL**: {res.get('url', 'N/A')}\n")
                f.write(f"- **スコア**: {res.get('score', 0.0):.3f}\n")
                f.write(f"- **検索順位**: {res.get('search_rank', 'N/A')}\n")
                f.write(f"- **コンテンツ長**: {res.get('scraped_content_length', 0)} 文字\n")
                f.write(f"- **理由**: {res.get('reasoning', 'N/A')}\n")
                f.write(f"- **マッチした情報**: {res.get('matched_info', 'N/A')}\n\n")
        else:
            f.write("結果がありません。\n\n")
        
        f.write("---\n")
        f.write("*この結果は自動生成されました*\n")

def get_api_usage_file_path():
    """
    API使用件数ファイルのパスを取得
    :return: 日付付きのAPI使用件数ファイルパス
    """
    today = datetime.now().strftime("%Y%m%d")
    return f"search_api_count_{today}.txt"

def get_current_api_usage():
    """
    当日のAPI使用件数を取得
    :return: 使用件数（int）
    """
    file_path = get_api_usage_file_path()
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                count = int(f.read().strip())
                return count
        except (ValueError, IOError) as e:
            logging.warning(f"API使用件数ファイルの読み込みに失敗: {e}")
            return 0
    return 0

def update_api_usage(count: int):
    """
    API使用件数を更新
    :param count: 追加する使用件数
    """
    current_count = get_current_api_usage()
    new_count = current_count + count
    
    file_path = get_api_usage_file_path()
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(str(new_count))
        logging.info(f"API使用件数を更新: {current_count} → {new_count}")
    except IOError as e:
        logging.error(f"API使用件数ファイルの書き込みに失敗: {e}")

def check_api_limit(required_calls: int = 1, daily_limit: int = 100):
    """
    API使用制限をチェック
    :param required_calls: 必要な呼び出し回数
    :param daily_limit: 1日の制限件数
    :return: True: 実行可能, False: 制限超過
    """
    current_usage = get_current_api_usage()
    if current_usage + required_calls > daily_limit:
        logging.error(f"API使用制限を超過します。現在の使用件数: {current_usage}, 必要件数: {required_calls}, 制限: {daily_limit}")
        return False
    return True

def setup_logger(log_level: str = "INFO", log_file: str = "app.log"):
    """
    ログ設定を初期化
    :param log_level: ログレベル
    :param log_file: ログファイル名
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # ログの重複を防ぐため、既存のハンドラーをクリア
    logging.getLogger().handlers.clear()
    
    # フォーマット設定
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # ファイルハンドラー
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # ルートロガー設定
    logger = logging.getLogger()
    logger.setLevel(level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_api_rate_limit_file_path():
    """
    APIレート制限記録ファイルのパスを取得
    :return: レート制限記録ファイルパス
    """
    return "google_api_rate_limit.json"

def get_rate_limit_data():
    """
    APIレート制限データを取得
    :return: レート制限データ（dict）
    """
    file_path = get_api_rate_limit_file_path()
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (ValueError, IOError) as e:
            logging.warning(f"レート制限ファイルの読み込みに失敗: {e}")
    
    # デフォルトデータ
    return {
        "last_call_time": 0,
        "calls_this_minute": 0,
        "minute_start": 0,
        "calls_this_second": 0,
        "second_start": 0
    }

def update_rate_limit_data(data):
    """
    APIレート制限データを更新
    :param data: レート制限データ
    """
    file_path = get_api_rate_limit_file_path()
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        logging.error(f"レート制限ファイルの書き込みに失敗: {e}")

def check_rate_limits(config):
    """
    APIレート制限をチェック（分/秒単位）
    :param config: 設定情報
    :return: (可能かどうか, 待機時間)
    """
    rate_limit_per_minute = int(config.get("GOOGLE_API_RATE_LIMIT_PER_MINUTE", 60))
    rate_limit_per_second = int(config.get("GOOGLE_API_RATE_LIMIT_PER_SECOND", 10))
    
    data = get_rate_limit_data()
    current_time = time.time()
    current_minute = int(current_time // 60)
    current_second = int(current_time)
    
    # 分単位のリセット
    if current_minute != data.get("minute_start", 0):
        data["calls_this_minute"] = 0
        data["minute_start"] = current_minute
    
    # 秒単位のリセット
    if current_second != data.get("second_start", 0):
        data["calls_this_second"] = 0
        data["second_start"] = current_second
    
    # レート制限チェック
    if data["calls_this_minute"] >= rate_limit_per_minute:
        wait_time = 60 - (current_time % 60)
        return False, wait_time
    
    if data["calls_this_second"] >= rate_limit_per_second:
        wait_time = 1 - (current_time % 1)
        return False, wait_time
    
    return True, 0

def record_api_call(config):
    """
    API呼び出しを記録
    :param config: 設定情報
    """
    data = get_rate_limit_data()
    current_time = time.time()
    
    data["last_call_time"] = current_time
    data["calls_this_minute"] += 1
    data["calls_this_second"] += 1
    
    update_rate_limit_data(data)

def check_api_usage_warning(current_usage, daily_limit, config):
    """
    API使用量の警告レベルをチェック
    :param current_usage: 現在の使用量
    :param daily_limit: 1日の制限
    :param config: 設定情報
    :return: 警告レベル (0: 正常, 1: 警告, 2: 危険)
    """
    warning_threshold = int(config.get("GOOGLE_API_WARNING_THRESHOLD", 80))
    
    usage_percentage = (current_usage / daily_limit) * 100
    
    if usage_percentage >= 95:
        return 2  # 危険レベル
    elif usage_percentage >= warning_threshold:
        return 1  # 警告レベル
    else:
        return 0  # 正常

def enhanced_check_api_limit(required_calls: int = 1, config=None):
    """
    強化されたAPI制限チェック
    :param required_calls: 必要な呼び出し回数
    :param config: 設定情報
    :return: (実行可能, エラーメッセージ, 待機時間)
    """
    if config is None:
        from config import load_config
        config = load_config()
    
    daily_limit = int(config.get("GOOGLE_API_DAILY_LIMIT", 100))
    strict_mode = config.get("GOOGLE_API_STRICT_MODE", "false").lower() == "true"
    
    # 日次制限チェック
    current_usage = get_current_api_usage()
    if current_usage + required_calls > daily_limit:
        error_msg = f"API使用制限を超過します。現在の使用件数: {current_usage}, 必要件数: {required_calls}, 制限: {daily_limit}"
        logging.error(error_msg)
        return False, error_msg, 0
    
    # 警告レベルチェック
    warning_level = check_api_usage_warning(current_usage, daily_limit, config)
    if warning_level == 2:
        logging.warning(f"API使用量が危険レベルに達しています: {current_usage}/{daily_limit}")
    elif warning_level == 1:
        logging.warning(f"API使用量が警告レベルに達しています: {current_usage}/{daily_limit}")
    
    # レート制限チェック
    can_call, wait_time = check_rate_limits(config)
    if not can_call:
        if strict_mode:
            error_msg = f"レート制限により実行できません。{wait_time:.1f}秒後に再試行してください。"
            return False, error_msg, wait_time
        else:
            logging.warning(f"レート制限検出。{wait_time:.1f}秒待機します。")
            return True, "", wait_time
    
    return True, "", 0
