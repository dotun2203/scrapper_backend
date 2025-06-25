from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from scraper.scrape_nysc import scrape_nysc
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "✅ NYSC Scraper is live and ready!"

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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)