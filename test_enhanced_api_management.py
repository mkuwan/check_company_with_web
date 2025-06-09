"""
強化されたGoogle API使用制限管理機能のテスト
"""
import os
import sys
import time
from dotenv import load_dotenv
from utils import (
    enhanced_check_api_limit, 
    check_rate_limits,
    record_api_call,
    check_api_usage_warning,
    get_current_api_usage,
    update_api_usage,
    setup_logger
)
from config import load_config

def test_enhanced_api_management():
    """強化されたAPI使用件数管理機能をテスト"""
    load_dotenv()
    config = load_config()
    
    # ロガー設定
    logger = setup_logger(log_level="INFO", log_file="test_enhanced_api_management.log")
    
    print("=" * 70)
    print("強化されたGoogle Search API使用制限管理機能 テスト開始")
    print("=" * 70)
    
    # 1. 基本設定確認
    print(f"[テスト1] 基本設定確認")
    daily_limit = int(config.get('GOOGLE_API_DAILY_LIMIT', '100'))
    rate_limit_per_minute = int(config.get("GOOGLE_API_RATE_LIMIT_PER_MINUTE", 60))
    rate_limit_per_second = int(config.get("GOOGLE_API_RATE_LIMIT_PER_SECOND", 10))
    warning_threshold = int(config.get("GOOGLE_API_WARNING_THRESHOLD", 80))
    strict_mode = config.get("GOOGLE_API_STRICT_MODE", "false").lower() == "true"
    
    print(f"1日の制限: {daily_limit}件")
    print(f"分間制限: {rate_limit_per_minute}件/分")
    print(f"秒間制限: {rate_limit_per_second}件/秒")
    print(f"警告閾値: {warning_threshold}%")
    print(f"厳格モード: {strict_mode}")
    
    # 2. 警告レベルテスト
    print(f"\n[テスト2] 警告レベルテスト")
    current_usage = get_current_api_usage()
    
    # 様々な使用量での警告レベルをテスト
    test_usages = [30, 50, 80, 90, 95, 99]
    for usage in test_usages:
        warning_level = check_api_usage_warning(usage, daily_limit, config)
        warning_text = ["正常", "警告", "危険"][warning_level]
        print(f"使用量{usage}件({usage}%): {warning_text}")
    
    # 3. レート制限テスト
    print(f"\n[テスト3] レート制限チェックテスト")
    can_call, wait_time = check_rate_limits(config)
    print(f"レート制限チェック結果: 実行可能={can_call}, 待機時間={wait_time:.1f}秒")
    
    # 4. 強化されたAPI制限チェックテスト
    print(f"\n[テスト4] 強化されたAPI制限チェックテスト")
    
    # 正常なケース
    can_exec, error_msg, wait_time = enhanced_check_api_limit(1, config)
    print(f"1件実行チェック: 可能={can_exec}, エラー='{error_msg}', 待機={wait_time:.1f}秒")
    
    # 大量実行のケース
    can_exec_bulk, error_msg_bulk, wait_time_bulk = enhanced_check_api_limit(50, config)
    print(f"50件実行チェック: 可能={can_exec_bulk}, エラー='{error_msg_bulk}', 待機={wait_time_bulk:.1f}秒")
    
    # 5. API呼び出し記録テスト
    print(f"\n[テスト5] API呼び出し記録テスト")
    print("連続API呼び出しシミュレーション...")
    
    for i in range(3):
        print(f"呼び出し {i+1}/3:")
        
        # レート制限チェック
        can_call, wait_time = check_rate_limits(config)
        print(f"  制限チェック: 可能={can_call}, 待機={wait_time:.1f}秒")
        
        if wait_time > 0:
            print(f"  {wait_time:.1f}秒待機中...")
            time.sleep(wait_time)
        
        # API呼び出し記録
        record_api_call(config)
        print(f"  API呼び出しを記録しました")
        
        # 少し待機
        time.sleep(0.5)
    
    # 6. 実際のAPI使用量更新テスト
    print(f"\n[テスト6] API使用量更新テスト")
    old_usage = get_current_api_usage()
    print(f"更新前の使用量: {old_usage}")
    
    # テスト用に1件追加
    update_api_usage(1)
    new_usage = get_current_api_usage()
    print(f"1件追加後の使用量: {new_usage}")
    
    # 警告レベル確認
    warning_level = check_api_usage_warning(new_usage, daily_limit, config)
    warning_text = ["正常", "警告", "危険"][warning_level]
    print(f"現在の警告レベル: {warning_text}")
    
    # 7. 制限近くでのテスト
    print(f"\n[テスト7] 制限近くでのテスト")
    
    # 警告レベルまで使用量を設定
    warning_usage = int(daily_limit * (warning_threshold / 100))
    print(f"警告レベル使用量（{warning_usage}件）での動作テスト")
    
    # 一時的に使用量ファイルを更新
    from utils import get_api_usage_file_path
    usage_file = get_api_usage_file_path()
    original_usage = get_current_api_usage()
    
    try:
        with open(usage_file, "w", encoding="utf-8") as f:
            f.write(str(warning_usage))
        
        # 制限チェック
        can_exec, error_msg, wait_time = enhanced_check_api_limit(1, config)
        print(f"警告レベルでの実行チェック: 可能={can_exec}")
        
        # 危険レベルまで設定
        danger_usage = int(daily_limit * 0.95)
        with open(usage_file, "w", encoding="utf-8") as f:
            f.write(str(danger_usage))
        
        can_exec_danger, error_msg_danger, wait_time_danger = enhanced_check_api_limit(1, config)
        print(f"危険レベル（{danger_usage}件）での実行チェック: 可能={can_exec_danger}")
        
        # 制限超過レベル
        over_usage = daily_limit
        with open(usage_file, "w", encoding="utf-8") as f:
            f.write(str(over_usage))
        
        can_exec_over, error_msg_over, wait_time_over = enhanced_check_api_limit(1, config)
        print(f"制限超過（{over_usage}件）での実行チェック: 可能={can_exec_over}")
        print(f"エラーメッセージ: {error_msg_over}")
        
    finally:
        # 元の使用量に戻す
        with open(usage_file, "w", encoding="utf-8") as f:
            f.write(str(original_usage))
    
    # 8. 設定値テスト
    print(f"\n[テスト8] 各種設定値テスト")
    auto_pause = config.get("GOOGLE_API_AUTO_PAUSE", "true").lower() == "true"
    pause_duration = int(config.get("GOOGLE_API_PAUSE_DURATION", 60))
    retry_attempts = int(config.get("GOOGLE_API_RETRY_ATTEMPTS", 3))
    retry_delay = int(config.get("GOOGLE_API_RETRY_DELAY", 1))
    
    print(f"自動一時停止: {auto_pause}")
    print(f"一時停止時間: {pause_duration}秒")
    print(f"リトライ回数: {retry_attempts}回")
    print(f"リトライ間隔: {retry_delay}秒")
    
    print("\n" + "=" * 70)
    print("強化されたAPI使用制限管理機能テスト完了")
    print("=" * 70)

def test_burst_limit():
    """バースト制限のテスト"""
    load_dotenv()
    config = load_config()
    
    print("\n[追加テスト] バースト制限テスト")
    burst_limit = int(config.get("GOOGLE_API_BURST_LIMIT", 20))
    print(f"バースト制限: {burst_limit}件")
    
    # 短時間での大量呼び出しをシミュレーション
    print("短時間での大量API呼び出しシミュレーション...")
    
    start_time = time.time()
    calls_made = 0
    
    for i in range(burst_limit + 5):  # 制限を超える呼び出し
        can_call, wait_time = check_rate_limits(config)
        
        if can_call:
            record_api_call(config)
            calls_made += 1
            print(f"  呼び出し {calls_made}: 成功")
        else:
            print(f"  呼び出し {i+1}: レート制限により待機（{wait_time:.1f}秒）")
            break
        
        time.sleep(0.1)  # 短い間隔
    
    elapsed_time = time.time() - start_time
    print(f"実行時間: {elapsed_time:.1f}秒, 成功した呼び出し: {calls_made}件")

if __name__ == "__main__":
    test_enhanced_api_management()
    test_burst_limit()
