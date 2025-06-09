"""
Google Search API使用件数管理機能のテスト
"""
import os
import sys
from dotenv import load_dotenv
from utils import get_current_api_usage, update_api_usage, check_api_limit, get_api_usage_file_path, setup_logger
from config import load_config

def test_api_management():
    """API使用件数管理機能をテスト"""
    load_dotenv()
    config = load_config()
    
    # ロガー設定
    logger = setup_logger(log_level="INFO", log_file="test_api_management.log")
    
    print("=" * 60)
    print("Google Search API使用件数管理機能 テスト開始")
    print("=" * 60)
    
    # 1. 現在の使用件数確認
    usage_file = get_api_usage_file_path()
    current_usage = get_current_api_usage()
    daily_limit = int(config.get('GOOGLE_API_DAILY_LIMIT', '100'))
    
    print(f"使用件数ファイル: {usage_file}")
    print(f"現在の使用件数: {current_usage}")
    print(f"1日の制限: {daily_limit}")
    
    # 2. API制限チェックテスト
    print(f"\n[テスト1] API制限チェック")
    can_use_1 = check_api_limit(required_calls=1, daily_limit=daily_limit)
    can_use_5 = check_api_limit(required_calls=5, daily_limit=daily_limit)
    can_use_over_limit = check_api_limit(required_calls=daily_limit + 1, daily_limit=daily_limit)
    
    print(f"1回の呼び出し可能: {can_use_1}")
    print(f"5回の呼び出し可能: {can_use_5}")
    print(f"制限超過呼び出し可能: {can_use_over_limit}")
    
    # 3. 使用件数更新テスト
    print(f"\n[テスト2] 使用件数更新テスト")
    old_usage = get_current_api_usage()
    print(f"更新前: {old_usage}")
    
    # テスト用に1件追加
    update_api_usage(1)
    new_usage = get_current_api_usage()
    print(f"1件追加後: {new_usage}")
    
    # さらに3件追加
    update_api_usage(3)
    newest_usage = get_current_api_usage()
    print(f"さらに3件追加後: {newest_usage}")
    
    # 4. 検索API実行シミュレーション
    print(f"\n[テスト3] 検索API実行シミュレーション")
    try:
        from search import google_search
        
        # 制限チェック付きでgoogle_search関数をテスト
        print("実際のGoogle検索を実行してAPI管理をテスト...")
        
        # テスト用の簡単なクエリ
        test_query = "Python programming"
        
        # 実際のAPI呼び出し
        if check_api_limit(required_calls=1, daily_limit=daily_limit):
            print(f"API制限チェック: OK")
            print(f"クエリ実行: '{test_query}'")
            
            # 実際のAPI呼び出しはコメントアウト（テスト時のAPI消費を避ける）
            # results = google_search(
            #     test_query,
            #     config["GOOGLE_API_KEY"],
            #     config["GOOGLE_CSE_ID"],
            #     num=3,
            #     daily_limit=daily_limit
            # )
            # print(f"検索結果: {len(results)}件")
            
            print("※実際のAPI呼び出しはスキップしました（テスト用）")
        else:
            print("API制限により実行をスキップしました")
            
    except Exception as e:
        print(f"エラー: {e}")
    
    # 5. 制限近くでのテスト
    print(f"\n[テスト4] 制限近くでのテスト")
    print(f"現在の使用件数: {get_current_api_usage()}")
    
    # 制限の90%まで使用した場合をシミュレーション
    simulated_usage = int(daily_limit * 0.9)
    print(f"シミュレーション: {simulated_usage}件使用済みとして設定")
    
    # 一時的にファイルを更新
    usage_file = get_api_usage_file_path()
    with open(usage_file, "w", encoding="utf-8") as f:
        f.write(str(simulated_usage))
    
    # チェック
    remaining = daily_limit - simulated_usage
    print(f"残り使用可能件数: {remaining}件")
    
    can_use_remaining = check_api_limit(required_calls=remaining, daily_limit=daily_limit)
    can_use_over = check_api_limit(required_calls=remaining + 1, daily_limit=daily_limit)
    
    print(f"残り件数での実行可能: {can_use_remaining}")
    print(f"残り件数+1での実行可能: {can_use_over}")
    
    print("\n" + "=" * 60)
    print("API使用件数管理機能テスト完了")
    print("=" * 60)

if __name__ == "__main__":
    test_api_management()
