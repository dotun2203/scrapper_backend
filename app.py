from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from scraper.scrape_nysc import scrape_nysc

app = Flask(__name__)
CORS(app)

@app.route('/api/scrape', methods=['POST'])
def scrape():
    year = request.json.get('year')
    if not year:
        return jsonify({"error": "Year is required"}), 400
    try:
        filename = scrape_nysc(year)
        return jsonify({"message":"scraping completed", "file": filename})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    return send_file(f"./outputs/{filename}", as_attachment=True)