import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_links(url):
    try:
        # Add http:// if not present
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        logger.info(f"Fetching URL: {url}")
        
        # Get the main domain for comparison
        main_domain = urlparse(url).netloc
        logger.info(f"Main domain: {main_domain}")
        
        # Fetch the webpage
        response = requests.get(url, timeout=10)
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
                        links.add(clean_url)
                    else:
                        links.add(f"{parsed.scheme}://{parsed.netloc}")
        
        logger.info(f"Extracted {len(links)} unique URLs from domain {main_domain}")
        return sorted(list(links))
    
    except requests.exceptions.RequestException as e:
        error_msg = f"Error fetching the URL: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg) 