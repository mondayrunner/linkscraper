from flask import Flask, render_template, request, jsonify
from scraper import extract_links
import logging

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
            return jsonify({'error': 'URL is required', 'links': []}), 400
        
        logger.info(f"Received scrape request for URL: {url}")
        links = extract_links(url)
        logger.info(f"Extracted {len(links)} links: {links}")
        
        if not links:
            logger.warning("No links found")
            return jsonify({'error': 'No links found', 'links': []}), 404
            
        response_data = {'links': links}
        logger.info(f"Sending response: {response_data}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        return jsonify({'error': str(e), 'links': []}), 500

if __name__ == '__main__':
    app.run(debug=True) 