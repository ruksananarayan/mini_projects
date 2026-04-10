from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from services.prediction_service import PredictionService
from services.llm_service import LLMService
from models.weather_service import WeatherService

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize services
weather_service = WeatherService()
prediction_service = PredictionService()
llm_service = LLMService()

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Microclimate Crop Advisor is running'})

@app.route('/api/weather/current', methods=['GET'])
def get_current_weather():
    try:
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        
        if not lat or not lon:
            return jsonify({'error': 'Latitude and longitude are required'}), 400
        
        weather_data = weather_service.get_current_weather(float(lat), float(lon))
        return jsonify(weather_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict/crop', methods=['POST'])
def predict_crop():
    try:
        data = request.json
        
        if 'weather_data' not in data:
            lat = data.get('lat')
            lon = data.get('lon')
            if lat and lon:
                weather_data = weather_service.get_current_weather(float(lat), float(lon))
            else:
                return jsonify({'error': 'Weather data or location coordinates required'}), 400
        else:
            weather_data = data['weather_data']
        
        prediction = prediction_service.predict_optimal_crop(weather_data)
        return jsonify(prediction)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/advisor/chat', methods=['POST'])
def advisor_chat():
    try:
        data = request.json
        user_message = data.get('message')
        context = data.get('context', {})
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        if context.get('lat') and context.get('lon'):
            weather_data = weather_service.get_current_weather(
                float(context['lat']), float(context['lon'])
            )
            context['weather'] = weather_data
        
        response = llm_service.get_crop_advice(user_message, context)
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/advisor/complete-analysis', methods=['POST'])
def complete_analysis():
    try:
        data = request.json
        lat = data.get('lat')
        lon = data.get('lon')
        
        if not lat or not lon:
            return jsonify({'error': 'Location coordinates required'}), 400
        
        weather_data = weather_service.get_current_weather(float(lat), float(lon))
        prediction = prediction_service.predict_optimal_crop(weather_data)
        analysis = llm_service.generate_complete_analysis(weather_data, prediction)
        
        return jsonify({
            'location': {'lat': lat, 'lon': lon},
            'weather': weather_data,
            'prediction': prediction,
            'analysis': analysis
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)