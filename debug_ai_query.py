#!/usr/bin/env python3
"""
AI検索クエリ生成のデバッグスクリプト
"""

import os
from dotenv import load_dotenv
from config import load_config
from analyzer import ai_generate_query
import json

def main():
    # 環境変数を明示的にクリア
    import os
    if 'OLLAMA_API_URL' in os.environ:
        del os.environ['OLLAMA_API_URL']
    
    load_dotenv()
    config = load_config()
    
    # テスト用の申請情報
    application_info = ["株式会社サンプル", "東京都千代田区1-1-1", "03-1234-5678"]
    
    ollama_url = config["OLLAMA_API_URL"]
    ollama_model = config["OLLAMA_MODEL"]
    
    print(f"Ollama URL: {ollama_url}")
    print(f"Ollama Model: {ollama_model}")
    print(f"申請情報: {application_info}")
    print("=" * 50)
    
    try:
        # AI検索クエリ生成をテスト
        queries = ai_generate_query(
            application_info=application_info,
            ollama_url=ollama_url,
            ollama_model=ollama_model,
            max_queries=3
        )
        
        print(f"生成された検索クエリ数: {len(queries)}")
        for i, query in enumerate(queries, 1):
            print(f"[{i}] {query}")
            
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
