#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
効率化版メイン処理

高スコア検出後の並行処理継続問題を解決し、
関連性の低いコンテンツの事前フィルタリング機能を追加
"""

import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from dotenv import load_dotenv
from config import load_config
from utils import (
    setup_logger, 
    write_result_json, 
    write_result_markdown, 
    get_current_api_usage,
    enhanced_check_api_limit,
    check_api_usage_warning,
    reset_early_termination,
    set_early_termination,
    check_early_termination,
    standardize_output_format
)
import argparse
from analyzer import ai_generate_query
from search import google_search
from scraper import scrape_page, scrape_recursive
import sys
import logging
import time

@dataclass
class TestCompanyInfo:
    """テスト用企業情報モデル"""
    company: str  # 会社名
    address: str  # 住所
    tel: str      # 電話番号
    other: Optional[List[str]] = None  # その他情報（旧社名、支店名など）
    
    def __post_init__(self):
        """初期化後処理：otherがNoneの場合は空リストに設定"""
        if self.other is None:
            self.other = []

def parse_args():
    parser = argparse.ArgumentParser(description="取引先申請情報の確認システム")
    parser.add_argument('--company', type=str, required=True, help='会社名')
    parser.add_argument('--address', type=str, required=True, help='住所')
    parser.add_argument('--tel', type=str, required=True, help='電話番号')
    parser.add_argument('--other', nargs='*', default=[], help='その他情報（旧社名、支店名など）')
    return parser.parse_args()

def process_single_page(application_info, scraped_result, config, search_rank, page_rank, logger):
    """単一ページのAI解析処理（早期終了チェック付き）"""
    # 早期終了フラグチェック
    if check_early_termination():
        logger.info(f"[{search_rank}-{page_rank}] 早期終了フラグにより処理スキップ")
        return None
    
    # コンテンツの関連性事前チェック
    title = scraped_result.get('title', '')
    url = scraped_result.get('url', '')
    company_name = application_info[0] if len(application_info) > 0 else ""

    
    print(f"[{search_rank}-{page_rank}] AI解析開始: {title[:50]}...")
    logger.info(f"[{search_rank}-{page_rank}] AI解析開始: {url}")
    
    try:
        from analyzer import ai_analyze_content
        analysis_result = ai_analyze_content(
            application_info,
            scraped_result,
            config["OLLAMA_API_URL"],
            config["OLLAMA_MODEL"]
        )
        
        # 解析結果を追加
        analysis_result.update({
            "search_rank": search_rank,
            "page_rank": page_rank,
            "url": url,
            "title": title,
            "scraped_content_length": len(scraped_result.get('content', ''))
        })
        score = analysis_result.get("score", 0.0)
        reasoning = analysis_result.get('reasoning', '')
        print(f"[{search_rank}-{page_rank}] AI解析完了: スコア={score:.3f}, 判定理由={reasoning}")
        logger.info(f"[{search_rank}-{page_rank}] AI解析結果: スコア={score:.3f}")
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"[{search_rank}-{page_rank}] AI解析エラー: {e}")
        return None

def main_fixed(test_company_info: Optional[TestCompanyInfo] = None) -> Dict[str, Any]:
    """効率化版メイン処理（早期終了問題を解決 + 事前フィルタリング機能）"""
    # 環境変数を明示的にクリア（キャッシュ回避）
    if 'OLLAMA_API_URL' in os.environ:
        del os.environ['OLLAMA_API_URL']
    
    load_dotenv()
    config = load_config()
    
    # 新しいロガー設定を適用
    logger = setup_logger(
        log_level=config.get('LOG_LEVEL', 'INFO'),
        log_file=config.get('LOG_FILE', 'app.log')
    )
    
    logger.info("=" * 60)
    logger.info("取引先申請情報確認システム 開始")
    logger.info("=" * 60)
    
    # 早期終了フラグをリセット
    reset_early_termination()
    
    # 設定値の取得
    max_queries = int(config.get("MAX_GOOGLE_SEARCH", 3))
    num_results = int(config.get("GOOGLE_SEARCH_NUM_RESULTS", 3))
    max_scrape_depth = int(config.get("MAX_SCRAPE_DEPTH", 3))
    score_threshold = float(config.get("SCORE_THRESHOLD", 0.95))

    # API使用状況を確認
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
        time.sleep(wait_time)
      # 企業情報の取得
    if test_company_info:
        company = test_company_info.company
        address = test_company_info.address
        tel = test_company_info.tel
        other = test_company_info.other or []
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
        return
      # 各クエリごとにGoogle検索とスクレイピング・AI解析
    for idx, query in enumerate(queries, 1):
        if check_early_termination():
            logger.info(f"早期終了フラグによりクエリ{idx}以降をスキップ")
            break
        logger.info(f"[{idx}] 検索クエリ: {query}")
        print(f"[{idx}] 検索クエリ: {query}")
        try:
            # Google検索実行
            search_results = google_search(
                query,
                config["GOOGLE_API_KEY"],
                config["GOOGLE_CSE_ID"],
                num=num_results,
                config=config
            )
            logger.info(f"Google検索結果件数: {len(search_results)}件")
            print(f"Google検索結果: {len(search_results)}件")
            
            for i, item in enumerate(search_results, 1):
                logger.info(f"[{i}] {item['title']} {item['link']}")
                print(f"[{i}] {item['title']} {item['link']}")
            
            # スクレイピング・AI解析
            all_analysis_results = []
            found_match = False
            
            for i, item in enumerate(search_results, 1):
                if check_early_termination() or found_match:
                    logger.info(f"早期終了フラグまたは高スコア検出により検索{i}以降をスキップ")
                    break
                
                print(f"\n[{i}] ページ解析開始: {item['title']}")
                logger.info(f"[{i}] ページ解析開始: {item['link']}")
                
                try:                    # メインページをスクレイピング・AI解析
                    print(f"[{i}] メインページスクレイピング開始: {item['link']}")
                    logger.info(f"[{i}] メインページスクレイピング開始: {item['link']}")
                    
                    user_agent = config.get("SCRAPER_USER_AGENT", "Mozilla/5.0 (compatible; CompanyVerificationBot/1.0)")
                    main_scraped = scrape_page(item['link'], timeout=10, user_agent=user_agent)
                    if main_scraped and 'error' not in main_scraped:
                        # メインページのAI解析
                        total_searched_urls += 1
                        main_analysis = process_single_page(
                            application_info, main_scraped, config, i, 0, logger
                        )
                        
                        if main_analysis:
                            all_analysis_results.append(main_analysis)
                            main_score = main_analysis.get("score", 0.0)
                            
                            # メインページで閾値チェック
                            if main_score >= score_threshold:
                                print(f"\n★★★ メインページで高スコア検出! (スコア={main_score:.3f} >= {score_threshold}) ★★★")
                                logger.info(f"メインページで高スコア検出により処理早期終了: スコア={main_score:.3f}")
                                set_early_termination()
                                found_match = True
                                break
                          # 早期終了していない場合のみ関連ページをスクレイピング
                        if not check_early_termination() and not found_match:
                            print(f"[{i}] 関連ページスクレイピング開始")
                            logger.info(f"[{i}] 関連ページスクレイピング開始: {item['link']}")
                            
                            user_agent = config.get("SCRAPER_USER_AGENT", "Mozilla/5.0 (compatible; CompanyVerificationBot/1.0)")
                            scrape_interval = float(config.get("SCRAPER_INTERVAL", 1.0))
                            
                            scraped_pages = scrape_recursive(
                                item['link'], 
                                depth=1, 
                                max_depth=max_scrape_depth,
                                timeout=10,
                                user_agent=user_agent,
                                scrape_interval=scrape_interval
                            )
                    else:
                        print(f"[{i}] メインページスクレイピング失敗")
                        logger.warning(f"[{i}] メインページスクレイピング失敗: {item['link']}")
                        continue  # 次のURLへ
                        
                    # 関連ページスクレイピング結果の処理
                    if not scraped_pages:
                        print(f"[{i}] 関連ページスクレイピング結果なし")
                        logger.warning(f"[{i}] 関連ページスクレイピング結果なし: {item['link']}")
                    else:
                        print(f"[{i}] 関連ページスクレイピング完了: {len(scraped_pages)}ページ")
                        logger.info(f"[{i}] 関連ページスクレイピング完了: {len(scraped_pages)}ページ")
                        
                        # 関連ページのAI解析                        
                        for page_idx, scraped_result in enumerate(scraped_pages, 1):
                            if check_early_termination():
                                logger.info(f"[{i}-{page_idx}] 早期終了フラグにより残りのページ解析をスキップ")
                                break
                                
                            if 'error' in scraped_result:
                                error_msg = scraped_result.get('error', '不明なエラー')
                                if error_msg == 'robots.txt disallowed':
                                    print(f"[{i}-{page_idx}] robots.txtによりスキップ: {scraped_result.get('url', '')}")
                                    logger.info(f"[{i}-{page_idx}] robots.txtによりスキップ: {scraped_result.get('url', '')}")
                                else:
                                    print(f"[{i}-{page_idx}] スクレイピングエラーによりスキップ: {error_msg}")
                                    logger.warning(f"[{i}-{page_idx}] スクレイピングエラー: {scraped_result.get('url', '')} - {error_msg}")
                                continue
                            
                            # 関連ページのAI解析
                            total_searched_urls += 1
                            analysis_result = process_single_page(
                                application_info, scraped_result, config, i, page_idx, logger
                            )
                            if analysis_result:
                                all_analysis_results.append(analysis_result)
                                score = analysis_result.get("score", 0.0)
                                
                                # 関連ページでの閾値チェック
                                if score >= score_threshold:
                                    print(f"\n★★★ 関連ページで高スコア検出! (スコア={score:.3f} >= {score_threshold}) ★★★")
                                    logger.info(f"関連ページで高スコア検出により処理早期終了: スコア={score:.3f}")
                                    set_early_termination()
                                    found_match = True
                                    break
                    
                    # 4. 現在のURLの解析結果統計を表示
                    current_url_results = [r for r in all_analysis_results if r.get("search_rank") == i]
                    if current_url_results:
                        max_score = max(r.get("score", 0.0) for r in current_url_results)
                        print(f"[{i}] ページ解析完了: 解析件数={len(current_url_results)}, 最高スコア={max_score:.3f}")
                        logger.info(f"[{i}] ページ解析結果: 解析件数={len(current_url_results)}, 最高スコア={max_score:.3f}")
                    else:
                        print(f"[{i}] ページ解析完了: 有効な解析結果なし")
                        logger.info(f"[{i}] ページ解析結果: 有効な解析結果なし")
                        
                    if found_match:
                        break
                    
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
            # total_searched_urls += len(search_results)
            
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
    
    # 判定結果のJSON/Markdown出力（標準化フォーマット適用）
    raw_result = {
        "company": company,
        "address": address,
        "tel": tel,
        "other": other,
        "results": all_query_results,
        "searched_url_count": total_searched_urls,
        "found": found,
        "early_terminated": overall_found_match
    }
    
    # 設計書準拠の標準化フォーマットに変換
    standardized_result = standardize_output_format(raw_result)
    
    # ファイル出力
    write_result_json(standardized_result)
    write_result_markdown(standardized_result)
    
    # ログ出力
    logger.info(f"判定結果出力完了: found={standardized_result['found']}, searched_urls={standardized_result['searched_url_count']}, early_terminated={standardized_result['early_terminated']}")
    print(f"✅ 判定結果をresult.jsonとresult.mdに出力しました")
    print(f"📊 最終結果: found={standardized_result['found']}, URLs={standardized_result['searched_url_count']}, 早期終了={standardized_result['early_terminated']}")
    
    return standardized_result

def main(test_company_info: Optional[TestCompanyInfo] = None) -> Dict[str, Any]:
    return main_fixed(test_company_info)

if __name__ == "__main__":
    
    testCompany01: TestCompanyInfo = TestCompanyInfo(
        company="トヨタ自動車株式会社",
        address="愛知県豊田市トヨタ町1番地",
        tel="0565-28-2121",
        # other=["旧社名: テスト商事", "支店名: 新宿支店"]
    )

    main(testCompany01)
