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

class EarlyTerminationException(Exception):
    """早期終了例外"""
    pass

# グローバル早期終了フラグ
_early_termination_flag = threading.Event()

def set_early_termination():
    """早期終了フラグを設定"""
    _early_termination_flag.set()

def reset_early_termination():
    """早期終了フラグをリセット"""
    _early_termination_flag.clear()

def check_early_termination():
    """早期終了フラグをチェック"""
    return _early_termination_flag.is_set()

def timeout_decorator(timeout_seconds: int):
    """
    関数にタイムアウトを設定するデコレータ（早期終了対応版）
    :param timeout_seconds: タイムアウト時間（秒）
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 早期終了フラグのチェック
            if check_early_termination():
                raise EarlyTerminationException("早期終了フラグが設定されています")
            
            result = [TimeoutException("タイムアウトが発生しました")]
            stop_flag = threading.Event()
            
            def target():
                try:
                    result[0] = func(*args, **kwargs, _stop_flag=stop_flag)
                except Exception as e:
                    result[0] = e
            
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            
            # タイムアウト待機（100ms間隔で早期終了フラグもチェック）
            start_time = time.time()
            while thread.is_alive():
                if time.time() - start_time >= timeout_seconds:
                    stop_flag.set()  # 停止フラグを設定
                    thread.join(timeout=1.0)  # 1秒待機してスレッド終了を試行
                    raise TimeoutException(f"処理がタイムアウトしました ({timeout_seconds}秒)")
                
                if check_early_termination():
                    stop_flag.set()  # 停止フラグを設定
                    thread.join(timeout=1.0)  # 1秒待機してスレッド終了を試行
                    raise EarlyTerminationException("早期終了フラグが設定されました")
                
                time.sleep(0.1)  # 100ms間隔でチェック
            
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

def standardize_output_format(raw_result: dict) -> dict:
    """
    生の結果データを設計書で定義された標準フォーマットに変換
    :param raw_result: 生の結果データ
    :return: 標準化された結果データ
    """
    standardized = {
        "company": raw_result.get("company", "N/A"),
        "address": raw_result.get("address", "N/A"), 
        "tel": raw_result.get("tel", "N/A"),
        "results": [],
        "searched_url_count": raw_result.get("searched_url_count", 0),
        "found": raw_result.get("found", False),
        "early_terminated": raw_result.get("early_terminated", False)
    }
    
    # otherフィールドがある場合は追加
    if "other" in raw_result and raw_result["other"]:
        standardized["other"] = raw_result["other"]
    
    # URLが見つからなかった場合のメッセージ
    if not standardized["found"]:
        standardized["message"] = "申請情報に基づくURLが見つかりませんでした"
    
    # 結果をスコア順にソートして最大10件に制限
    raw_results = raw_result.get("results", [])
    sorted_results = sorted(raw_results, key=lambda x: x.get("score", 0), reverse=True)
    
    for result in sorted_results[:10]:  # 最大10件
        standardized_result = {
            "url": result.get("url", "N/A"),
            "score": result.get("score", 0.0),
            "is_real": result.get("score", 0.0) >= 0.7,  # スコア0.7以上をrealとする
            "reason": result.get("reasoning", result.get("reason", "判定理由不明"))
        }
        standardized["results"].append(standardized_result)
    
    return standardized

def write_result_markdown_table(result: dict, file_path: str = "result.md"):
    """
    判定結果を設計書で定義されたテーブル形式のMarkdownファイルに出力する
    :param result: 標準化された結果dict
    :param file_path: 出力先ファイル名
    """
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("# 判定結果\n\n")
        
        # 基本情報
        f.write(f"- 会社名: {result.get('company', 'N/A')}\n")
        f.write(f"- 住所: {result.get('address', 'N/A')}\n")
        f.write(f"- 電話番号: {result.get('tel', 'N/A')}\n")
        f.write(f"- 検索URL数: {result.get('searched_url_count', 0)}\n")
        
        # 見つかったかどうか
        found_icon = "✅" if result.get('found', False) else "❌"
        f.write(f"- 見つかった: {found_icon}\n\n")
        
        # その他情報がある場合
        if "other" in result and result["other"]:
            f.write(f"- その他情報: {', '.join(result['other'])}\n\n")
        
        # 早期終了の情報
        if result.get('early_terminated', False):
            f.write("- **注記**: スコア95%以上の結果が見つかりました\n\n")
        
        # URLが見つからなかった場合のメッセージ
        if not result.get('found', False):
            f.write(f"## メッセージ\n\n{result.get('message', 'URLが見つかりませんでした')}\n\n")
        
        # 結果テーブル
        results = result.get('results', [])
        if results:
            f.write("## 上位10件（スコア順）\n\n")
            f.write("| スコア | URL | 判定理由 |\n")
            f.write("|-------|-----|----------|\n")
            
            for res in results:
                score = res.get('score', 0.0)
                url = res.get('url', 'N/A')
                reason = res.get('reason', '判定理由不明')
                
                # URLが長い場合は短縮表示
                if len(url) > 50:
                    display_url = url[:47] + "..."
                else:
                    display_url = url
                
                # 理由が長い場合は短縮表示
                if len(reason) > 200:
                    display_reason = reason[:200] + "..."
                else:
                    display_reason = reason
                
                f.write(f"| {score:.2f} | {display_url} | {display_reason} |\n")
            
            f.write("\n")
        
        f.write("---\n")
        f.write("*この結果は自動生成されました*\n")

# 既存のwrite_result_markdown関数を新しい関数で置き換え
def write_result_markdown(result: dict, file_path: str = "result.md"):
    """
    判定結果をMarkdownファイルに出力する（標準化済みデータを期待）
    :param result: 出力するdict（標準化済み）
    :param file_path: 出力先ファイル名
    """
    # 標準化されていない場合は標準化を実行
    if "is_real" not in str(result) and "results" in result and result["results"]:
        # 生データの場合は標準化
        result = standardize_output_format(result)
    
    write_result_markdown_table(result, file_path)

def get_api_usage_file_path():
    """
    API使用件数ファイルのパスを取得
    :return: 日付付きのAPI使用件数ファイルパス
    """
    today = datetime.now().strftime("%Y%m%d")
    api_log_dir = "api_log"
    
    # api_logディレクトリが存在しない場合は作成
    if not os.path.exists(api_log_dir):
        os.makedirs(api_log_dir)
    
    return os.path.join(api_log_dir, f"search_api_count_{today}.txt")

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
    API呼び出しを記録（レート制限データ + 日別使用件数）
    :param config: 設定情報
    """
    # レート制限データの更新
    data = get_rate_limit_data()
    current_time = time.time()
    
    data["last_call_time"] = current_time
    data["calls_this_minute"] += 1
    data["calls_this_second"] += 1
    
    update_rate_limit_data(data)
    
    # 日別API使用件数の更新
    update_api_usage(1)

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

def reset_api_limits():
    """
    API制限データをリセットする（テスト用・開発用）
    """
    logger = logging.getLogger()
    
    try:
        # レート制限ファイルをリセット
        rate_limit_file = get_api_rate_limit_file_path()
        default_rate_data = {
            "last_call_time": 0,
            "calls_this_minute": 0,
            "minute_start": 0,
            "calls_this_second": 0,
            "second_start": 0
        }
        
        with open(rate_limit_file, "w", encoding="utf-8") as f:
            json.dump(default_rate_data, f, indent=2)
        
        logger.info(f"レート制限データをリセット: {rate_limit_file}")
        
        # 日別API使用件数ファイルをリセット
        today = datetime.now().strftime("%Y%m%d")
        api_log_dir = "api_log"
        
        # api_logディレクトリが存在しない場合は作成
        if not os.path.exists(api_log_dir):
            os.makedirs(api_log_dir)
        
        api_count_file = os.path.join(api_log_dir, f"search_api_count_{today}.txt")
        
        with open(api_count_file, "w", encoding="utf-8") as f:
            f.write("0")
        
        logger.info(f"API使用件数をリセット: {api_count_file}")
        print("✅ API制限データをリセットしました")
        
    except Exception as e:
        logger.error(f"API制限リセット失敗: {e}")
        print(f"❌ API制限リセット失敗: {e}")
