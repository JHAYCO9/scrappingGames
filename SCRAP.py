import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/scrape', methods=['GET'])
def scrape_matches():
    url = 'https://www.besoccer.com'
    response = requests.get(url)
    
    result = {"leagues": []}
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        paneles = soup.find_all('div', class_='panel-head')

        if not paneles:
            return jsonify({"error": "No se encontraron ligas."})
        
        for panel in paneles:
            titulo_div = panel.find('div', class_='panel-title')
            if not titulo_div:
                continue
                
            nombre_liga = titulo_div.find('span').text.strip() if titulo_div else "Liga desconocida"
            logo_liga = titulo_div.find('img')['src'] if titulo_div and titulo_div.find('img') else ""

            contenedor_partidos = panel.find_next_sibling('div')
            if not contenedor_partidos:
                continue

            partidos = contenedor_partidos.find_all('a', class_='match-link')
            if not partidos:
                continue
                
            league_data = {
                "name": nombre_liga,
                "logo": logo_liga,
                "matches": []
            }

            for partido in partidos:    
                match_href = partido['href']
                
                equipos = partido.find_all('div', class_='team-info')

                if len(equipos) >= 2:
                    local_div = equipos[0]
                    visitante_div = equipos[1]

                    nombre_local = local_div.find('div', class_='team-name').text.strip()
                    logo_local = local_div.find('img')['src'] if local_div.find('img') else ""

                    nombre_visitante = visitante_div.find('div', class_='team-name').text.strip()
                    logo_visitante = visitante_div.find('img')['src'] if visitante_div.find('img') else ""
                else:
                    continue

                marcador_div = partido.find('div', class_='marker')
                tiempo = ""
                estado = "scheduled"
                marcador = ""
                
                if marcador_div:
                    tiempo_tag = partido.find('span', class_='tag-nobg live')
                    if tiempo_tag:
                        estado = "live"
                        tiempo = tiempo_tag.find('b').text.strip()
                        marcador = marcador_div.get_text(strip=True)
                    else:
                        hora = marcador_div.find('p', class_='match_hour time')
                        if hora:
                            tiempo = hora.text.strip()
                            estado = "scheduled"
                        else:
                            marcador = marcador_div.get_text(strip=True)
                            estado = "finished"
                
                today = datetime.now().strftime('%Y-%m-%d')
                
                match_data = {
                    "href": match_href,
                    "homeTeam": {
                        "name": nombre_local,
                        "logo": logo_local
                    },
                    "awayTeam": {
                        "name": nombre_visitante,
                        "logo": logo_visitante
                    },
                    "date": today,
                    "status": estado,
                }
                
                if estado == "live":
                    match_data["currentTime"] = tiempo
                    match_data["score"] = marcador
                elif estado == "scheduled":
                    match_data["time"] = tiempo
                else:
                    match_data["score"] = marcador
                
                league_data["matches"].append(match_data)
                
            if league_data["matches"]:
                result["leagues"].append(league_data)
            
        return jsonify(result)
    else:
        return jsonify({"error": f"Error al obtener la página. Código: {response.status_code}"}), 400

@app.route('/scrape_match', methods=['POST'])
def scrape_match():
    data = request.get_json()
    match_url = data.get('url')
    
    if not match_url:
        return jsonify({"error": "URL no proporcionada"}), 400
    
    response = requests.get(match_url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        match_info = {
            "homeTeam": {},
            "awayTeam": {},
            "matchDetails": {},
            "probabilities": {}
        }
        
        # Obtener el contenedor principal del partido
        match_div = soup.find('div', class_='info match-link')
        
        if not match_div:
            return jsonify({"error": "No se encontró la información del partido"}), 404
        
        # Información de los equipos
        home_team = match_div.find('div', class_='team match-team left')
        away_team = match_div.find('div', class_='team match-team right')
        
        if home_team and away_team:
            # Equipo local
            match_info["homeTeam"]["name"] = home_team.find('p', class_='name').text.strip()
            match_info["homeTeam"]["logo"] = home_team.find('img')['src'] if home_team.find('img') else ""
            match_info["homeTeam"]["yellowCards"] = home_team.find('span', class_='yc').text.strip() if home_team.find('span', class_='yc') else "0"
            match_info["homeTeam"]["possession"] = home_team.find('span', class_='posesion-perc').text.strip() if home_team.find('span', class_='posesion-perc') else "0%"
            
            # Equipo visitante
            match_info["awayTeam"]["name"] = away_team.find('p', class_='name').text.strip()
            match_info["awayTeam"]["logo"] = away_team.find('img')['src'] if away_team.find('img') else ""
            match_info["awayTeam"]["yellowCards"] = away_team.find('span', class_='yc').text.strip() if away_team.find('span', class_='yc') else "0"
            match_info["awayTeam"]["possession"] = away_team.find('span', class_='posesion-perc').text.strip() if away_team.find('span', class_='posesion-perc') else "0%"
        
        # Marcador
        marker = match_div.find('div', class_='marker')
        if marker:
            score_div = marker.find('div', class_='data')
            if score_div:
                match_info["matchDetails"]["score"] = score_div.get_text(strip=True)
        
        # Estado del partido
        status_tag = match_div.find('div', class_='tag')
        if status_tag:
            match_info["matchDetails"]["status"] = status_tag.text.strip()
        
        # Fecha y hora del partido
        date_div = match_div.find('div', class_='date header-match-date')
        if date_div:
            match_info["matchDetails"]["dateTime"] = date_div.text.strip()
        
        # Probabilidades
        elo_bar = soup.find('div', class_='elo-bar-content')
        if elo_bar:
            team1_label = elo_bar.find('div', class_='team1-c')
            draw_label = elo_bar.find('div', class_='color-grey2')
            team2_label = elo_bar.find('div', class_='team2-c')
            
            if team1_label:
                match_info["probabilities"]["home"] = team1_label.find('div').text.strip()
            if draw_label:
                match_info["probabilities"]["draw"] = draw_label.find('div').text.strip()
            if team2_label:
                match_info["probabilities"]["away"] = team2_label.find('div').text.strip()
            
            # Valores numéricos de las probabilidades
            team1_bar = elo_bar.find('div', class_='team1-bar')
            draw_bar = elo_bar.find('div', class_='draw-bar')
            team2_bar = elo_bar.find('div', class_='team2-bar')
            
            if team1_bar and 'style' in team1_bar.attrs:
                try:
                    match_info["probabilities"]["homeValue"] = float(team1_bar['style'].split(':')[1].replace('%', '').strip())
                except:
                    match_info["probabilities"]["homeValue"] = 0
            
            if draw_bar and 'style' in draw_bar.attrs:
                try:
                    match_info["probabilities"]["drawValue"] = float(draw_bar['style'].split(':')[1].replace('%', '').strip())
                except:
                    match_info["probabilities"]["drawValue"] = 0
            
            if team2_bar and 'style' in team2_bar.attrs:
                try:
                    match_info["probabilities"]["awayValue"] = float(team2_bar['style'].split(':')[1].replace('%', '').strip())
                except:
                    match_info["probabilities"]["awayValue"] = 0
        
        return jsonify(match_info)
    else:
        return jsonify({"error": f"Error al obtener la página del partido. Código: {response.status_code}"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)