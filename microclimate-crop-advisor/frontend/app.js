class MicroclimateAdvisor {
    constructor() {
        this.currentLocation = null;
        this.currentWeather = null;
        this.currentPrediction = null;
        this.apiBaseUrl = 'http://localhost:5000/api';
        
        this.initializeEventListeners();
    }
    
    initializeEventListeners() {
        document.getElementById('getCurrentLocationBtn').addEventListener('click', () => this.getCurrentLocation());
        document.getElementById('searchLocationBtn').addEventListener('click', () => this.searchLocation());
        document.getElementById('analyzeBtn').addEventListener('click', () => this.getCompleteAnalysis());
        document.getElementById('sendBtn').addEventListener('click', () => this.sendMessage());
        document.getElementById('clearChatBtn').addEventListener('click', () => this.clearChat());
        
        // Quick action buttons
        document.querySelectorAll('.quick-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.getElementById('chatInput').value = btn.dataset.question;
                this.sendMessage();
            });
        });
        
        // Auto-resize textarea
        const textarea = document.getElementById('chatInput');
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 100) + 'px';
        });
        
        // Enter key for sending (Shift+Enter for new line)
        textarea.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        document.getElementById('cityInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.searchLocation();
        });
    }
    
    async getCurrentLocation() {
        if (!navigator.geolocation) {
            this.showStatus('Geolocation is not supported by your browser', 'error');
            return;
        }
        
        this.showStatus('📍 Getting your location...', 'info');
        
        navigator.geolocation.getCurrentPosition(
            async (position) => {
                this.currentLocation = {
                    lat: position.coords.latitude,
                    lon: position.coords.longitude
                };
                this.showStatus(`✅ Location obtained: ${this.currentLocation.lat.toFixed(2)}°, ${this.currentLocation.lon.toFixed(2)}°`, 'success');
                await this.fetchAllData();
            },
            (error) => {
                this.showStatus('❌ Error getting location: ' + error.message, 'error');
            }
        );
    }
    
    async searchLocation() {
        const city = document.getElementById('cityInput').value.trim();
        const country = document.getElementById('countryInput').value.trim();
        
        if (!city) {
            this.showStatus('Please enter a city name', 'error');
            return;
        }
        
        this.showStatus(`🔍 Searching for ${city}${country ? ', ' + country : ''}...`, 'info');
        
        try {
            // Using OpenStreetMap Nominatim for geocoding (free, no API key)
            const searchQuery = `${city}${country ? ', ' + country : ''}`;
            const response = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(searchQuery)}&format=json&limit=1`);
            const data = await response.json();
            
            if (data && data.length > 0) {
                this.currentLocation = {
                    lat: parseFloat(data[0].lat),
                    lon: parseFloat(data[0].lon),
                    name: data[0].display_name
                };
                this.showStatus(`✅ Found: ${data[0].display_name}`, 'success');
                await this.fetchAllData();
            } else {
                this.showStatus('❌ Location not found. Please try a different search.', 'error');
            }
        } catch (error) {
            console.error('Geocoding error:', error);
            this.showStatus('❌ Error searching location. Please try again.', 'error');
        }
    }
    
    async fetchAllData() {
        await this.fetchWeatherData();
        await this.fetchCropPrediction();
        this.updateSoilAnalysis();
    }
    
    async fetchWeatherData() {
        if (!this.currentLocation) return;
        
        try {
            const response = await fetch(
                `${this.apiBaseUrl}/weather/current?lat=${this.currentLocation.lat}&lon=${this.currentLocation.lon}`
            );
            
            if (!response.ok) throw new Error('Failed to fetch weather data');
            
            this.currentWeather = await response.json();
            this.displayWeatherData();
        } catch (error) {
            console.error('Error fetching weather:', error);
            this.displayWeatherError(error.message);
        }
    }
    
    async fetchCropPrediction() {
        if (!this.currentLocation) return;
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/predict/crop`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    lat: this.currentLocation.lat,
                    lon: this.currentLocation.lon
                })
            });
            
            if (!response.ok) throw new Error('Failed to fetch prediction');
            
            this.currentPrediction = await response.json();
            this.displayPredictionData();
        } catch (error) {
            console.error('Error fetching prediction:', error);
            this.displayPredictionError(error.message);
        }
    }
    
    updateSoilAnalysis() {
        if (!this.currentWeather || !this.currentPrediction) return;
        
        const soilDiv = document.getElementById('soilData');
        const w = this.currentWeather;
        const p = this.currentPrediction;
        
        // Calculate soil moisture recommendation
        let moistureRecommendation = '';
        if (w.humidity < 40) {
            moistureRecommendation = 'Low soil moisture detected. Increase irrigation frequency.';
        } else if (w.humidity > 80) {
            moistureRecommendation = 'High humidity. Ensure good drainage to prevent root rot.';
        } else {
            moistureRecommendation = 'Optimal moisture conditions. Maintain current irrigation schedule.';
        }
        
        // Calculate temperature suitability
        let tempAdvice = '';
        if (w.temperature < 15) {
            tempAdvice = 'Cool temperatures. Consider using row covers or greenhouse.';
        } else if (w.temperature > 35) {
            tempAdvice = 'High temperatures. Provide shade and increase irrigation.';
        } else {
            tempAdvice = 'Ideal temperature range for most crops.';
        }
        
        soilDiv.innerHTML = `
            <div class="soil-metrics">
                <div class="metric-card">
                    <i class="fas fa-tachometer-alt"></i>
                    <h4>Soil Moisture</h4>
                    <p class="value">${w.humidity}%</p>
                    <small>${moistureRecommendation}</small>
                </div>
                <div class="metric-card">
                    <i class="fas fa-temperature-high"></i>
                    <h4>Soil Temperature</h4>
                    <p class="value">${w.temperature}°C</p>
                    <small>${tempAdvice}</small>
                </div>
                <div class="metric-card">
                    <i class="fas fa-wind"></i>
                    <h4>Wind Exposure</h4>
                    <p class="value">${w.wind_speed} km/h</p>
                    <small>${w.wind_speed > 30 ? 'High wind. Install windbreaks.' : 'Wind conditions favorable.'}</small>
                </div>
            </div>
            <div class="soil-recommendation">
                <h4><i class="fas fa-lightbulb"></i> Recommended Action</h4>
                <p>Based on current conditions, ${p.recommendations[0] || 'maintain standard farming practices.'}</p>
            </div>
        `;
    }
    
    displayWeatherData() {
        const weatherDiv = document.getElementById('weatherData');
        const w = this.currentWeather;
        
        const isRealData = w.temperature !== 22.5 || w.humidity !== 65;
        const badge = document.getElementById('dataSourceBadge');
        if (badge) {
            badge.textContent = isRealData ? '✓ Live Data' : '⚠ Demo Data';
            badge.style.background = isRealData ? '#2ecc71' : '#f39c12';
        }
        
        weatherDiv.innerHTML = `
            <div class="weather-details">
                <div class="weather-item">
                    <i class="fas fa-thermometer-half"></i>
                    <span class="label">Temperature</span>
                    <span class="value">${w.temperature}°C</span>
                </div>
                <div class="weather-item">
                    <i class="fas fa-tint"></i>
                    <span class="label">Humidity</span>
                    <span class="value">${w.humidity}%</span>
                </div>
                <div class="weather-item">
                    <i class="fas fa-cloud-rain"></i>
                    <span class="label">Rainfall</span>
                    <span class="value">${w.rainfall} mm</span>
                </div>
                <div class="weather-item">
                    <i class="fas fa-wind"></i>
                    <span class="label">Wind Speed</span>
                    <span class="value">${w.wind_speed} km/h</span>
                </div>
                <div class="weather-item">
                    <i class="fas fa-cloud-sun"></i>
                    <span class="label">Cloud Cover</span>
                    <span class="value">${w.cloud_cover}%</span>
                </div>
                <div class="weather-item">
                    <i class="fas fa-map-marker-alt"></i>
                    <span class="label">Location</span>
                    <span class="value">${w.location}</span>
                </div>
            </div>
            <div class="weather-condition">
                <i class="fas ${this.getWeatherIcon(w.conditions)}"></i>
                <p>${w.conditions}</p>
                <small>Last updated: ${new Date(w.timestamp).toLocaleString()}</small>
            </div>
        `;
    }
    
    getWeatherIcon(condition) {
        const conditionLower = condition.toLowerCase();
        if (conditionLower.includes('rain')) return 'fa-cloud-rain';
        if (conditionLower.includes('cloud')) return 'fa-cloud';
        if (conditionLower.includes('clear')) return 'fa-sun';
        return 'fa-cloud-sun';
    }
    
    displayPredictionData() {
        const predictionDiv = document.getElementById('predictionData');
        const p = this.currentPrediction;
        
        const suitabilityPercent = (p.suitability_score * 100).toFixed(0);
        let suitabilityClass = '';
        let suitabilityMessage = '';
        
        if (p.suitability_score > 0.7) {
            suitabilityClass = 'high';
            suitabilityMessage = 'Excellent conditions for this crop!';
        } else if (p.suitability_score > 0.4) {
            suitabilityClass = 'medium';
            suitabilityMessage = 'Moderate suitability. Follow recommendations for best results.';
        } else {
            suitabilityClass = 'low';
            suitabilityMessage = 'Challenging conditions. Consider alternative crops.';
        }
        
        predictionDiv.innerHTML = `
            <div class="crop-result">
                <i class="fas fa-seedling" style="font-size: 3rem;"></i>
                <div class="crop-name">${p.recommended_crop}</div>
                <div class="suitability-score">
                    <span class="suitability-${suitabilityClass}">${suitabilityPercent}% Suitability</span>
                    <p><small>${suitabilityMessage}</small></p>
                </div>
                <div class="score-bar">
                    <div class="score-fill" style="width: ${suitabilityPercent}%"></div>
                </div>
            </div>
            <div class="recommendations">
                <h4><i class="fas fa-list-check"></i> Key Recommendations</h4>
                <ul class="recommendations-list">
                    ${p.recommendations.map(rec => `<li><i class="fas fa-check-circle"></i> ${rec}</li>`).join('')}
                </ul>
            </div>
            <div class="alternative-crops">
                <h4><i class="fas fa-chart-simple"></i> Alternative Crops</h4>
                <div class="alternatives">
                    ${Object.entries(p.all_probabilities)
                        .filter(([crop]) => crop !== p.recommended_crop)
                        .slice(0, 3)
                        .map(([crop, prob]) => `
                            <div class="alternative-item">
                                <span>${crop}</span>
                                <div class="alt-bar">
                                    <div class="alt-fill" style="width: ${(prob * 100).toFixed(0)}%"></div>
                                </div>
                                <span>${(prob * 100).toFixed(0)}%</span>
                            </div>
                        `).join('')}
                </div>
            </div>
        `;
    }
    
    async getCompleteAnalysis() {
        if (!this.currentLocation) {
            this.showStatus('Please select a location first', 'error');
            return;
        }
        
        const analysisDiv = document.getElementById('analysisData');
        analysisDiv.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i><p>Analyzing microclimate data...</p></div>';
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/advisor/complete-analysis`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    lat: this.currentLocation.lat,
                    lon: this.currentLocation.lon
                })
            });
            
            if (!response.ok) throw new Error('Failed to get analysis');
            
            const data = await response.json();
            this.displayAnalysis(data.analysis);
        } catch (error) {
            console.error('Error getting analysis:', error);
            analysisDiv.innerHTML = `<div class="error">❌ Error: ${error.message}</div>`;
        }
    }
    
    displayAnalysis(analysis) {
        const analysisDiv = document.getElementById('analysisData');
        
        // Parse and format analysis content
        const sections = analysis.split(/\d\./).filter(s => s.trim());
        
        analysisDiv.innerHTML = `
            <div class="analysis-sections">
                ${sections.map((section, index) => `
                    <div class="analysis-section">
                        <h4><i class="fas fa-chart-line"></i> ${index === 0 ? 'Microclimate Analysis' : index === 1 ? 'Crop Suitability' : index === 2 ? 'Action Plan' : 'Risk Management'}</h4>
                        <p>${section.trim()}</p>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    async sendMessage() {
        const input = document.getElementById('chatInput');
        const message = input.value.trim();
        
        if (!message) return;
        
        this.addMessageToChat(message, 'user');
        input.value = '';
        input.style.height = 'auto';
        
        this.showTypingIndicator(true);
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/advisor/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: message,
                    context: {
                        lat: this.currentLocation?.lat,
                        lon: this.currentLocation?.lon,
                        weather: this.currentWeather,
                        prediction: this.currentPrediction
                    }
                })
            });
            
            if (!response.ok) throw new Error('Failed to get response');
            
            const data = await response.json();
            this.showTypingIndicator(false);
            this.addMessageToChat(data.response, 'bot');
        } catch (error) {
            console.error('Error sending message:', error);
            this.showTypingIndicator(false);
            this.addMessageToChat('Sorry, I encountered an error. Please try again.', 'bot');
        }
    }
    
    addMessageToChat(message, sender) {
        const chatDiv = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        messageDiv.innerHTML = `
            <div class="message-avatar">
                <i class="fas ${sender === 'user' ? 'fa-user' : 'fa-robot'}"></i>
            </div>
            <div class="message-content">
                <div class="message-header">
                    <span class="sender">${sender === 'user' ? 'You' : 'AI Advisor'}</span>
                    <span class="time">${time}</span>
                </div>
                <p>${this.formatMessage(message)}</p>
            </div>
        `;
        
        chatDiv.appendChild(messageDiv);
        chatDiv.scrollTop = chatDiv.scrollHeight;
    }
    
    formatMessage(message) {
        // Convert markdown-like formatting
        return message
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
    }
    
    showTypingIndicator(show) {
        const indicator = document.getElementById('typingIndicator');
        if (show) {
            indicator.classList.add('active');
        } else {
            indicator.classList.remove('active');
        }
    }
    
    clearChat() {
        const chatDiv = document.getElementById('chatMessages');
        chatDiv.innerHTML = `
            <div class="message bot">
                <div class="message-avatar">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="message-content">
                    <div class="message-header">
                        <span class="sender">AI Advisor</span>
                        <span class="time">Just now</span>
                    </div>
                    <p>Chat cleared! How can I help you with your crops today?</p>
                </div>
            </div>
        `;
        this.showStatus('Chat history cleared', 'info');
    }
    
    displayWeatherError(error) {
        const weatherDiv = document.getElementById('weatherData');
        weatherDiv.innerHTML = `<div class="error">❌ Error loading weather data: ${error}</div>`;
    }
    
    displayPredictionError(error) {
        const predictionDiv = document.getElementById('predictionData');
        predictionDiv.innerHTML = `<div class="error">❌ Error loading prediction: ${error}</div>`;
    }
    
    showStatus(message, type) {
        const statusDiv = document.getElementById('locationStatus');
        statusDiv.className = `status-message ${type}`;
        statusDiv.innerHTML = `<i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i> ${message}`;
        
        setTimeout(() => {
            statusDiv.innerHTML = '';
            statusDiv.className = 'status-message';
        }, 5000);
    }
}

// Initialize the application
const app = new MicroclimateAdvisor();