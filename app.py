from flask import Flask, jsonify
from SCRAP import scrape_matches  # Asegúrate de que el archivo se llame exactamente SCRAP.py (mayúsculas)

import os

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"message": "API de scrapping funcionando. Usa /scrape para obtener datos."})

@app.route('/scrape')
def scrape():
    data = scrape_matches()
    return jsonify(data)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Puerto definido por Railway
    app.run(host="0.0.0.0", port=port)
