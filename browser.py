import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import re

def clean_text(text):
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove scripts and style content
    text = re.sub(r'<script.*?</script>', '', text, flags=re.DOTALL)
    text = re.sub(r'<style.*?</style>', '', text, flags=re.DOTALL)
    return text

def browse_website(url, max_length=2000):
    """
    Browse a website and extract meaningful content.
    Returns tuple: (success boolean, content or error message)
    """
    try:
        # Add scheme if not present
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'iframe']):
            element.decompose()
        
        # Extract title
        title = soup.title.string if soup.title else "No title found"
        
        # Extract main content
        main_content = []
        
        # Try to find main content containers
        content_elements = soup.find_all(['article', 'main', 'div'], class_=re.compile(r'content|main|article'))
        if not content_elements:
            content_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        for element in content_elements:
            text = clean_text(element.get_text())
            if text and len(text) > 50:  # Only include substantial content
                main_content.append(text)
        
        # Combine and truncate content
        content = f"Title: {title}\n\nContent:\n" + "\n".join(main_content)
        if len(content) > max_length:
            content = content[:max_length] + "... (content truncated)"
            
        return True, content
        
    except requests.exceptions.RequestException as e:
        return False, f"Error accessing website: {str(e)}"
    except Exception as e:
        return False, f"Error processing website content: {str(e)}"
