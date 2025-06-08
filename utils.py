import json
import signal
import threading
from functools import wraps
from typing import Any, Callable

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
