#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI解析機能のデバッグテスト
"""

import requests
import json
from config import load_config

def debug_ollama_response():
    """Ollamaの生のレスポンスをデバッグ"""
    print("=== Ollama AI解析レスポンス デバッグ ===")
    
    config = load_config()
    
    # テスト用申請情報
    application_info = ["株式会社壱番屋", "愛知県一宮市", "0586-76-1550", "CoCo壱番屋"]
    
    # テスト用スクレイピング結果
    scraped_content = {
        "title": "カレーハウスCoCo壱番屋",
        "url": "https://www.ichibanya.co.jp/",
        "content": "カレーハウスCoCo壱番屋 株式会社壱番屋 愛知県一宮市千秋町 CoCo壱番屋",
        "links": []
    }
    
    company_name = application_info[0]
    address = application_info[1]
    tel = application_info[2]
    other_info = application_info[3:]
    
    content = scraped_content.get("content", "")[:1000]
    title = scraped_content.get("title", "")
    url = scraped_content.get("url", "")
    
    prompt = f"""
以下の申請情報と取得したウェブページ内容を比較し、同一会社である可能性をスコア化してください。

【申請情報】
会社名: {company_name}
住所: {address}
電話番号: {tel}
その他情報: {other_info}

【取得ページ情報】
タイトル: {title}
URL: {url}
内容: {content}

【判定基準】
- 会社名の完全一致: +0.4
- 会社名の部分一致: +0.2  
- 住所の完全一致: +0.3
- 住所の部分一致: +0.15
- 電話番号の一致: +0.3
- その他情報の一致: +0.1～0.2

【出力形式】
必ず以下のJSON形式のみで回答してください：
{{
    "score": 0.85,
    "reasoning": "会社名'○○'が完全一致し、住所'××'も部分一致している。電話番号は確認できないが、総合的に同一会社の可能性が高い。",
    "matched_info": ["会社名完全一致", "住所部分一致"],
    "confidence": 0.9
}}

重要: JSON以外の文字は一切出力しないでください。
"""

    payload = {
        "model": config["OLLAMA_MODEL"],
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }
    
    print(f"Ollamaエンドポイント: {config['OLLAMA_API_URL']}")
    print(f"使用モデル: {config['OLLAMA_MODEL']}")
    print(f"プロンプト長: {len(prompt)}文字")
    
    try:
        print("\nOllamaにリクエスト送信中...")
        response = requests.post(config["OLLAMA_API_URL"], json=payload, timeout=30)
        print(f"HTTPステータス: {response.status_code}")
        print(f"レスポンスヘッダー: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("\n=== 生レスポンス ===")
            response_text = response.text
            print(f"レスポンステキスト: '{response_text}'")
            print(f"レスポンス長: {len(response_text)}文字")
            
            # ストリーミングモードでの処理を再現
            content = ""
            for line in response.iter_lines():
                if not line:
                    continue
                print(f"行データ: {line}")
                try:
                    line_data = json.loads(line.decode('utf-8'))
                    print(f"JSONパース結果: {line_data}")
                    if line_data.get("done", False):
                        print("処理完了フラグ検出")
                        break
                    content += line_data.get("message", {}).get("content", "")
                except json.JSONDecodeError as e:
                    print(f"行のJSONパースエラー: {e}")
                    print(f"問題のある行: {line}")
            
            print(f"\n=== 抽出されたコンテンツ ===")
            print(f"コンテンツ: '{content}'")
            print(f"コンテンツ長: {len(content)}文字")
            
            if content.strip():
                print("\n=== JSON解析テスト ===")
                try:
                    result = json.loads(content.strip())
                    print(f"JSON解析成功: {result}")
                except json.JSONDecodeError as e:
                    print(f"JSON解析失敗: {e}")
                    print(f"解析対象テキスト: '{content.strip()}'")
            else:
                print("抽出されたコンテンツが空です")
        else:
            print(f"HTTPエラー: {response.status_code}")
            print(f"エラー内容: {response.text}")
            
    except Exception as e:
        print(f"リクエストエラー: {e}")
    
    print("\n=== デバッグ終了 ===")

if __name__ == "__main__":
    debug_ollama_response()
