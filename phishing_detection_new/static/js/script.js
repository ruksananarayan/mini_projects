class PhishingDetector {
    constructor() {
        this.totalScanned = 0;
        this.phishingDetected = 0;
        this.updateStats();
        this.bindEvents();
        this.checkHealth();
    }

    bindEvents() {
        document.getElementById('checkBtn').addEventListener('click', () => this.checkSingleUrl());
        document.getElementById('batchCheckBtn').addEventListener('click', () => this.checkBatchUrls());
        document.getElementById('trainBtn').addEventListener('click', () => this.trainModel());
        document.getElementById('clearBtn').addEventListener('click', () => this.clearResults());
        
        // Enter key support
        document.getElementById('urlInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.checkSingleUrl();
        });

        // Sample URL buttons
        document.querySelectorAll('.sample-url').forEach(button => {
            button.addEventListener('click', (e) => {
                const url = e.target.closest('.sample-url').dataset.url;
                document.getElementById('urlInput').value = url;
                this.checkSingleUrl();
            });
        });
    }

    async checkHealth() {
        try {
            const response = await fetch('/health');
            const data = await response.json();
            document.getElementById('modelStatus').textContent = data.model_trained ? 'Ready' : 'Training';
        } catch (error) {
            console.log('Health check failed:', error);
        }
    }

    async checkSingleUrl() {
        const urlInput = document.getElementById('urlInput');
        const url = urlInput.value.trim();
        
        if (!url) {
            this.showNotification('Please enter a URL to analyze', 'error');
            return;
        }

        await this.analyzeUrl(url);
    }

    async checkBatchUrls() {
        const textarea = document.getElementById('batchUrls');
        const urls = textarea.value.trim().split('\n').filter(url => url.trim());
        
        if (urls.length === 0) {
            this.showNotification('Please enter URLs to analyze', 'error');
            return;
        }

        if (urls.length > 10) {
            this.showNotification('Please limit to 10 URLs for batch analysis', 'warning');
            return;
        }

        this.showLoading('Analyzing multiple URLs...');
        
        try {
            const response = await fetch('/batch_predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ urls })
            });

            const data = await response.json();
            
            if (data.success) {
                this.displayBatchResults(data.results);
                this.updateStats(data.results.length, data.phishing_count);
                this.showNotification(`Analyzed ${data.results.length} URLs. Found ${data.phishing_count} phishing sites.`, 'success');
            } else {
                this.showNotification(data.error || 'Analysis failed', 'error');
            }
        } catch (error) {
            this.showNotification('Network error: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async analyzeUrl(url) {
        this.showLoading('Analyzing URL features...');
        
        try {
            const response = await fetch('/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url })
            });

            const data = await response.json();
            
            if (data.error) {
                this.showNotification(data.error, 'error');
            } else {
                this.displayResult(data);
                this.updateStats(1, data.is_phishing ? 1 : 0);
                
                // Show appropriate notification
                if (data.is_phishing) {
                    this.showNotification(`🚨 Phishing detected! Risk: ${data.risk_level}`, 'error');
                } else {
                    this.showNotification(`✅ URL appears safe. Risk: ${data.risk_level}`, 'success');
                }
            }
        } catch (error) {
            this.showNotification('Network error: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async trainModel() {
        this.showLoading('Training AI model with analytics...');
        
        try {
            const response = await fetch('/train', {
                method: 'POST'
            });

            const data = await response.json();
            
            if (data.success) {
                this.showNotification(`🤖 Model trained! Accuracy: ${(data.accuracy * 100).toFixed(2)}%`, 'success');
                if (data.graphs) {
                    this.displayTrainingGraphs(data.graphs);
                }
                this.checkHealth();
            } else {
                this.showNotification(data.error || 'Training failed', 'error');
            }
        } catch (error) {
            this.showNotification('Training failed: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    displayTrainingGraphs(graphs) {
        const trainingSection = document.getElementById('trainingGraphs');
        const container = document.getElementById('trainingGraphsContainer');
        
        if (graphs && Object.keys(graphs).length > 0) {
            let graphsHTML = '';
            
            if (graphs.feature_importance) {
                graphsHTML += `
                    <div class="graph-card">
                        <div class="graph-title">Feature Importance</div>
                        <img src="data:image/png;base64,${graphs.feature_importance}" alt="Feature Importance">
                    </div>
                `;
            }
            
            if (graphs.confusion_matrix) {
                graphsHTML += `
                    <div class="graph-card">
                        <div class="graph-title">Confusion Matrix</div>
                        <img src="data:image/png;base64,${graphs.confusion_matrix}" alt="Confusion Matrix">
                    </div>
                `;
            }
            
            container.innerHTML = graphsHTML;
            trainingSection.style.display = 'block';
            trainingSection.scrollIntoView({ behavior: 'smooth' });
        }
    }

    displayPredictionGraphs(graphs) {
        const predictionSection = document.getElementById('predictionGraphs');
        const container = document.getElementById('predictionGraphsContainer');
        
        if (graphs && Object.keys(graphs).length > 0) {
            let graphsHTML = '';
            
            if (graphs.risk_assessment) {
                graphsHTML += `
                    <div class="graph-card">
                        <div class="graph-title">Risk Assessment</div>
                        <img src="data:image/png;base64,${graphs.risk_assessment}" alt="Risk Assessment">
                    </div>
                `;
            }
            
            if (graphs.feature_contribution) {
                graphsHTML += `
                    <div class="graph-card">
                        <div class="graph-title">Feature Contribution</div>
                        <img src="data:image/png;base64,${graphs.feature_contribution}" alt="Feature Contribution">
                    </div>
                `;
            }
            
            container.innerHTML = graphsHTML;
            predictionSection.style.display = 'block';
        }
    }

    displayResult(result) {
        const resultsSection = document.getElementById('resultsSection');
        const featuresSection = document.getElementById('featuresSection');
        const resultsContainer = document.getElementById('resultsContainer');
        const featuresContainer = document.getElementById('featuresContainer');
        
        resultsSection.style.display = 'block';
        featuresSection.style.display = 'block';

        const resultClass = result.is_phishing ? 'result-phishing' : 'result-safe';
        const statusClass = result.is_phishing ? 'status-phishing' : 'status-safe';
        const statusText = result.is_phishing ? 'PHISHING DETECTED' : 'SAFE';
        const riskColor = result.risk_color;
        const riskIcon = result.is_phishing ? '🚨' : '✅';

        let resultHTML = `
            <div class="result-card ${resultClass}">
                <div class="result-header">
                    <div class="result-url">${result.url}</div>
                    <div class="result-status ${statusClass}">${riskIcon} ${statusText}</div>
                </div>
                <div class="result-details">
                    <div class="detail-item">
                        <span class="detail-label">Risk Level:</span>
                        <span class="detail-value" style="color: ${riskColor}; font-weight: 700;">${result.risk_level}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Risk Score:</span>
                        <span class="detail-value">${result.risk_score.toFixed(1)}%</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Confidence:</span>
                        <span class="detail-value">${(result.confidence * 100).toFixed(2)}%</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">AI Model:</span>
                        <span class="detail-value">${result.model_used}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Analysis Time:</span>
                        <span class="detail-value">${result.timestamp}</span>
                    </div>
                </div>
        `;

        // Add phishing analysis if available
        if (result.phishing_analysis && result.is_phishing) {
            const phishingAnalysis = result.phishing_analysis;
            
            resultHTML += `
                <div class="phishing-analysis">
                    <h3 style="margin: 20px 0 15px 0; color: #374151; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px;">
                        🎯 Phishing Type Analysis
                    </h3>
                    <div class="analysis-details">
                        <div class="analysis-item">
                            <strong>Primary Type:</strong>
                            <span class="phishing-type ${phishingAnalysis.primary_type}">
                                ${phishingAnalysis.primary_type.replace(/_/g, ' ').toUpperCase()}
                            </span>
                        </div>
                        <div class="analysis-item">
                            <strong>Description:</strong>
                            <span>${phishingAnalysis.description}</span>
                        </div>
                        ${phishingAnalysis.detected_patterns && phishingAnalysis.detected_patterns.length > 0 ? `
                        <div class="analysis-item">
                            <strong>Detected Patterns:</strong>
                            <ul style="margin: 5px 0; padding-left: 20px;">
                                ${phishingAnalysis.detected_patterns.map(pattern => `<li>${pattern}</li>`).join('')}
                            </ul>
                        </div>
                        ` : ''}
                    </div>
                </div>
                
                <div class="prevention-tips">
                    <h3 style="margin: 20px 0 15px 0; color: #374151; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px;">
                        💡 Prevention Tips
                    </h3>
                    <ul style="margin: 0; padding-left: 20px;">
                        ${result.prevention_tips.map(tip => `<li>${tip}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        resultHTML += `</div>`; // Close result-card

        resultsContainer.innerHTML = resultHTML;

        // Display feature analysis
        let featuresHTML = '<div class="features-grid">';
        for (const [feature, value] of Object.entries(result.feature_analysis)) {
            const featureClass = this.getFeatureClass(feature, value);
            const displayName = this.formatFeatureName(feature);
            const displayValue = this.formatFeatureValue(feature, value);
            
            featuresHTML += `
                <div class="feature-card">
                    <div class="feature-value ${featureClass}">${displayValue}</div>
                    <div class="feature-name">${displayName}</div>
                </div>
            `;
        }
        featuresHTML += '</div>';
        featuresContainer.innerHTML = featuresHTML;

        // Display prediction graphs if available
        if (result.graphs) {
            this.displayPredictionGraphs(result.graphs);
        }

        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    displayBatchResults(results) {
        const resultsSection = document.getElementById('resultsSection');
        const resultsContainer = document.getElementById('resultsContainer');
        
        resultsSection.style.display = 'block';
        document.getElementById('featuresSection').style.display = 'none';
        document.getElementById('trainingGraphs').style.display = 'none';
        document.getElementById('predictionGraphs').style.display = 'none';

        let resultsHTML = '';
        results.forEach(result => {
            const resultClass = result.is_phishing ? 'result-phishing' : 'result-safe';
            const statusClass = result.is_phishing ? 'status-phishing' : 'status-safe';
            const statusText = result.is_phishing ? 'PHISHING' : 'SAFE';
            const riskColor = result.risk_color;
            const riskIcon = result.is_phishing ? '🚨' : '✅';

            resultsHTML += `
                <div class="result-card ${resultClass}">
                    <div class="result-header">
                        <div class="result-url">${result.url}</div>
                        <div class="result-status ${statusClass}">${riskIcon} ${statusText}</div>
                    </div>
                    <div class="result-details">
                        <div class="detail-item">
                            <span class="detail-label">Risk Level:</span>
                            <span class="detail-value" style="color: ${riskColor}">${result.risk_level}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Confidence:</span>
                            <span class="detail-value">${(result.confidence * 100).toFixed(2)}%</span>
                        </div>
                    </div>
                </div>
            `;
        });

        resultsContainer.innerHTML = resultsHTML;
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    getFeatureClass(feature, value) {
        if (typeof value === 'boolean') {
            return value ? 'feature-high' : 'feature-low';
        }
        
        const thresholds = {
            'url_length': [30, 60],
            'num_special_chars': [3, 8],
            'num_digits': [2, 5],
            'url_entropy': [3, 4.5],
            'num_subdomains': [2, 4],
            'domain_age_days': [30, 365]  // Less than 30 days = high risk, less than 1 year = medium
        };

        if (thresholds[feature]) {
            const [low, high] = thresholds[feature];
            if (feature === 'domain_age_days') {
                // For domain age, lower values are riskier
                if (value < low) return 'feature-high';
                if (value < high) return 'feature-medium';
                return 'feature-low';
            } else {
                // For other features, higher values are riskier
                if (value < low) return 'feature-low';
                if (value < high) return 'feature-medium';
                return 'feature-high';
            }
        }

        return 'feature-medium';
    }

    formatFeatureName(feature) {
        const names = {
            'url_length': 'URL Length',
            'num_special_chars': 'Special Characters',
            'num_digits': 'Digit Count',
            'has_https': 'HTTPS Secure',
            'has_at_symbol': 'Contains @ Symbol',
            'has_double_slash': 'Double Slash',
            'num_subdomains': 'Subdomain Count',
            'has_ip': 'IP Address in URL',
            'suspicious_tld': 'Suspicious TLD',
            'url_entropy': 'URL Entropy',
            'has_suspicious_keywords': 'Suspicious Keywords',
            'domain_age_days': 'Domain Age (Days)'
        };
        return names[feature] || feature;
    }

    formatFeatureValue(feature, value) {
        if (typeof value === 'boolean') {
            return value ? 'Yes' : 'No';
        }
        
        if (feature === 'url_entropy') {
            return value.toFixed(2);
        }
        
        if (feature === 'domain_age_days') {
            if (value < 30) return `${value} days`;
            if (value < 365) return `${Math.round(value/30)} months`;
            return `${Math.round(value/365)} years`;
        }
        
        return value.toString();
    }

    updateStats(incrementTotal = 0, incrementPhishing = 0) {
        this.totalScanned += incrementTotal;
        this.phishingDetected += incrementPhishing;
        
        document.getElementById('totalScanned').textContent = this.totalScanned;
        document.getElementById('phishingDetected').textContent = this.phishingDetected;
    }

    clearResults() {
        document.getElementById('resultsContainer').innerHTML = '';
        document.getElementById('featuresContainer').innerHTML = '';
        document.getElementById('trainingGraphsContainer').innerHTML = '';
        document.getElementById('predictionGraphsContainer').innerHTML = '';
        document.getElementById('resultsSection').style.display = 'none';
        document.getElementById('featuresSection').style.display = 'none';
        document.getElementById('trainingGraphs').style.display = 'none';
        document.getElementById('predictionGraphs').style.display = 'none';
        document.getElementById('urlInput').value = '';
        document.getElementById('batchUrls').value = '';
        this.showNotification('Results cleared', 'success');
    }

    showLoading(message = 'Analyzing URL...') {
        const modal = document.getElementById('loadingModal');
        const title = document.getElementById('loadingTitle');
        const messageEl = document.getElementById('loadingMessage');
        
        title.textContent = 'AI Analysis in Progress';
        messageEl.textContent = message;
        modal.style.display = 'flex';
    }

    hideLoading() {
        const modal = document.getElementById('loadingModal');
        modal.style.display = 'none';
    }

    showNotification(message, type = 'info') {
        const notification = document.getElementById('notification');
        notification.textContent = message;
        notification.className = `notification ${type} show`;
        
        setTimeout(() => {
            notification.classList.remove('show');
        }, 5000);
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PhishingDetector();
    console.log('🚀 Phishing Detection System Ready!');
});