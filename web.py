import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
from typing import Dict, List, Union, Tuple

def extract_search_results(soup: BeautifulSoup) -> List[Dict[str, str]]:
    """Extract search results from BeautifulSoup object"""
    results = []
    for result in soup.select(".result"):
        title_elem = result.select_one(".result__title")
        snippet_elem = result.select_one(".result__snippet")
        link_elem = result.select_one(".result__url")
        
        if title_elem:
            # Get title and try to find actual URL
            title = title_elem.get_text(strip=True)
            url = ""
            
            # Try to get URL from title link first
            title_link = title_elem.find("a")
            if title_link and "href" in title_link.attrs:
                url = title_link["href"]
            elif link_elem:  # Fallback to displayed URL
                url = link_elem.get_text(strip=True)
            
            snippet = ""
            if snippet_elem:
                snippet = snippet_elem.get_text(strip=True)
            
            if title and (snippet or url):
                results.append({
                    "title": title,
                    "snippet": snippet,
                    "url": url
                })
    
    return results

def web_search_tool(query: str) -> str:
    """
    Performs web search and returns formatted results
    
    :param query: Search query string
    :return: Formatted string of search results or error message
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        search_url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
        res = requests.get(search_url, headers=headers, timeout=10)
        res.raise_for_status()
        
        soup = BeautifulSoup(res.text, "html.parser")
        results = extract_search_results(soup)

        if not results:
            return "No search results found."

        formatted_results = []
        for result in results[:5]:  # Get top 5 results
            formatted_results.append(
                f"Title: {result['title']}\n"
                f"URL: {result['url']}\n"
                f"Summary: {result['snippet']}\n"
            )

        return "\n\n".join(formatted_results)
        
    except requests.RequestException as e:
        return f"Web search network error: {str(e)}"
    except Exception as e:
        return f"Web search error: {str(e)}"