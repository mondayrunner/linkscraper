from flask import Flask, render_template, request, jsonify
from scraper import extract_links
import logging
import os

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return render_template('index.html', links=[], error=None)

@app.route('/scrape', methods=['POST'])
def scrape():
    try:
        url = request.json.get('url', '')
        if not url:
            logger.error("No URL provided")
            return jsonify({'error': 'URL is required', 'links': [], 'content': ''}), 400
        
        logger.info(f"Received scrape request for URL: {url}")
        links, content = extract_links(url)
        logger.info(f"Extracted {len(links)} links")
        
        if not links:
            logger.warning("No links found")
            return jsonify({'error': 'No links found', 'links': [], 'content': ''}), 404
            
        response_data = {'links': links, 'content': content}
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        return jsonify({'error': str(e), 'links': [], 'content': ''}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 