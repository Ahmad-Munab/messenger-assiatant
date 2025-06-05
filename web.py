import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

def web_search_tool(query):
    """Performs web search and returns results"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        search_url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
        res = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        results = soup.select(".result__snippet")

        if not results:
            return "No search results found."

        search_results = []
        for result in results[:5]:  # Get top 5 results
            snippet = result.get_text(strip=True)
            if snippet:
                search_results.append(snippet)

        return "\n\n".join(search_results)
    except Exception as e:
        return f"Web search failed: {str(e)}"