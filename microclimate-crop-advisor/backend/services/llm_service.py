import os
import requests
import random
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN', '')
        self.use_mock = not self.github_token
        self.api_url = "https://models.inference.ai.azure.com/chat/completions"
        self.model = "gpt-4o"
        
        if self.github_token:
            print("✅ GitHub AI is enabled - using REAL AI responses!")
        else:
            print("⚠️ No GitHub token found - using MOCK responses")
            print("   Get free token from: https://github.com/settings/tokens")
    
    def get_crop_advice(self, user_message, context):
        if self.use_mock:
            return self._get_mock_advice(user_message, context)
        
        try:
            system_prompt = self._build_system_prompt(context)
            
            headers = {
                "Authorization": f"Bearer {self.github_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.7,
                "max_tokens": 500
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return data['choices'][0]['message']['content']
            else:
                print(f"AI API Error: {response.status_code}")
                return self._get_mock_advice(user_message, context)
                
        except Exception as e:
            print(f"AI Error: {e}")
            return self._get_mock_advice(user_message, context)
    
    def generate_complete_analysis(self, weather_data, prediction):
        if self.use_mock:
            return self._get_mock_analysis(weather_data, prediction)
        
        try:
            prompt = f"""
            Based on the following microclimate data and crop prediction, provide a comprehensive analysis:
            
            Weather Conditions:
            - Temperature: {weather_data['temperature']}°C
            - Humidity: {weather_data['humidity']}%
            - Rainfall: {weather_data['rainfall']}mm
            - Wind Speed: {weather_data['wind_speed']} km/h
            - Cloud Cover: {weather_data['cloud_cover']}%
            - Location: {weather_data['location']}
            
            Crop Prediction:
            - Recommended Crop: {prediction['recommended_crop']}
            - Suitability Score: {prediction['suitability_score']:.0%}
            
            Please provide:
            1. Analysis of current microclimate conditions
            2. Why this crop is suitable
            3. Specific recommendations for planting and care
            4. Potential challenges and mitigation strategies
            """
            
            headers = {
                "Authorization": f"Bearer {self.github_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are an expert agricultural advisor specializing in microclimate analysis."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 800
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return data['choices'][0]['message']['content']
            else:
                return self._get_mock_analysis(weather_data, prediction)
                
        except Exception as e:
            return self._get_mock_analysis(weather_data, prediction)
    
    def _build_system_prompt(self, context):
        prompt = """You are an expert agricultural advisor specializing in microclimate conditions and crop management. 
        Provide practical, actionable advice based on the current conditions."""
        
        if context.get('weather'):
            w = context['weather']
            prompt += f"\n\nCurrent conditions: {w.get('temperature', '?')}°C, {w.get('humidity', '?')}% humidity, {w.get('conditions', 'unknown')}"
        
        if context.get('prediction'):
            prompt += f"\n\nRecommended crop: {context['prediction'].get('recommended_crop', 'Not specified')}"
        
        return prompt
    
    def _get_mock_advice(self, user_message, context):
        responses = [
            "Based on current conditions, I recommend checking soil moisture before planting. Well-drained soil with organic matter will give the best results.",
            "For optimal growth, consider using drip irrigation to maintain consistent soil moisture. This also helps prevent fungal diseases.",
            "Monitor weather forecasts for the next 5 days. If rain is expected, adjust your planting schedule accordingly.",
            "Apply a balanced fertilizer before planting. A 10-10-10 NPK ratio works well for most crops in this region.",
            "Consider mulching around plants to retain soil moisture and suppress weed growth.",
            "Test your soil pH before planting. Most crops prefer slightly acidic to neutral soil (6.0-7.0)."
        ]
        return random.choice(responses)
    
    def _get_mock_analysis(self, weather_data, prediction):
        return f"""
        🌾 **Microclimate Analysis Report**
        
        **Location:** {weather_data['location']}
        **Current Conditions:** {weather_data['temperature']}°C, {weather_data['humidity']}% humidity
        **Wind Speed:** {weather_data['wind_speed']} km/h
        **Cloud Cover:** {weather_data['cloud_cover']}%
        
        **Recommended Crop:** {prediction['recommended_crop']}
        **Suitability Score:** {prediction['suitability_score']*100:.0f}%
        **Confidence:** {prediction['confidence']*100:.0f}%
        
        **Key Recommendations:**
        {chr(10).join(f'• {rec}' for rec in prediction.get('recommendations', ['Prepare soil with organic matter', 'Monitor soil moisture regularly', 'Apply balanced fertilizer'])[:3])}
        
        **Next Steps:**
        • Begin soil preparation within the next 3-5 days
        • Install moisture sensors for optimal irrigation
        • Set up weather monitoring for early warning of adverse conditions
        
        For more detailed advice, please ask specific questions about planting, irrigation, or pest management.
        """