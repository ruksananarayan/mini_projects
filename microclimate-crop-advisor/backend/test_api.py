# test_api.py
import requests
from datetime import datetime

def test_weather_api():
    # Test with Delhi coordinates
    lat, lon = 28.6139, 77.2090
    
    print("=" * 50)
    print("Testing Weather API...")
    print("=" * 50)
    
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ["temperature_2m", "relative_humidity_2m"],
        "timezone": "auto"
    }
    
    try:
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            current = data.get("current", {})
            
            temp = current.get("temperature_2m")
            humidity = current.get("relative_humidity_2m")
            
            print(f"✅ API IS WORKING!")
            print(f"📍 Location: Delhi, India")
            print(f"🌡️ REAL Temperature: {temp}°C")
            print(f"💧 REAL Humidity: {humidity}%")
            print(f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("\n✨ Your app is using REAL weather data!")
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print("⚠️ Your app is using DUMMY data")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("⚠️ Your app is using DUMMY data")

def test_github_ai():
    """Test if GitHub AI is working"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    token = os.getenv('GITHUB_TOKEN', '')
    
    print("\n" + "=" * 50)
    print("Testing GitHub AI API...")
    print("=" * 50)
    
    if not token:
        print("❌ No GitHub token found in .env file")
        print("⚠️ Your app is using MOCK AI responses")
        return
    
    url = "https://models.inference.ai.azure.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "user", "content": "Say 'AI is working'"}
        ],
        "max_tokens": 20
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ GitHub AI IS WORKING!")
            print(f"🤖 Response: {data['choices'][0]['message']['content']}")
            print("\n✨ Your app is using REAL AI responses!")
        else:
            print(f"❌ AI API Error: {response.status_code}")
            print("⚠️ Your app is using MOCK AI responses")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("⚠️ Your app is using MOCK AI responses")

if __name__ == "__main__":
    test_weather_api()
    test_github_ai()