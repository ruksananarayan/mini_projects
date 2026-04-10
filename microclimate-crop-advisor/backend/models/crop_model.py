import numpy as np
from sklearn.ensemble import RandomForestClassifier
import pickle
import os

class CropPredictionModel:
    def __init__(self):
        self.model = None
        self.crops = ['Rice', 'Wheat', 'Maize', 'Soybean', 'Cotton', 'Sugarcane']
        self._create_simulated_model()
    
    def _create_simulated_model(self):
        """Create a machine learning model for crop prediction"""
        np.random.seed(42)
        n_samples = 1000
        
        # Features: [temperature, humidity, rainfall, wind_speed, cloud_cover]
        X = np.random.rand(n_samples, 5)
        
        # Scale features to realistic ranges
        X[:, 0] = X[:, 0] * 30 + 5   # temperature: 5-35°C
        X[:, 1] = X[:, 1] * 80 + 20  # humidity: 20-100%
        X[:, 2] = X[:, 2] * 200      # rainfall: 0-200mm
        X[:, 3] = X[:, 3] * 50       # wind_speed: 0-50 km/h
        X[:, 4] = X[:, 4] * 100      # cloud_cover: 0-100%
        
        # Rule-based labeling
        y = []
        for features in X:
            temp, humidity, rainfall, wind, cloud = features
            
            if temp > 20 and humidity > 60 and rainfall > 50:
                y.append(0)  # Rice
            elif temp < 20 and humidity < 60:
                y.append(1)  # Wheat
            elif temp > 25 and rainfall < 100:
                y.append(2)  # Maize
            elif temp > 20 and rainfall > 30:
                y.append(3)  # Soybean
            elif temp > 25 and cloud < 50:
                y.append(4)  # Cotton
            else:
                y.append(5)  # Sugarcane
        
        # Train model
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X, np.array(y))
    
    def predict(self, features):
        """Predict crop based on features"""
        features_array = np.array(features).reshape(1, -1)
        prediction = self.model.predict(features_array)[0]
        probabilities = self.model.predict_proba(features_array)[0]
        
        return {
            'recommended_crop': self.crops[prediction],
            'confidence': float(max(probabilities)),
            'all_probabilities': {
                crop: float(prob) for crop, prob in zip(self.crops, probabilities)
            }
        }