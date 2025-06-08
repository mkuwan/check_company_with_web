import requests
import os

def google_search(query, api_key, cse_id, num=8):
    """
    Google Custom Search APIで検索し、結果URLリストを返す
    """
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cse_id,
        "q": query,
        "num": num
    }
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    results = []
    for item in data.get("items", []):
        results.append({
            "title": item.get("title"),
            "link": item.get("link"),
            "snippet": item.get("snippet")
        })
    return results

if __name__ == "__main__":
    # テスト用
    api_key = os.getenv("GOOGLE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")
    query = "株式会社サンプル 東京都千代田区"
    print(google_search(query, api_key, cse_id))
