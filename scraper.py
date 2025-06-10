import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import logging
import time

# robots.txtキャッシュ（ドメインごと）
_robots_cache = {}

def check_robots_txt(url, user_agent="*", timeout=5):
    """
    指定URLに対してrobots.txtをチェックし、スクレイピング許可を判定
    
    Args:
        url (str): チェック対象のURL
        user_agent (str): User-Agent文字列
        timeout (int): robots.txt取得のタイムアウト秒数
    
    Returns:
        bool: スクレイピング許可の場合True、禁止の場合False
    """
    try:
        parsed_url = urlparse(url)
        domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # キャッシュから取得を試行
        if domain in _robots_cache:
            rp = _robots_cache[domain]
        else:
            # robots.txtを取得・解析
            robots_url = urljoin(domain, '/robots.txt')
            rp = RobotFileParser()
            rp.set_url(robots_url)
            
            try:
                rp.read()
                _robots_cache[domain] = rp
                logging.info(f"robots.txt取得成功: {robots_url}")
            except Exception as e:
                # robots.txt取得失敗時は許可として扱う
                logging.warning(f"robots.txt取得失敗: {robots_url} - {e}")
                _robots_cache[domain] = None
                return True
        
        # robots.txtが存在しない場合は許可
        if rp is None:
            return True
            
        # robots.txtでのアクセス許可をチェック
        can_fetch = rp.can_fetch(user_agent, url)
        
        if not can_fetch:
            logging.info(f"robots.txt でDisallow指定: {url}")
        else:
            logging.debug(f"robots.txt でAllow: {url}")
            
        return can_fetch
        
    except Exception as e:
        # エラー時は許可として扱う
        logging.warning(f"robots.txtチェックエラー: {url} - {e}")
        return True

def scrape_page(url, timeout=15, user_agent=None):
    """
    指定URLのHTMLからタイトル・本文テキスト・リンクを抽出して返す
    robots.txtチェック機能付き
    
    Args:
        url (str): スクレイピング対象URL
        timeout (int): HTTPリクエストのタイムアウト秒数
        user_agent (str): User-Agent文字列
    
    Returns:
        dict: { 'url': url, 'title': title, 'content': content, 'links': links }
    """
    # デフォルトUser-Agent設定
    if user_agent is None:
        user_agent = "Mozilla/5.0 (compatible; CompanyVerificationBot/1.0; +http://localhost/robots.txt)"
    
    # robots.txtチェック
    if not check_robots_txt(url, user_agent):
        logging.warning(f"robots.txtによりスクレイピング禁止: {url}")
        return {
            'url': url, 
            'title': '', 
            'content': '', 
            'links': [],
            'error': 'robots.txt disallowed'
        }
    
    try:
        headers = {'User-Agent': user_agent}
        res = requests.get(url, timeout=timeout, headers=headers)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        title = soup.title.string.strip() if soup.title and soup.title.string else ''
        
        # 本文テキスト（script/style除外、空行除外）
        for s in soup(['script', 'style']):
            s.decompose()
        content = ' '.join(soup.stripped_strings)
        
        # リンク抽出
        links = []
        for a in soup.find_all('a', href=True):
            link = urljoin(url, a['href'])
            links.append(link)
        
        logging.info(f"スクレイピング成功: {url} (タイトル: {title[:50]}...)")
        
        return {
            'url': url, 
            'title': title, 
            'content': content,
            'links': links
        }
    except Exception as e:
        logging.error(f"スクレイピングエラー: {url} - {e}")
        return {
            'url': url, 
            'title': '', 
            'content': '', 
            'links': [],
            'error': str(e)
        }

def scrape_recursive(url, depth=1, max_depth=2, visited=None, timeout=15, user_agent=None, scrape_interval=1.0):
    """
    指定URLから深度max_depthまで再帰的にリンクをたどり、各ページのタイトル・本文を収集
    robots.txtチェックとアクセス間隔制御機能付き
    
    Args:
        url (str): 開始URL
        depth (int): 現在の深度
        max_depth (int): 最大深度
        visited (set): 巡回済みURL集合
        timeout (int): HTTPリクエストのタイムアウト秒数
        user_agent (str): User-Agent文字列
        scrape_interval (float): スクレイピング間隔（秒）
        
    Returns:
        list[dict]: 各ページの{'url', 'title', 'content', 'links'}
    """
    if visited is None:
        visited = set()
    
    if user_agent is None:
        user_agent = "Mozilla/5.0 (compatible; CompanyVerificationBot/1.0; +http://localhost/robots.txt)"
    
    results = []
    
    if url in visited or depth > max_depth:
        return results
    
    visited.add(url)
    
    # アクセス間隔制御（初回以外）
    if len(visited) > 1:
        time.sleep(scrape_interval)
        logging.debug(f"スクレイピング間隔待機: {scrape_interval}秒")
    
    page = scrape_page(url, timeout=timeout, user_agent=user_agent)
    results.append(page)
    
    # 深度制御: max_depthまで
    if depth < max_depth and page.get('content') and 'error' not in page:
        try:
            # aタグのhrefから同一ドメインのリンクのみ抽出
            base = urlparse(url).netloc
            links = set()
            for link in page.get('links', []):
                if urlparse(link).netloc == base and link not in visited:
                    # robots.txtチェック済みリンクのみ追加
                    if check_robots_txt(link, user_agent):
                        links.add(link)
                    else:
                        logging.info(f"robots.txtにより除外: {link}")
            
            for link in links:
                results.extend(scrape_recursive(
                    link, depth+1, max_depth, visited, timeout, user_agent, scrape_interval
                ))
        except Exception as e:
            logging.error(f"再帰スクレイピングエラー: {url} - {e}")
    
    return results

if __name__ == "__main__":
    # テスト用
    url = "https://www.example.com/"
    print(scrape_page(url))
    # 再帰テスト
    # print(scrape_recursive(url, max_depth=2))
