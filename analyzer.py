import requests
import json
import re

def is_relevant_content(title, url, company_name):
    """
    タイトルとURLから企業の実在性検証に関連するコンテンツかどうかを判定
    
    Args:
        title: ページタイトル
        url: ページURL
        company_name: 申請された会社名
    
    Returns:
        bool: 関連性がある場合True
    """
    # 会社名から株式会社などの法人格を除去して核心部分を抽出
    company_core = company_name.replace('株式会社', '').replace('有限会社', '').replace('合同会社', '').replace('(株)', '').replace('（株）', '').strip()
    
    # 除外キーワード（これらが含まれる場合は関連性が低い）
    exclude_keywords = [
        'テスト', 'test', '例', 'example', 
        '記載例', '作成例', 'フォーマット', 'format', 'template', 'テンプレート',
        '消防計画', '防災', '税務', '申告書', '調書', 'PDF', 'pdf',
        'マニュアル', 'manual', 'ガイド', 'guide', '手引き',
        '研修', '講習', 'セミナー', 'seminar', 'training',
        'TSR', 'tsr', 'TSRreport', 'TSRレポート'
    ]
    
    # 実際の会社名に「サンプル」が含まれる場合は、「サンプル」を除外キーワードから除く
    if 'サンプル' not in company_name.lower():
        exclude_keywords.extend(['サンプル', 'sample'])
    
    # ドメイン除外リスト（政府機関、一般的なサービスサイト等）
    exclude_domains = [
        'nta.go.jp',  # 国税庁
        'meti.go.jp',  # 経済産業省
        'tfd.metro.tokyo.lg.jp',  # 東京消防庁
        'koshonin.gr.jp',  # 日本公証人連合会
        'wikipedia.org',  # Wikipedia
        'indeed.com',  # 求人サイト
        'recruit.co.jp',  # リクルート
        'mynavi.jp',  # マイナビ
        'tsr-net.co.jp'  # TSRレポート
    ]
    
    # 除外ドメインチェック
    for domain in exclude_domains:
        if domain in url.lower():
            return False
    
    # 無関係な企業名のチェック（大企業の名前が含まれている場合は除外）
    unrelated_companies = [
        'シティバンク', 'citibank', 'citigroup', 'citi',
        'アイカ工業', 'aica', 
        '田島ルーフィング', 'tajima',
        'トーソー', 'toso'
    ]
    
    # 申請会社名の核心部分が無関係企業リストに含まれていない場合のみチェック
    if company_core.lower() not in [comp.lower() for comp in unrelated_companies]:
        title_lower = title.lower()
        url_lower = url.lower()
        for unrelated in unrelated_companies:
            if unrelated.lower() in title_lower or unrelated.lower() in url_lower:
                return False
    
    # 除外キーワードチェック（タイトル）
    title_lower = title.lower()
    for keyword in exclude_keywords:
        if keyword in title_lower:
            return False
    
    # URLから除外キーワードチェック
    url_lower = url.lower()
    for keyword in ['test', 'example', 'demo', 'pdf']:
        # 実際の会社名に含まれるキーワードは除外しない
        if keyword in url_lower and keyword not in company_name.lower():
            return False
    
    # 会社名の一部が含まれているかチェック
    company_keywords = company_name.replace('株式会社', '').replace('有限会社', '').replace('合同会社', '').strip()
    if company_keywords and company_keywords in title:
        return True
    
    # 企業情報に関連するキーワードがあるかチェック
    relevant_keywords = [
        '会社概要', '企業情報', '会社案内', 'company', 'corporate',
        '所在地', '住所', '連絡先', 'contact', 'address',
        '事業所', '支店', '営業所', 'office', 'branch',
        '代表者', '役員', 'profile', 'about'
    ]
    
    for keyword in relevant_keywords:
        if keyword in title_lower or keyword in url_lower:
            return True
    
    return True  # デフォルトでは関連性ありとする

def ai_generate_query(application_info, ollama_url, ollama_model, max_queries=1):
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
- "{company_name} {address} {tel} {other_info}"
- "{company_name} {address.split()[0] if address else ''} {tel.split()[0] if tel else ''}"
- "{company_name} 企業情報"
- "{company_name} 会社概要"
- "{company_name} 公式サイト"

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
    company_core = company_name.replace('株式会社', '').replace('有限会社', '').replace('合同会社', '').replace('(株)', '').replace('（株）', '').strip()
    
    # クエリリストに分割し、不要な行を除去
    queries = []
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
        sample_words = ["sample", "test", "例", "記載例", "作成例", "テンプレート", "フォーマット"]
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

def pre_filter_search_results(search_results, company_name):
    """
    検索結果を事前フィルタリングして関連性の高いものだけを残す
    
    Args:
        search_results: Google検索結果のリスト
        company_name: 申請された会社名
    
    Returns:
        list: フィルタリング後の検索結果
    """
    filtered_results = []
    
    for result in search_results:
        title = result.get('title', '')
        url = result.get('link', '')
        
        if is_relevant_content(title, url, company_name):
            filtered_results.append(result)
        else:
            # 除外されたURLをログに記録（デバッグ用）
            print(f"[フィルタ除外] {title[:50]}... - {url}")
    
    return filtered_results

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
申請された企業情報と取得したウェブページを比較し、企業の基本情報として適切で同一会社である可能性をスコア化してください。

【申請情報】
会社名: {company_name}
住所: {address}
電話番号: {tel}
その他情報: {other_info}

【取得ページ情報】
タイトル: {title}
URL: {url}
内容: {content}

【重要な判定ルール】
1. コンテンツタイプの評価:
   - 企業概要・会社案内・基本情報: 高評価
   - 採用情報・IR情報・財務情報: 中評価
   - 製品情報・サービス紹介: 中評価
   - プレスリリース・ニュース: 低評価
   - 製品リコール・問題対応・過去の障害情報: 大幅減点
   - サンプル・例・テンプレート: 大幅減点

4. 企業情報の一致度:
   - 会社名完全一致: +0.5 (但しコンテンツタイプが適切な場合のみ)
   - 会社名部分一致: +0.2 (但しコンテンツタイプが適切な場合のみ)
   - 住所完全一致: +0.25
   - 住所部分一致: +0.15
   - 電話番号一致: +0.25

【出力形式】
必ず以下のJSON形式のみで回答してください：
{{
    "score": 0.85,
    "reasoning": "企業概要ページで会社名が完全一致し、住所も部分一致している。企業の基本情報として適切。",
    "matched_info": ["会社名完全一致", "住所部分一致", "企業基本情報"],
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
