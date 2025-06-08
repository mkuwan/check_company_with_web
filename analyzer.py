import requests
import json

def ai_generate_query(application_info, ollama_url, ollama_model, max_queries=1):
    """
    申請情報（リストやdict）をもとにAI（ollama）でGoogle検索クエリを最大max_queries件生成する
    各クエリは括弧や記号・説明文・番号・前置きを含めず、キーワードのみ
    戻り値: クエリのリスト
    """
    import json
    prompt = f"""
以下の会社情報から、Google検索で最も有効な検索クエリを日本語で最大{max_queries}件、1行につき1クエリずつ出力してください。
【重要】各検索クエリには括弧や記号（「」『』""\"' など）、説明文、番号、前置き（例: '1.', '2.', '以下の', '検索クエリが考えられます' など）は一切含めず、Google検索に最適なキーワードのみを出力してください。
例：
株式会社サンプル
東京都千代田区1-1-1
東京支店
会社情報: {json.dumps(application_info, ensure_ascii=False)}
出力はクエリ文字列のみ。各クエリは改行で区切ってください。
"""
    payload = {
        "model": ollama_model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }
    response = requests.post(ollama_url, json=payload, timeout=60, stream=True)
    content = ""
    for line in response.iter_lines():
        if not line:
            continue
        try:
            obj = json.loads(line.decode('utf-8'))
            if "message" in obj and "content" in obj["message"]:
                content += obj["message"]["content"]
            elif "response" in obj:
                content += obj["response"]
        except Exception:
            continue
    # クエリリストに分割し、空行・重複・空白・説明文・番号付き行を除去
    queries = [q.strip() for q in content.strip().split("\n") if q.strip() and not any(x in q for x in ["以下の", "検索クエリ", "考えられます", ".", "．", "1.", "2.", "3.", "1．", "2．", "3．"])]
    # 最大max_queries件に制限
    return queries[:max_queries]

def ai_analyze_content(application_info, scraped_content, ollama_url, ollama_model):
    """
    申請情報とスクレイピング内容をAIで解析し、一致度をスコア化する
    
    Args:
        application_info: 申請情報リスト [会社名, 住所, 電話番号, その他...]
        scraped_content: スクレイピング結果辞書 {"title": "", "url": "", "content": "", "links": []}
        ollama_url: OllamaのAPIエンドポイント
        ollama_model: 使用するAIモデル名
    
    Returns:
        dict: {
            "score": float,  # 0.0-1.0の一致度スコア
            "reasoning": str,  # 判定理由
            "matched_info": list,  # 一致した情報の詳細
            "confidence": float  # 信頼度
        }
    """
    company_name = application_info[0] if len(application_info) > 0 else ""
    address = application_info[1] if len(application_info) > 1 else ""
    tel = application_info[2] if len(application_info) > 2 else ""
    other_info = application_info[3:] if len(application_info) > 3 else []
    
    # スクレイピング内容を要約（長すぎる場合はトランケート）
    content = scraped_content.get("content", "")[:3000]  # 最大3000文字
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
        "model": ollama_model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }
    
    try:
        response = requests.post(ollama_url, json=payload, timeout=120)
        response.raise_for_status()
        
        # stream=Falseの場合、レスポンスは単一のJSONオブジェクト
        response_data = response.json()
        content = response_data.get("message", {}).get("content", "")
        
        # JSONレスポンスをパース
        result = json.loads(content.strip())
        
        # スコアを0.0-1.0の範囲に制限
        result["score"] = max(0.0, min(1.0, float(result.get("score", 0.0))))
        result["confidence"] = max(0.0, min(1.0, float(result.get("confidence", 0.0))))
        
        return result
        
    except json.JSONDecodeError as e:
        # JSONパースエラーの場合はデフォルト値を返す
        return {
            "score": 0.0,
            "reasoning": f"AI解析エラー: JSON解析失敗 ({str(e)})",
            "matched_info": [],
            "confidence": 0.0
        }
    except Exception as e:
        return {
            "score": 0.0,
            "reasoning": f"AI解析エラー: {str(e)}",
            "matched_info": [],
            "confidence": 0.0
        }

if __name__ == "__main__":
    # テスト用
    application_info = [
        "株式会社サンプル",
        "東京都千代田区1-1-1",
        "03-1234-5678",
        "東京支店",
        "旧サンプル株式会社"
    ]
    ollama_url = "http://localhost:11434/api/chat"
    ollama_model = "llama3.1:latest"
    print(ai_generate_query(application_info, ollama_url, ollama_model, max_queries=3))
