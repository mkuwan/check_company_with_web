#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
スクレイピング機能の単体テスト
"""

from scraper import scrape_page

def test_scraping():
    """スクレイピング機能のテスト"""
    print("=== スクレイピング機能テスト開始 ===")
    
    test_url = "https://www.ichibanya.co.jp/"
    print(f"テストURL: {test_url}")
    
    try:
        result = scrape_page(test_url)
        if result:
            print(f"スクレイピング成功:")
            print(f"  タイトル: {result.get('title', 'None')}")
            print(f"  URL: {result.get('url', 'None')}")
            print(f"  コンテンツ長: {len(result.get('content', ''))}文字")
            print(f"  リンク数: {len(result.get('links', []))}")
            
            # コンテンツの一部を表示（最初の500文字）
            content = result.get('content', '')
            if content:
                print(f"  コンテンツサンプル: {content[:500]}...")
            else:
                print("  コンテンツ: 空")
        else:
            print("スクレイピング失敗: 結果がNone")
            
    except Exception as e:
        print(f"スクレイピングエラー: {e}")
    
    print("=== スクレイピング機能テスト終了 ===")

if __name__ == "__main__":
    test_scraping()
