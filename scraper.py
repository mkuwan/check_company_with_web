import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def scrape_page(url, timeout=15):
    """
    指定URLのHTMLからタイトル・本文テキスト・リンクを抽出して返す
    戻り値: dict { 'url': url, 'title': title, 'content': content, 'links': links }
    """
    try:
        res = requests.get(url, timeout=timeout)
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
        
        return {
            'url': url, 
            'title': title, 
            'content': content,
            'links': links
        }
    except Exception as e:
        return {
            'url': url, 
            'title': '', 
            'content': '', 
            'links': [],
            'error': str(e)
        }

def scrape_recursive(url, depth=1, max_depth=2, visited=None, timeout=15):
    """
    指定URLから深度max_depthまで再帰的にリンクをたどり、各ページのタイトル・本文を収集
    visited: 巡回済みURL集合
    戻り値: list[dict] 各ページの{'url', 'title', 'text'}
    """
    if visited is None:
        visited = set()
    results = []
    if url in visited or depth > max_depth:
        return results
    visited.add(url)
    page = scrape_page(url, timeout=timeout)
    results.append(page)    # 深度制御: max_depthまで
    if depth < max_depth and page.get('content'):
        try:
            res = requests.get(url, timeout=timeout)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, 'html.parser')
            # aタグのhrefから同一ドメインのリンクのみ抽出
            base = urlparse(url).netloc
            links = set()
            for a in soup.find_all('a', href=True):
                link = urljoin(url, a['href'])
                if urlparse(link).netloc == base and link not in visited:
                    links.add(link)
            for link in links:
                results.extend(scrape_recursive(link, depth+1, max_depth, visited, timeout))
        except Exception:
            pass
    return results

if __name__ == "__main__":
    # テスト用
    url = "https://www.example.com/"
    print(scrape_page(url))
    # 再帰テスト
    # print(scrape_recursive(url, max_depth=2))
