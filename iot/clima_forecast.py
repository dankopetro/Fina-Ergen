import urllib.request
import json
import socket
import sys
from datetime import datetime, timedelta

# Script para obtener pronóstico del clima (5 días / 3 horas)
socket.setdefaulttimeout(10)

if len(sys.argv) > 2:
    API_KEY = sys.argv[1]
    CITY_ID = sys.argv[2]
else:
    print(json.dumps({"cod": 400, "message": "Missing API Key or City ID"}))
    sys.exit(1)

# Usamos endpoint forecast
URL = f"http://api.openweathermap.org/data/2.5/forecast?id={CITY_ID}&appid={API_KEY}&units=metric&lang=es"

try:
    req = urllib.request.Request(URL)
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
        
        # Procesar datos crudos para simplificar (agrupar por día)
        # OWM devuelve 40 items (5 días * 8 intervalos de 3h)
        # Queremos los próximos 3 días.
        
        forecast_by_day = {}
        
        for item in data.get('list', []):
            dt_txt = item.get('dt_txt') # "2023-10-25 12:00:00"
            date_str = dt_txt.split(' ')[0]
            
            # Ignorar hoy
            today = datetime.now().strftime('%Y-%m-%d')
            if date_str == today:
                 continue

            if date_str not in forecast_by_day:
                forecast_by_day[date_str] = {
                    'temps': [],
                    'icons': [],
                    'dt': item.get('dt')
                }
            
            forecast_by_day[date_str]['temps'].append(item['main']['temp'])
            # Guardamos el icon del mediodía preferiblemente, o todos para sacar moda
            hour = int(dt_txt.split(' ')[1].split(':')[0])
            if 11 <= hour <= 14:
                forecast_by_day[date_str]['noon_icon'] = item['weather'][0]['id']
            forecast_by_day[date_str]['icons'].append(item['weather'][0]['id'])
        
        # Formatear salida para UI
        # Estructura: [ { day: 'LUN', min: 20, max: 30, code: 800 }, ... ]
        final_forecast = []
        days_map = ['DOM', 'LUN', 'MAR', 'MIÉ', 'JUE', 'VIE', 'SÁB']
        
        count = 0
        for date_k, vals in forecast_by_day.items():
            if count >= 3: break # Solo 3 días
            
            min_t = min(vals['temps'])
            max_t = max(vals['temps'])
            
            # Usar icono del mediodía o el primero
            code = vals.get('noon_icon', vals['icons'][0])
            
            # Obtener día de la semana
            dt_obj = datetime.strptime(date_k, '%Y-%m-%d')
            day_name = days_map[int(dt_obj.strftime('%w'))]
            
            final_forecast.append({
                'day': day_name,
                'min': round(min_t),
                'max': round(max_t),
                'code': code
            })
            count += 1
            
        print(json.dumps(final_forecast))

except Exception as e:
    print(json.dumps({"error": str(e)}))
