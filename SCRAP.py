import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

def scrape_matches():
    url = 'https://www.besoccer.com'
    response = requests.get(url)
    
    result = {"leagues": []}
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        paneles = soup.find_all('div', class_='panel-head')

        if not paneles:
            return {"error": "No se encontraron ligas."}
        
        for panel in paneles:
            titulo_div = panel.find('div', class_='panel-title')
            if not titulo_div:
                continue
                
            nombre_liga = titulo_div.find('span').text.strip() if titulo_div else "Liga desconocida"
            logo_liga = titulo_div.find('img')['src'] if titulo_div and titulo_div.find('img') else ""

            contenedor_partidos = panel.find_next_sibling('div')
            if not contenedor_partidos:
                continue  # Omitir ligas sin partidos

            partidos = contenedor_partidos.find_all('a', class_='match-link')
            if not partidos:
                continue  # Omitir ligas vacías
                
            league_data = {
                "name": nombre_liga,
                "logo": logo_liga,
                "matches": []
            }

            for partido in partidos:    
                equipos = partido.find_all('div', class_='team-info')

                if len(equipos) >= 2:
                    local_div = equipos[0]
                    visitante_div = equipos[1]

                    nombre_local = local_div.find('div', class_='team-name').text.strip()
                    logo_local = local_div.find('img')['src'] if local_div.find('img') else ""

                    nombre_visitante = visitante_div.find('div', class_='team-name').text.strip()
                    logo_visitante = visitante_div.find('img')['src'] if visitante_div.find('img') else ""
                else:
                    continue  # Omitir si no hay ambos equipos

                marcador = partido.find('div', class_='marker')
                if marcador:
                    tiempo = marcador.get_text(strip=True)
                else:
                    hora = partido.find('p', class_='match_hour time')
                    tiempo = hora.text.strip() if hora else ""
                
                # Usar la fecha actual para el partido
                today = datetime.now().strftime('%Y-%m-%d')
                
                # Crear objeto de partido
                match_data = {
                    "homeTeam": {
                        "name": nombre_local,
                        "logo": logo_local
                    },
                    "awayTeam": {
                        "name": nombre_visitante,
                        "logo": logo_visitante
                    },
                    "time": tiempo,
                    "date": today,
                    "odds": {
                        "home": "1.95",  # Valores por defecto
                        "draw": "3.25",
                        "away": "3.60"
                    }
                }
                
                league_data["matches"].append(match_data)
                
            if league_data["matches"]:  # Solo agregar ligas que tienen partidos
                result["leagues"].append(league_data)
            
        return result
    else:
        return {"error": f"Error al obtener la página. Código de estado: {response.status_code}"}

if __name__ == "__main__":
    matches_data = scrape_matches()
    print(json.dumps(matches_data, ensure_ascii=False, indent=2))