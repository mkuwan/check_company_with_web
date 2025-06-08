#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown出力機能のテスト

目的:
- write_result_markdown関数が正しく動作することを確認
- 出力されるMarkdownファイルの内容を確認
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import write_result_markdown, write_result_json

def test_markdown_output():
    """Markdown出力機能のテスト"""
    print("=== Markdown出力機能テスト ===")
    
    # テスト用の結果データ
    test_result = {
        "company": "株式会社テスト企業",
        "address": "東京都港区テスト1-2-3",
        "tel": "03-1234-5678",
        "other": ["旧社名：テスト商事", "支店：大阪支店"],
        "results": [
            {
                "title": "株式会社テスト企業 - 企業情報",
                "url": "https://example.com/company1",
                "score": 0.95,
                "search_rank": 1,
                "scraped_content_length": 1500,
                "reasoning": "会社名、住所、電話番号が完全に一致",
                "matched_info": "会社名、住所、電話番号"
            },
            {
                "title": "テスト企業グループ概要",
                "url": "https://example.com/company2",
                "score": 0.75,
                "search_rank": 2,
                "scraped_content_length": 800,
                "reasoning": "会社名と住所が一致するが、電話番号が不明",
                "matched_info": "会社名、住所"
            },
            {
                "title": "業界情報 - テスト企業について",
                "url": "https://example.com/industry",
                "score": 0.60,
                "search_rank": 3,
                "scraped_content_length": 600,
                "reasoning": "会社名のみ一致",
                "matched_info": "会社名"
            }
        ],
        "searched_url_count": 3,
        "found": True,
        "early_terminated": True
    }
    
    # テスト用のファイル名
    test_markdown_file = "test_result.md"
    test_json_file = "test_result.json"
    
    try:
        # Markdown出力テスト
        print("Markdown出力中...")
        write_result_markdown(test_result, test_markdown_file)
        print(f"✅ Markdownファイル '{test_markdown_file}' が作成されました")
        
        # JSON出力テスト（比較用）
        print("JSON出力中...")
        write_result_json(test_result, test_json_file)
        print(f"✅ JSONファイル '{test_json_file}' が作成されました")
        
        # ファイル存在確認
        if os.path.exists(test_markdown_file):
            print(f"✅ Markdownファイルが存在します")
            
            # ファイル内容の一部表示
            with open(test_markdown_file, "r", encoding="utf-8") as f:
                content = f.read()
                print(f"✅ ファイルサイズ: {len(content)} 文字")
                print("\n--- Markdownファイル内容の一部 ---")
                lines = content.split('\n')
                for i, line in enumerate(lines[:20]):  # 最初の20行を表示
                    print(f"{i+1:2d}: {line}")
                if len(lines) > 20:
                    print(f"... (残り {len(lines)-20} 行)")
        else:
            print(f"❌ Markdownファイルが見つかりません")
        
        if os.path.exists(test_json_file):
            print(f"✅ JSONファイルが存在します")
            
            # ファイル内容の一部表示
            with open(test_json_file, "r", encoding="utf-8") as f:
                content = f.read()
                print(f"✅ ファイルサイズ: {len(content)} 文字")
        else:
            print(f"❌ JSONファイルが見つかりません")
        
        print("\n✅ Markdown出力機能テスト PASSED")
        
    except Exception as e:
        print(f"❌ Markdown出力機能テスト FAILED: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # テストファイルのクリーンアップ
        for file_path in [test_markdown_file, test_json_file]:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"🗑️ テストファイル '{file_path}' を削除しました")
                except Exception as e:
                    print(f"⚠️ テストファイル '{file_path}' の削除に失敗: {e}")

if __name__ == "__main__":
    test_markdown_output()
