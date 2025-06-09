#!/usr/bin/env python3
"""
設定読み込みのデバッグスクリプト
"""

import os
from dotenv import load_dotenv

def main():
    print("=== 設定読み込みデバッグ ===")
    
    # 1. 環境変数をクリア
    if 'OLLAMA_API_URL' in os.environ:
        del os.environ['OLLAMA_API_URL']
        print("環境変数 OLLAMA_API_URL をクリアしました")
    
    # 2. .envファイルの内容を直接確認
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines, 1):
                if 'OLLAMA_API_URL' in line:
                    print(f".envファイル {i}行目: {line.strip()}")
    except Exception as e:
        print(f".envファイル読み込みエラー: {e}")
    
    # 3. load_dotenv()を実行
    print("load_dotenv()を実行...")
    load_dotenv()
    
    # 4. 環境変数を確認
    ollama_url = os.getenv('OLLAMA_API_URL')
    print(f"環境変数 OLLAMA_API_URL: {ollama_url}")
    
    # 5. configモジュールを使用
    from config import load_config
    config = load_config()
    print(f"config['OLLAMA_API_URL']: {config.get('OLLAMA_API_URL')}")

if __name__ == "__main__":
    main()
