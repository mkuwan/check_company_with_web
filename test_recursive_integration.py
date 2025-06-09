#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
再帰的スクレイピング機能の結合テスト
"""

from main import main

def test_recursive_scraping():
    """再帰的スクレイピング機能のテスト"""
    print("=== 再帰的スクレイピング機能 結合テスト開始 ===")
    
    # テスト用企業情報
    test_company_info = {
        'company': 'トヨタ自動車株式会社',
        'address': '愛知県豊田市トヨタ町1番地',
        'tel': '0565-28-2121',
        'other': []
    }
    
    print(f"テスト対象: {test_company_info['company']}")
    print(f"住所: {test_company_info['address']}")
    print(f"電話: {test_company_info['tel']}")
    
    try:
        result = main(test_company_info)
        
        print("\n=== テスト結果 ===")
        print(f"実行結果: {result}")
        print(f"検索URL数: {result.get('searched_urls', 0)}")
        print(f"見つかった結果数: {len(result.get('results', []))}")
        print(f"早期終了: {'はい' if result.get('early_termination', False) else 'いいえ'}")
        
        if result.get('results'):
            print(f"最高スコア: {result['results'][0].get('score', 0.0):.3f}")
            print(f"最高スコアページ: {result['results'][0].get('url', '')}")
            
            # 再帰的に取得されたページが複数あるかチェック
            pages_per_search = {}
            for r in result['results']:
                search_rank = r.get('search_rank', 0)
                if search_rank not in pages_per_search:
                    pages_per_search[search_rank] = 0
                pages_per_search[search_rank] += 1
            
            print(f"検索結果ごとのページ数: {pages_per_search}")
            
            # 再帰的スクレイピングが動作していることを確認
            if any(count > 1 for count in pages_per_search.values()):
                print("✅ 再帰的スクレイピング機能が動作していることを確認")
            else:
                print("⚠️ 再帰的スクレイピング機能が十分に動作していない可能性があります")
        
        print("=== テスト完了 ===")
        return result
        
    except Exception as e:
        print(f"テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_recursive_scraping()
