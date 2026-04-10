from models.crop_model import CropPredictionModel

class PredictionService:
    def __init__(self):
        self.crop_model = CropPredictionModel()
    
    def predict_optimal_crop(self, weather_data):
        """Predict optimal crop based on weather conditions"""
        features = [
            weather_data.get('temperature', 20),
            weather_data.get('humidity', 60),
            weather_data.get('rainfall', 50),
            weather_data.get('wind_speed', 10),
            weather_data.get('cloud_cover', 30)
        ]
        
        prediction = self.crop_model.predict(features)
        prediction['suitability_score'] = self._calculate_suitability(weather_data, prediction['recommended_crop'])
        prediction['recommendations'] = self._generate_recommendations(weather_data, prediction['recommended_crop'])
        
        return prediction
    
    def _calculate_suitability(self, weather_data, crop):
        scores = {
            'Rice': 0.85, 'Wheat': 0.75, 'Maize': 0.80,
            'Soybean': 0.70, 'Cotton': 0.65, 'Sugarcane': 0.90
        }
        
        base_score = scores.get(crop, 0.70)
        
        if weather_data.get('temperature', 20) < 10:
            base_score *= 0.8
        if weather_data.get('rainfall', 0) > 150:
            base_score *= 0.9
            
        return min(1.0, base_score)
    
    def _generate_recommendations(self, weather_data, crop):
        recommendations = []
        
        temp = weather_data.get('temperature', 20)
        humidity = weather_data.get('humidity', 60)
        
        if temp < 15:
            recommendations.append("Consider using frost protection measures")
        elif temp > 30:
            recommendations.append("Increase irrigation frequency due to high temperatures")
        
        if humidity < 40:
            recommendations.append("Implement additional irrigation to maintain soil moisture")
        elif humidity > 80:
            recommendations.append("Monitor for fungal diseases and ensure good air circulation")
        
        recommendations.append(f"Optimal planting depth for {crop}: 2-4 inches")
        recommendations.append("Apply organic fertilizer before planting")
        
        return recommendations[:4]