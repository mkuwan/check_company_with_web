#!/usr/bin/env python3
"""
高スコア早期終了機能のテストスクリプト
実在する有名企業でテストして95%以上のスコアを取得できるかチェック
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import main

def test_high_score_early_termination():
    """
    高スコア早期終了のテスト
    実在する有名企業の情報でテスト
    """
    print("=== 高スコア早期終了テスト開始 ===")
    
    # 実在する有名企業の情報を使用
    # トヨタ自動車株式会社の公開情報
    test_company_info = {
        "company": "トヨタ自動車株式会社",
        "address": "愛知県豊田市トヨタ町1番地",
        "tel": "0565-28-2121",
        "other": []
    }
    
    print(f"テスト対象: {test_company_info['company']}")
    print(f"住所: {test_company_info['address']}")
    print(f"電話: {test_company_info['tel']}")
    print()
    
    try:
        # main関数を実行
        result = main(test_company_info)
        
        print("\n=== テスト結果 ===")
        print(f"実行結果: {result}")
        
        # 結果ファイルを確認
        with open('result.json', 'r', encoding='utf-8') as f:
            import json
            result_data = json.load(f)
            
        print(f"検索URL数: {result_data.get('searched_urls', 0)}")
        print(f"早期終了: {'はい' if result_data.get('early_termination', False) else 'いいえ'}")
        
        if result_data.get('results'):
            max_score = max(r['score'] for r in result_data['results'])
            print(f"最高スコア: {max_score:.3f}")
            
            if max_score >= 0.95:
                print("✅ 95%以上のスコアを達成しました！")
                if result_data.get('early_termination', False):
                    print("✅ 早期終了も正常に動作しました！")
                else:
                    print("⚠️ 早期終了フラグが設定されていません")
            else:
                print(f"⚠️ 最高スコアが95%未満でした（{max_score:.1%}）")
        
    except Exception as e:
        print(f"❌ テスト実行中にエラーが発生: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_high_score_early_termination()
