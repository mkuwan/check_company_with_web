import requests
import json
import re


def ai_generate_query(application_info, ollama_url, ollama_model, max_queries=1) -> list:
    """
    申請情報（リストやdict）をもとにAI（ollama）でGoogle検索クエリを最大max_queries件生成する
    企業の実在性検証に特化した検索クエリを生成
    戻り値: クエリのリスト
    """
    import json
    
    # 会社名から不要な文字を除去
    company_name = application_info[0] if len(application_info) > 0 else ""
    address = application_info[1] if len(application_info) > 1 else ""
    tel = application_info[2] if len(application_info) > 2 else ""
    other_info = application_info[3:] if len(application_info) > 3 else []
    prompt = f"""
以下の会社情報から、対象企業の実在性を確認するための効果的なGoogle検索クエリを最大{max_queries}件生成してください。

【会社情報】
会社名: {company_name}
住所: {address}
電話番号: {tel}
その他情報: {other_info}

【検索の目的】
- この特定の企業の公式サイトや企業情報ページを発見
- 会社の実在性・真正性の確認
- 住所・電話番号等の申請情報との一致確認

【重要な指針】
1. 必ず対象会社名を含むクエリを作成（他の企業名は含めない）
2. "サンプル"、"例"、"テスト"、"記載例"などは除外
3. 会社名 住所 電話番号などの組み合わせを優先
4. 政府機関、TSRレポート、消防計画などの無関係サイトが出ないよう注意

【生成すべきクエリの例】
- "{company_name} 概要"
- "{company_name} 沿革"
- "{company_name} 歴史"
- "{company_name} history"
- "{company_name} 公式"

【出力形式】
検索クエリのみを1行ずつ出力してください。説明文、番号、記号、余計な文字は不要です。
"""
    
    payload = {
        "model": ollama_model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
    }
    
    response = requests.post(ollama_url, json=payload, timeout=60)
    response.raise_for_status()
    result = response.json()
    content = result["message"]["content"]
    
    # 会社名から核心部分を抽出（フィルタリング用）
    company_core = company_name.replace('株式会社', ' 株式会社 ').replace('有限会社', ' 有限会社 ').replace('合同会社', ' 合同会社 ')\
        .replace('株式会社', '').replace('有限会社', '').replace('合同会社', '')\
        .replace('（株）', '').replace('（有）', '').replace('（合）', '')\
        .replace('法人', '法人 ')\
        .replace('(株) ', '').replace('(有)', '').strip()
    
    # クエリリストに分割し、不要な行を除去
    queries = []
    queries.append(f"{company_name} {address.split()[0] if address else ''} {tel.split()[0] if tel else ''}")
    queries.append(f"{company_name} {address}")
    queries.append(f"{company_name} {tel}")
    queries.append(f"{company_name} {other_info[0] if other_info else ''}")
    queries.append(f"{company_name}")
    for line in content.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
            
        # 番号や記号を除去
        line = re.sub(r'^[0-9]+[\.\)]\s*', '', line)
        line = re.sub(r'^[・\-\*]\s*', '', line)
        line = re.sub(r'^[\[\]【】]\s*', '', line)
        
        # 説明的な文言を除去
        if any(word in line for word in ["以下の", "検索クエリ", "考えられます", "例：", "【", "】", "出力形式", "「", "」"]):
            continue
            
        # 対象会社名が含まれていないクエリは除外
        if company_core and company_core.lower() not in line.lower():
            continue
            
        # サンプルやテスト関連のクエリを除外（ただし実際の会社名に含まれる場合は例外）
        exclude_sample = False
        sample_words = ["sample", "記載例", "作成例", "テンプレート", "フォーマット"]
        for word in sample_words:
            if word in line.lower() and company_name.lower() not in line.lower():
                exclude_sample = True
                break
        
        if exclude_sample:
            continue
            
        if line and len(line) > 3:  # 最低限の長さ
            queries.append(line)
    
    # 重複除去と最大件数制限
    unique_queries = []
    for q in queries:
        if q not in unique_queries:
            unique_queries.append(q)
    
    return unique_queries[:max_queries]


def ai_analyze_content(application_info, scraped_content, ollama_url, ollama_model, _stop_flag=None):
    """
    申請情報とスクレイピング内容をAIで解析し、一致度をスコア化する
    
    Args:
        application_info: 申請情報リスト [会社名, 住所, 電話番号, その他...]
        scraped_content: スクレイピング結果辞書 {"title": "", "url": "", "content": "", "links": []}
        ollama_url: OllamaのAPIエンドポイント
        ollama_model: 使用するAIモデル名
        _stop_flag: 早期終了フラグ（threading.Event）
    
    Returns:
        dict: {
            "score": float,  # 0.0-1.0の一致度スコア
            "reasoning": str,  # 判定理由
            "matched_info": list,  # 一致した情報の詳細
            "confidence": float  # 信頼度
        }
    """
    # 早期終了フラグのチェック
    from utils import check_early_termination, EarlyTerminationException
    if check_early_termination():
        raise EarlyTerminationException("早期終了フラグが設定されています")
    
    if _stop_flag and _stop_flag.is_set():
        raise EarlyTerminationException("停止フラグが設定されています")
    company_name = application_info[0] if len(application_info) > 0 else ""
    address = application_info[1] if len(application_info) > 1 else ""
    tel = application_info[2] if len(application_info) > 2 else ""
    other_info = application_info[3:] if len(application_info) > 3 else []
      # スクレイピング内容を要約（長すぎる場合はトランケート）
    content = scraped_content.get("content", "")[:3000]  # 最大3000文字
    title = scraped_content.get("title", "")
    url = scraped_content.get("url", "")
    
    prompt = f"""
申請された企業情報と取得したウェブページを比較し、企業の実在性と同一性を厳密に評価してスコア化してください。
判定は必ずステップバイステップで行い、最終的なスコアを0.0から1.0の範囲で出力してください。

【申請情報】
会社名: {company_name}
住所: {address}
電話番号: {tel}
その他情報: {other_info}

【取得ページ情報】
タイトル: {title}
URL: {url}
内容: {content}

【厳密な判定ルール - 必ず以下の基準に従ってください】
【重要】郵便番号の〒や括弧()は無視して判定してください

1. 会社名の判定:
   - 完全一致（〒、括弧、英語表記は無視）: +0.5点
   - 例: "トヨタ自動車株式会社" = "トヨタ自動車株式会社（TOYOTA MOTOR CORPORATION）" → 完全一致
   - 部分一致（略称・旧称等）: +0.2点
   - 不一致または無関係: 0点

2. 住所の判定:
   - 完全一致（〒郵便番号は無視、番地まで一致）: +0.25点
   - 例1: "愛知県豊田市トヨタ町1番地" = "〒471-8571　愛知県豊田市トヨタ町1番地" → 完全一致 0.25点
   - 例2: "東京都千代田区1-1-1" = "〒100-0001 東京都千代田区1-1-1" → 完全一致 0.25点
   - 部分一致（市区町村レベル一致）: +0.15点
   - 例: "愛知県豊田市" のみ一致 → 部分一致 0.15点
   - 都道府県のみ一致: +0.05点
   - 不一致: 0点

3. 電話番号の判定:
   - 完全一致（ハイフンの有無無視）: +0.25点
   - 不一致: 0点

【計算方法】
1. 上記ルールに基づいて各項目の点数を算出
2. 合計点数を計算（上限1.0、下限0.0）
3. 最終スコアを0.0-1.0の範囲で出力

【計算検証】必ず以下の手順で計算してください：
STEP1: 会社名判定 → X点
STEP2: 住所判定 → Y点  
STEP3: 電話番号判定 → Z点
STEP4: 合計 = X + Y + Z
STEP5: 上限1.0で切り捨て

【判定例】
- 会社名完全一致(0.5) + 住所完全一致(0.25) + 電話番号一致(0.25) = 1.0
- 会社名完全一致(0.5) + 住所部分一致(0.15) + 電話番号一致(0.25) = 0.9
- 会社名部分一致(0.2) + 住所部分一致(0.15) + 電話番号不一致(0) = 0.35

【出力形式】
以下のJSON形式で回答してください。計算過程や説明文は一切出力せず、JSONのみを出力してください：

{{
    "score": 計算した正確な一致度スコア（小数点第3位まで）,
    "reasoning": "STEP1:会社名判定=X点, STEP2:住所判定=Y点, STEP3:電話番号判定=Z点",
    "matched_info": ["具体的に一致した項目のリスト"],
    "confidence": 判定の確実性を示す信頼度スコア（0.0-1.0）
}}

【絶対厳守】
- JSON以外の文字（説明、計算過程、コメント等）は一切出力禁止
- JSONの前後に空行や文字を含めない
- 波括弧{{}}で始まり波括弧で終わる形式のみ
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
        # 生の情報をprintする
        print(f"AI応答(raw): {content}")  # 完全な応答を表示
        
        # JSONのみを抽出する処理
        try:
            # 最初の{から最後の}までを抽出
            start_idx = content.find('{')
            end_idx = content.rfind('}')
            if start_idx != -1 and end_idx != -1:
                json_content = content[start_idx:end_idx+1]
                print(f"抽出したJSON: {json_content}")
                result = json.loads(json_content)
            else:
                raise json.JSONDecodeError("JSON形式が見つかりません", content, 0)
        except json.JSONDecodeError:
            # JSONが見つからない場合の処理
            print(f"JSON抽出失敗。元の応答: {content[:200]}...")
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

