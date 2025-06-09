import requests
import os
import time
import logging
from utils import enhanced_check_api_limit, record_api_call, update_api_usage
from config import load_config

def google_search(query, api_key, cse_id, num=8, config=None):
    """
    Google Custom Search APIで検索し、結果URLリストを返す
    強化されたAPI使用件数管理とレート制限を実装
    """
    if config is None:
        config = load_config()
    
    # 強化されたAPI制限チェック
    can_execute, error_msg, wait_time = enhanced_check_api_limit(required_calls=1, config=config)
    
    if not can_execute:
        raise ValueError(f"Google Search API制限エラー: {error_msg}")
    
    # 待機が必要な場合
    if wait_time > 0:
        auto_pause = config.get("GOOGLE_API_AUTO_PAUSE", "true").lower() == "true"
        if auto_pause:
            logging.info(f"レート制限により{wait_time:.1f}秒待機します...")
            time.sleep(wait_time)
        else:
            logging.warning(f"レート制限検出: {wait_time:.1f}秒の待機が推奨されます")
    
    # API呼び出し記録（レート制限用）
    record_api_call(config)
    
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cse_id,
        "q": query,
        "num": num
    }
    
    try:
        logging.info(f"Google検索実行: クエリ='{query}', 最大件数={num}")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        # API使用件数を更新
        update_api_usage(1)
        
        data = response.json()
        results = []
        for item in data.get("items", []):
            results.append({
                "title": item.get("title"),
                "link": item.get("link"),
                "snippet": item.get("snippet")
            })
        
        logging.info(f"Google検索完了: {len(results)}件の結果を取得")
        return results
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Google検索でエラーが発生: {e}")
        raise

if __name__ == "__main__":
    # テスト用
    api_key = os.getenv("GOOGLE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")
    query = "株式会社サンプル 東京都千代田区"
    print(google_search(query, api_key, cse_id))
