import os
from dotenv import load_dotenv
from config import load_config
from utils import (
    setup_logger, 
    write_result_json, 
    write_result_markdown, 
    get_current_api_usage,
    enhanced_check_api_limit,
    check_api_usage_warning
)
import argparse
from analyzer import ai_generate_query
from search import google_search
from scraper import scrape_page, scrape_recursive
from utils import timeout_decorator, TimeoutException
import sys
import logging

def parse_args():
    parser = argparse.ArgumentParser(description="取引先申請情報の確認システム")
    parser.add_argument('--company', type=str, required=True, help='会社名')
    parser.add_argument('--address', type=str, required=True, help='住所')
    parser.add_argument('--tel', type=str, required=True, help='電話番号')
    parser.add_argument('--other', nargs='*', default=[], help='その他情報（旧社名、支店名など）')
    return parser.parse_args()

def main(test_company_info=None):
    load_dotenv()
    config = load_config()
    
    # 新しいロガー設定を適用
    logger = setup_logger(
        log_level=config.get('LOG_LEVEL', 'INFO'),
        log_file=config.get('LOG_FILE', 'app.log')
    )
    
    logger.info("=" * 60)
    logger.info("取引先申請情報確認システム 開始")
    logger.info("=" * 60)    # 設定値の取得（再帰的スクレイピング対応）
    max_queries = int(config["MAX_GOOGLE_SEARCH"])
    num_results = int(config.get("GOOGLE_SEARCH_NUM_RESULTS", 8))
    max_scrape_depth = int(config.get("MAX_SCRAPE_DEPTH", 10))
    per_processing_time = int(config.get("PER_PROCESSING_TIME", 60))
    score_threshold = float(config.get("SCORE_THRESHOLD", 0.95))

    # API使用状況を確認と警告レベルチェック
    current_usage = get_current_api_usage()
    daily_limit = int(config.get('GOOGLE_API_DAILY_LIMIT', '100'))
    warning_level = check_api_usage_warning(current_usage, daily_limit, config)
    
    logger.info(f"本日のGoogle Search API使用状況: {current_usage}/{daily_limit}")
    
    # 警告レベルに応じたメッセージ表示
    if warning_level == 2:
        print(f"⚠️  危険: API使用量が危険レベルです ({current_usage}/{daily_limit})")
        logger.warning(f"API使用量が危険レベル: {current_usage}/{daily_limit}")
    elif warning_level == 1:
        print(f"⚠️  警告: API使用量が警告レベルです ({current_usage}/{daily_limit})")
        logger.warning(f"API使用量が警告レベル: {current_usage}/{daily_limit}")
    
    # 強化されたAPI制限チェック
    can_execute, error_msg, wait_time = enhanced_check_api_limit(required_calls=max_queries, config=config)
    if not can_execute:
        print(f"❌ API制限エラー: {error_msg}")
        logger.error(f"API制限により実行停止: {error_msg}")
        sys.exit(1)
      if wait_time > 0:
        print(f"⏱️  レート制限により{wait_time:.1f}秒待機します...")
        import time
        time.sleep(wait_time)
        import time
        time.sleep(wait_time)
    
    # テスト用の企業情報が提供された場合はそれを使用、そうでなければコマンドライン引数を解析
    if test_company_info:
        company = test_company_info['company']
        address = test_company_info['address']
        tel = test_company_info['tel']
        other = test_company_info.get('other', [])
        logger.info("テストモードで実行中")
    else:
        args = parse_args()
        company = args.company
        address = args.address
        tel = args.tel
        other = args.other
        logger.info("コマンドラインモードで実行中")
    
    logger.info(f"受け取った申請情報: 会社名={company}, 住所={address}, 電話番号={tel}, その他={other}")
    application_info = [company, address, tel] + other
    
    print("受け取った申請情報:")
    print(f"会社名: {company}")
    print(f"住所: {address}")
    print(f"電話番号: {tel}")
    print(f"その他: {other}")
    print(f"本日のAPI使用状況: {current_usage}/{daily_limit}")
    
    print(f"[DEBUG] PER_PROCESSING_TIME={per_processing_time}")
    print(f"[DEBUG] MAX_SCRAPE_DEPTH={max_scrape_depth}")
    logger.info(f"PER_PROCESSING_TIME: {per_processing_time}")
    logger.info(f"MAX_SCRAPE_DEPTH: {max_scrape_depth}")

    # 全結果を蓄積するためのグローバル変数
    all_query_results = []
    total_searched_urls = 0
    overall_found_match = False

    # AIによる検索クエリ生成
    try:
        queries = ai_generate_query(
            application_info,
            config["OLLAMA_API_URL"],
            config["OLLAMA_MODEL"],
            max_queries=max_queries
        )
        logger.info(f"AI生成検索クエリリスト: {queries}")
        print(f"AI生成検索クエリリスト: {queries}")
    except Exception as e:
        logger.error(f"AIによる検索クエリ生成に失敗: {e}", exc_info=True)
        print("AIによる検索クエリ生成に失敗しました")
        return    # 各クエリごとにGoogle検索とスクレイピング・AI解析
    for idx, query in enumerate(queries, 1):
        logger.info(f"[{idx}] 検索クエリ: {query}")
        print(f"[{idx}] 検索クエリ: {query}")
        
        try:            # Google検索実行（強化されたAPI制限管理を使用）
            search_results = google_search(
                query,
                config["GOOGLE_API_KEY"],
                config["GOOGLE_CSE_ID"],
                num=num_results,
                config=config
            )
            
            logger.info(f"Google検索結果件数: {len(search_results)}")
            for i, item in enumerate(search_results, 1):
                logger.info(f"[{i}] {item['title']} {item['link']}")
            
            print(f"Google検索結果: {len(search_results)}件")
            for i, item in enumerate(search_results, 1):
                print(f"[{i}] {item['title']} {item['link']}")
            
            # 再帰的スクレイピング・AI解析
            all_analysis_results = []
            found_match = False
            
            for i, item in enumerate(search_results, 1):
                if found_match:
                    break
                
                print(f"\n[{i}] 再帰的スクレイピング+AI解析開始: {item['title']}")
                logger.info(f"[{i}] 再帰的スクレイピング+AI解析開始: {item['link']}")
                
                try:
                    # タイムアウト付きで再帰的スクレイピング+AI解析を実行
                    @timeout_decorator(per_processing_time)
                    def process_recursive_pages():
                        # 再帰的スクレイピング実行
                        scraped_pages = scrape_recursive(
                            item['link'], 
                            depth=1, 
                            max_depth=max_scrape_depth,
                            timeout=10
                        )
                        
                        if not scraped_pages:
                            return []
                        
                        print(f"[{i}] 再帰的スクレイピング完了: {len(scraped_pages)}ページ")
                        logger.info(f"[{i}] 再帰的スクレイピング完了: {len(scraped_pages)}ページ")
                        
                        page_results = []
                        
                        # 各ページごとにAI解析実行
                        for page_idx, scraped_result in enumerate(scraped_pages, 1):
                            if 'error' in scraped_result:
                                continue
                                
                            print(f"[{i}-{page_idx}] AI解析開始: {scraped_result.get('title', '')[:30]}...")
                            logger.info(f"[{i}-{page_idx}] AI解析開始: {scraped_result.get('url', '')}")
                            
                            from analyzer import ai_analyze_content
                            analysis_result = ai_analyze_content(
                                application_info,
                                scraped_result,
                                config["OLLAMA_API_URL"],
                                config["OLLAMA_MODEL"]
                            )
                            
                            # 解析結果を追加
                            analysis_result.update({
                                "search_rank": i,
                                "page_rank": page_idx,
                                "url": scraped_result.get('url', ''),
                                "title": scraped_result.get('title', ''),
                                "scraped_content_length": len(scraped_result.get('content', ''))
                            })
                            
                            page_results.append(analysis_result)
                            
                            score = analysis_result.get("score", 0.0)
                            print(f"[{i}-{page_idx}] AI解析完了: スコア={score:.3f}")
                            logger.info(f"[{i}-{page_idx}] AI解析結果: スコア={score:.3f}")
                            
                            # 閾値チェック - 95%以上なら即時終了
                            if score >= score_threshold:
                                print(f"\n★★★ 高スコア検出! (スコア={score:.3f} >= {score_threshold}) 再帰処理を終了します ★★★")
                                logger.info(f"高スコア検出により再帰処理早期終了: スコア={score:.3f}")
                                return page_results
                        
                        return page_results
                    
                    # タイムアウト付き実行
                    page_analysis_results = process_recursive_pages()
                    
                    if page_analysis_results:
                        all_analysis_results.extend(page_analysis_results)
                        
                        # 最高スコアをチェックして早期終了判定
                        max_score = max(r.get("score", 0.0) for r in page_analysis_results)
                        best_result = max(page_analysis_results, key=lambda x: x.get("score", 0.0))
                        
                        print(f"[{i}] 再帰的解析完了: 最高スコア={max_score:.3f}, 理由={best_result.get('reasoning', '')}")
                        logger.info(f"[{i}] 再帰的解析結果: 最高スコア={max_score:.3f}")
                        
                        # 閾値チェック - 95%以上なら全体のクエリ処理も終了
                        if max_score >= score_threshold:
                            print(f"\n★★★ 高スコア検出! (スコア={max_score:.3f} >= {score_threshold}) 検索を終了します ★★★")
                            logger.info(f"高スコア検出によりクエリ{idx}で早期終了: スコア={max_score:.3f}")
                            found_match = True
                            break
                    else:
                        print(f"[{i}] 再帰的スクレイピング失敗: 内容を取得できませんでした")
                        logger.warning(f"[{i}] 再帰的スクレイピング失敗: {item['link']}")
                
                except TimeoutException:
                    print(f"[{i}] タイムアウト({per_processing_time}秒): {item['title']}")
                    logger.warning(f"[{i}] タイムアウト({per_processing_time}秒): {item['link']}")
                
                except Exception as e:
                    print(f"[{i}] スクレイピング/解析エラー: {str(e)}")
                    logger.error(f"[{i}] スクレイピング/解析エラー: {item['link']} {e}", exc_info=True)
            
            # クエリ結果の表示と蓄積
            print(f"\nクエリ[{idx}]の解析結果: {len(all_analysis_results)}件")
            all_analysis_results.sort(key=lambda x: x.get("score", 0.0), reverse=True)
            for i, result in enumerate(all_analysis_results, 1):
                print(f"  [{i}] スコア={result.get('score', 0.0):.3f} - {result.get('title', '')[:50]} - {result.get('url', '')}")
            
            # 結果をグローバルリストに追加
            all_query_results.extend(all_analysis_results)
            total_searched_urls += len(search_results)
            
            # 高スコアが見つかった場合は全体のクエリ処理も終了
            if found_match:
                overall_found_match = True
                logger.info(f"高スコア検出により全クエリ処理を早期終了")
                break
                
        except Exception as e:
            logger.error(f"Google検索APIエラー: {e}", exc_info=True)
            print("Google検索APIでエラーが発生しました")

    # 全クエリからのすべての結果を統合し、スコア順でソート
    all_query_results.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    
    # マッチング判定（最高スコアで判定）
    best_score = all_query_results[0].get("score", 0.0) if all_query_results else 0.0
    found = best_score >= score_threshold
    
    # 判定結果のJSON/Markdown出力
    from utils import write_result_json, write_result_markdown
    result = {
        "company": company,
        "address": address,
        "tel": tel,
        "other": other,
        "results": all_query_results,
        "searched_urls": total_searched_urls,
        "found": found,
        "early_termination": overall_found_match
    }
    
    write_result_json(result)
    write_result_markdown(result)
    
    return result

if __name__ == "__main__":
    main()
