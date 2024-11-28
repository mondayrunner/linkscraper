import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_text(text):
    # Remove extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text

def extract_main_content(soup):
    # Common WordPress and modern website content containers
    content_selectors = [
        # WordPress specific
        '.entry-content',
        '.post-content',
        'article',
        '.site-content',
        '.content-area',
        # Common content areas
        'main',
        '#main',
        '#content',
        '.content',
        '[role="main"]',
        # Specific content blocks
        '.page-content',
        '.article-content',
        '.main-content'
    ]
    
    # Try each selector
    for selector in content_selectors:
        content = soup.select_one(selector)
        if content:
            # Remove unwanted elements
            for elem in content.find_all(['script', 'style', 'nav', 'header', 'footer', 'iframe', 'noscript']):
                elem.decompose()
            return content
    
    # If no content found, try the body but clean it
    body = soup.find('body')
    if body:
        # Remove unwanted elements
        for elem in body.find_all(['script', 'style', 'nav', 'header', 'footer', 'iframe', 'noscript', 'aside']):
            elem.decompose()
        
        # Also try to find and remove common navigation and footer classes
        for elem in body.find_all(class_=re.compile(r'(menu|nav|footer|header|sidebar|widget)', re.I)):
            elem.decompose()
            
        return body
    
    return soup

def extract_content_from_url(url):
    try:
        # Add http:// if not present
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Fetch the webpage with a desktop user agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to get the page title
        title = soup.title.string if soup.title else url
        title = clean_text(title)
        
        # Get main content
        main_content = extract_main_content(soup)
        
        # Extract text and clean it
        text_content = []
        
        # First try to get all paragraphs
        paragraphs = main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'])
        
        if paragraphs:
            for p in paragraphs:
                cleaned = clean_text(p.get_text())
                if cleaned and len(cleaned) > 20:  # Only include substantial paragraphs
                    text_content.append(cleaned)
        else:
            # Fallback to all text if no paragraphs found
            for text in main_content.stripped_strings:
                cleaned = clean_text(text)
                if cleaned and len(cleaned) > 20:  # Only include substantial text
                    text_content.append(cleaned)
        
        if text_content:
            return f"\n=== {title} ===\n\n" + '\n\n'.join(text_content) + "\n\n"
        else:
            return f"\n=== {title} ===\n\nNo content found\n\n"
            
    except Exception as e:
        logger.error(f"Error extracting content from {url}: {str(e)}")
        return f"\n=== Error: {url} ===\n\nFailed to extract content: {str(e)}\n\n"

def extract_all_content(urls, max_workers=5):
    all_content = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(extract_content_from_url, url): url for url in urls}
        for future in as_completed(future_to_url):
            content = future.result()
            if content:
                all_content.append(content)
    
    return ''.join(all_content)

def extract_links(url):
    try:
        # Add http:// if not present
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        logger.info(f"Fetching URL: {url}")
        
        # Get the main domain for comparison
        main_domain = urlparse(url).netloc
        logger.info(f"Main domain: {main_domain}")
        
        # Fetch the webpage with a desktop user agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all links
        links = set()
        link_elements = soup.find_all('a')
        logger.info(f"Found {len(link_elements)} link elements")
        
        for link in link_elements:
            href = link.get('href')
            if href:
                # Convert relative URLs to absolute URLs
                full_url = urljoin(url, href)
                # Parse the URL
                parsed = urlparse(full_url)
                # Only include URLs from the same domain
                if parsed.netloc == main_domain:
                    # Remove fragments and queries for cleaner URLs
                    clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                    if parsed.path:
                        links.add(clean_url.rstrip('/'))
                    else:
                        links.add(f"{parsed.scheme}://{parsed.netloc}")
        
        links_list = sorted(list(links))
        logger.info(f"Extracted {len(links_list)} unique URLs from domain {main_domain}")
        
        # Extract content from all URLs
        logger.info("Extracting content from all URLs...")
        all_content = extract_all_content(links_list)
        logger.info("Content extraction completed")
        
        return links_list, all_content
    
    except requests.exceptions.RequestException as e:
        error_msg = f"Error fetching the URL: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg) 