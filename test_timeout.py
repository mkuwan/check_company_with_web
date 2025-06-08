#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
個別処理タイムアウト機能のテスト

目的:
- 60秒のタイムアウト設定で各スクレイピング+AI解析処理が正常に動作することを確認
- タイムアウト発生時に適切なエラーハンドリングが行われることを確認
"""

import os
import sys
import time
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import timeout_decorator, TimeoutException

def test_timeout_functionality():
    """タイムアウト機能の動作テスト"""
    print("=== タイムアウト機能テスト開始 ===")
    
    # 1. 正常処理のテスト（タイムアウト以内で完了）
    print("\n[TEST 1] 正常処理テスト（5秒以内完了）")
    
    @timeout_decorator(10)  # 10秒タイムアウト
    def quick_process():
        print("  - 処理開始...")
        time.sleep(2)  # 2秒の処理
        print("  - 処理完了!")
        return "成功"
    
    try:
        result = quick_process()
        print(f"  結果: {result}")
        print("  ✅ 正常処理テスト PASSED")
    except Exception as e:
        print(f"  ❌ 正常処理テスト FAILED: {e}")
    
    # 2. タイムアウト処理のテスト
    print("\n[TEST 2] タイムアウト処理テスト（5秒でタイムアウト）")
    
    @timeout_decorator(5)  # 5秒タイムアウト
    def slow_process():
        print("  - 長時間処理開始...")
        time.sleep(10)  # 10秒の処理（タイムアウトする）
        print("  - 処理完了!")
        return "成功"
    
    try:
        result = slow_process()
        print(f"  ❌ タイムアウトテスト FAILED: タイムアウトしませんでした")
    except TimeoutException as e:
        print(f"  ✅ タイムアウトテスト PASSED: {e}")
    except Exception as e:
        print(f"  ❌ タイムアウトテスト FAILED (予期しないエラー): {e}")

def test_realistic_scenario():
    """実際のスクレイピング+AI解析をシミュレート"""
    print("\n=== 実際のシナリオテスト ===")
    
    # 設定値を読み込み
    load_dotenv()
    from config import load_config
    config = load_config()
    per_processing_time = int(config.get("PER_PROCESSING_TIME", 60))
    
    print(f"設定されたタイムアウト時間: {per_processing_time}秒")
    
    @timeout_decorator(per_processing_time)
    def simulate_scraping_and_ai():
        print("  - スクレイピング開始...")
        time.sleep(2)  # スクレイピング処理のシミュレート
        print("  - スクレイピング完了 (2秒)")
        
        print("  - AI解析開始...")
        time.sleep(3)  # AI解析処理のシミュレート
        print("  - AI解析完了 (3秒)")
        
        return {
            "score": 0.85,
            "reasoning": "テスト成功",
            "matched_info": "会社名が一致"
        }
    
    try:
        start_time = time.time()
        result = simulate_scraping_and_ai()
        end_time = time.time()
        elapsed = end_time - start_time
        
        print(f"  処理時間: {elapsed:.2f}秒")
        print(f"  結果: スコア={result['score']}, 理由={result['reasoning']}")
        print("  ✅ 実際のシナリオテスト PASSED")
        
    except TimeoutException as e:
        print(f"  ❌ 実際のシナリオテスト FAILED: {e}")
    except Exception as e:
        print(f"  ❌ 実際のシナリオテスト FAILED (予期しないエラー): {e}")

if __name__ == "__main__":
    test_timeout_functionality()
    test_realistic_scenario()
    print("\n=== テスト完了 ===")
