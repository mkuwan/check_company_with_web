"""
ログ設定とロガーユーティリティ

主な機能:
- 構造化ログ出力（JSON形式）
- ファイルとコンソールへのデュアル出力
- ログレベル別の色分け（コンソール）
- ログローテーション（日次、サイズ制限）
- ログフォーマットの統一

--- サービス層での利用例 ---
from src.utils.logger import LoggerManager, get_env_log_dir, get_env_log_level
log_dir = get_env_log_dir()
log_level = get_env_log_level()
logger = LoggerManager.get_logger("service_name", log_dir, log_level)
logger.info("AI応答取得", {"input_company": "サンプル株式会社", "score": 88.8})
logger.error("AI応答失敗", exc_info=True)

.env例:
LOG_FILE_PATH=logs/app.log
LOG_LEVEL=INFO

サンプルログ出力（app.log, JSON形式）:
{
  "timestamp": "2025-06-06T10:00:00",
  "level": "INFO",
  "logger": "company_verification",
  "message": "AI応答取得",
  "module": "ai_service",
  "function": "analyze_content_match",
  "line": 42,
  "extra": {"input_company": "サンプル株式会社", "score": 88.8}
}

.env未設定時は logs/app.log, INFOレベルがデフォルト
logs/ ディレクトリは自動作成されます

主要サービス層では try-except 内で error ログを必ず出力してください

詳細は設計.md「6.3 ログ設計・運用方針」参照
"""

import logging
import logging.handlers
import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import colorama
from colorama import Fore, Back, Style

# カラー初期化
colorama.init()

class ColoredFormatter(logging.Formatter):
    """コンソール用の色付きフォーマッタ"""
    
    # ログレベル別の色設定
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Back.WHITE + Style.BRIGHT,
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{log_color}{record.levelname}{Style.RESET_ALL}"
        # extra_dataがあればmessage末尾に[extra: ...]を追加
        msg = super().format(record)
        if hasattr(record, 'extra_data') and record.extra_data is not None:
            msg += f" [extra: {record.extra_data}]"
        return msg

class JsonFormatter(logging.Formatter):
    """JSON形式のフォーマッタ（ファイル出力用）"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # 例外情報があれば追加
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # カスタム属性があれば追加
        if hasattr(record, 'extra_data'):
            log_entry['extra'] = record.extra_data
            
        return json.dumps(log_entry, ensure_ascii=False)

class Logger:
    """ログ管理クラス"""
    
    def __init__(self, name: str, log_file_path: str = None, level: str = "INFO"):
        """
        ロガーを初期化
        
        Args:
            name: ロガー名
            log_file_path: ログファイルのパス（ファイル名まで）
            level: ログレベル（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        """
        self.name = name
        self.level = getattr(logging, level.upper())
        if log_file_path is None:
            log_file_path = f"logs/{name}.log"
        log_file_path = str(log_file_path)
        if os.path.isdir(log_file_path):
            log_file_path = os.path.join(log_file_path, "app.log")
        self.log_file_path = Path(log_file_path)
        self.log_dir = self.log_file_path.parent
        
        # ログディレクトリを作成
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # ロガーを設定
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.level)
        
        # 既存のハンドラをクリア（重複回避）
        self.logger.handlers.clear()
        
        # ハンドラを追加
        self._setup_handlers()
    
    def _setup_handlers(self):
        """ログハンドラを設定"""
        
        # 1. ファイルハンドラ（JSON形式、日次ローテーション）
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=str(self.log_file_path),
            when='midnight',
            interval=1,
            backupCount=30,  # 30日分保持
            encoding='utf-8'
        )
        file_handler.setLevel(self.level)
        file_handler.setFormatter(JsonFormatter())
        self.logger.addHandler(file_handler)
        
        # 2. エラーファイルハンドラ（エラー以上のみ）
        error_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_dir / f"{self.name}_error.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(JsonFormatter())
        self.logger.addHandler(error_handler)
        
        # 3. コンソールハンドラ（色付き）
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.level)
        console_handler.setFormatter(ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(console_handler)
    
    def debug(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """デバッグログ"""
        self._log(logging.DEBUG, message, extra_data)
    
    def info(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """情報ログ"""
        self._log(logging.INFO, message, extra_data)
    
    def warning(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """警告ログ"""
        self._log(logging.WARNING, message, extra_data)
    
    def error(self, message: str, extra_data: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """エラーログ"""
        self._log(logging.ERROR, message, extra_data, exc_info)
    
    def critical(self, message: str, extra_data: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """クリティカルログ"""
        self._log(logging.CRITICAL, message, extra_data, exc_info)
    
    def _log(self, level: int, message: str, extra_data: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """内部ログ出力メソッド"""
        if extra_data:
            # カスタムLogRecordを作成してextra_dataを追加
            record = self.logger.makeRecord(
                self.logger.name, level, "", 0, message, (), None
            )
            record.extra_data = extra_data
            self.logger.handle(record)
        else:
            self.logger.log(level, message, exc_info=exc_info)

class LoggerManager:
    """ログ管理マネージャー"""
    
    _loggers: Dict[str, Logger] = {}
    
    @classmethod
    def get_logger(cls, name: str, log_file_path: str = None, level: str = "INFO") -> Logger:
        """
        ロガーを取得（シングルトンパターン）
        
        Args:
            name: ロガー名
            log_file_path: ログファイルのパス（ファイル名まで）
            level: ログレベル
            
        Returns:
            Logger: ロガーインスタンス
        """
        key = f"{name}:{log_file_path or ''}"
        if key not in cls._loggers:
            cls._loggers[key] = Logger(name, log_file_path, level)
        # StreamHandler追加処理はLogger側で一元管理するため、ここでは何もしない
        return cls._loggers[key]
    
    @classmethod
    def set_level(cls, level: str):
        """全ロガーのレベルを変更"""
        log_level = getattr(logging, level.upper())
        for logger in cls._loggers.values():
            logger.logger.setLevel(log_level)
            for handler in logger.logger.handlers:
                handler.setLevel(log_level)

def get_env_log_dir():
    """.envのLOG_FILE_PATHからディレクトリ部分を取得（なければlogs/）"""
    log_file = os.getenv("LOG_FILE_PATH", "logs/app.log")
    return Path(os.path.dirname(log_file) or "logs")

def get_env_log_level():
    return os.getenv("LOG_LEVEL", "INFO")

def get_env_log_file_path():
    """LOG_FILE_PATH（ファイル名まで）を取得。なければlogs/main.log"""
    return os.getenv("LOG_FILE_PATH", "logs/main.log")



# テスト関数
def test_logger():
    """ロガーのテスト関数"""
    print("=== Logger Test ===")
    
    # テスト用ログディレクトリ
    test_log_dir = Path("logs")
    test_log_dir.mkdir(exist_ok=True)
    
    # ロガーを作成
    logger = Logger("test_logger", test_log_dir, "DEBUG")
    
    # 各レベルのログをテスト
    logger.debug("これはデバッグメッセージです")
    logger.info("これは情報メッセージです")
    logger.warning("これは警告メッセージです")
    logger.error("これはエラーメッセージです")
    
    # extra_dataのテスト
    logger.info("ユーザーログイン", {
        "user_id": "test_user",
        "ip_address": "192.168.1.1",
        "timestamp": datetime.now().isoformat()
    })
    
    # 例外ログのテスト
    try:
        1 / 0
    except Exception:
        logger.error("ゼロ除算エラーが発生しました", exc_info=True)
    
    print(f"ログファイルが作成されました: {test_log_dir}")
    
    # ログマネージャーのテスト
    logger2 = LoggerManager.get_logger("test_logger2", test_log_dir)
    logger2.info("別のロガーからのメッセージ")
    
    print("ログテスト完了")

if __name__ == "__main__":
    test_logger()

# サービス層での利用例:
# from src.utils.logger import LoggerManager, get_env_log_dir, get_env_log_level
# LoggerManager.get_logger() を推奨
# log_dir = get_env_log_dir()
# log_level = get_env_log_level()
# logger = LoggerManager.get_logger("service_name", log_dir, log_level)
# logger.info("AI応答取得", {"input_company": "サンプル株式会社", "score": 88.8})
# logger.error("AI応答失敗", exc_info=True)
