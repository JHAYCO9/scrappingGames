from flask import Flask, jsonify
from SCRAP import scrape_matches
import os

app = Flask(__name__)

@app.route('/scrape')
def scrape():
    data = scrape_matches()
    return jsonify(data)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
