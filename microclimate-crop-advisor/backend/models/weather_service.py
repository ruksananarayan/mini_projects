import requests
from datetime import datetime

class WeatherService:
    def __init__(self):
        # Using Open-Meteo - COMPLETELY FREE, NO API KEY NEEDED!
        self.base_url = "https://api.open-meteo.com/v1/forecast"
    
    def get_current_weather(self, lat, lon):
        """Fetch REAL weather data - Free, no API key required!"""
        try:
            print(f"📍 Fetching weather for: {lat}, {lon}")
            
            params = {
                "latitude": lat,
                "longitude": lon,
                "current": [
                    "temperature_2m",
                    "relative_humidity_2m",
                    "precipitation",
                    "wind_speed_10m",
                    "cloud_cover",
                    "pressure_msl"
                ],
                "hourly": ["temperature_2m", "precipitation_probability"],
                "daily": ["temperature_2m_max", "temperature_2m_min"],
                "timezone": "auto"
            }
            
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            current = data.get("current", {})
            print(f"✅ Got real weather: {current.get('temperature_2m')}°C")
            
            # Get location name
            location_name = self._get_location_name(lat, lon)
            
            return {
                'temperature': current.get('temperature_2m', 0),
                'humidity': current.get('relative_humidity_2m', 0),
                'pressure': current.get('pressure_msl', 1013),
                'rainfall': current.get('precipitation', 0),
                'wind_speed': current.get('wind_speed_10m', 0),
                'cloud_cover': current.get('cloud_cover', 0),
                'timestamp': datetime.now().isoformat(),
                'location': location_name,
                'conditions': self._get_weather_condition(
                    current.get('cloud_cover', 0),
                    current.get('precipitation', 0)
                ),
                'forecast': self._get_forecast(lat, lon)
            }
            
        except Exception as e:
            print(f"❌ Weather API error: {e}")
            return self._get_fallback_data(lat, lon)
    
    def _get_forecast(self, lat, lon):
        """Get 24-hour forecast"""
        try:
            params = {
                "latitude": lat,
                "longitude": lon,
                "hourly": ["temperature_2m", "precipitation_probability"],
                "forecast_days": 1,
                "timezone": "auto"
            }
            response = requests.get(self.base_url, params=params)
            data = response.json()
            
            hourly = data.get("hourly", {})
            times = hourly.get("time", [])[:8]
            temps = hourly.get("temperature_2m", [])[:8]
            
            return [{'time': times[i], 'temp': temps[i], 'conditions': 'Forecast'} 
                    for i in range(len(times))]
        except:
            return []
    
    def _get_location_name(self, lat, lon):
        """Free reverse geocoding - NO API key!"""
        try:
            url = f"https://api.bigdatacloud.net/data/reverse-geocode-client"
            params = {"latitude": lat, "longitude": lon, "localityLanguage": "en"}
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            
            city = data.get('city', '')
            country = data.get('countryName', '')
            
            if city and country:
                return f"{city}, {country}"
            return f"Location ({lat:.2f}, {lon:.2f})"
        except:
            return f"Location ({lat:.2f}, {lon:.2f})"
    
    def _get_weather_condition(self, cloud_cover, rainfall):
        if rainfall > 0:
            return "Rainy"
        elif cloud_cover < 20:
            return "Clear sky"
        elif cloud_cover < 50:
            return "Partly cloudy"
        elif cloud_cover < 80:
            return "Mostly cloudy"
        return "Overcast"
    
    def _get_fallback_data(self, lat, lon):
        """Fallback if API fails"""
        return {
            'temperature': 22.5,
            'humidity': 65,
            'pressure': 1013,
            'rainfall': 0,
            'wind_speed': 12,
            'cloud_cover': 30,
            'timestamp': datetime.now().isoformat(),
            'location': f'Location ({lat:.2f}, {lon:.2f})',
            'conditions': 'clear sky',
            'forecast': []
        }