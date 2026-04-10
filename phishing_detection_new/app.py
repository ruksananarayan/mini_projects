import pandas as pd
import numpy as np
import re
import urllib.parse
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, confusion_matrix
import joblib
from datetime import datetime
from flask import Flask, render_template, request, jsonify
import os
import matplotlib
matplotlib.use('Agg')  # Required for server environments
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64

app = Flask(__name__)

class AdvancedPhishingDetector:
    def __init__(self):
        self.model = None
        self.feature_names = [
            'url_length', 'num_special_chars', 'num_digits', 'has_https',
            'has_at_symbol', 'has_double_slash', 'num_subdomains', 'has_ip',
            'suspicious_tld', 'url_entropy', 'has_suspicious_keywords', 'domain_age_days'
        ]
        self.is_trained = False
        self.model_type = "Random Forest"
        
        # Phishing type patterns
        self.phishing_patterns = {
            'brand_impersonation': {
                'keywords': ['facebook', 'google', 'paypal', 'amazon', 'microsoft', 'apple', 'netflix', 'bank'],
                'description': 'Imitates legitimate brands to steal credentials'
            },
            'credential_harvesting': {
                'keywords': ['login', 'signin', 'authenticate', 'password', 'credential', 'verify'],
                'description': 'Designed to capture usernames and passwords'
            },
            'financial_phishing': {
                'keywords': ['bank', 'paypal', 'payment', 'billing', 'invoice', 'transfer'],
                'description': 'Targets financial information and accounts'
            },
            'urgent_action': {
                'keywords': ['urgent', 'immediate', 'security', 'alert', 'suspicious', 'required'],
                'description': 'Creates urgency to prompt quick action'
            },
            'account_recovery': {
                'keywords': ['recovery', 'reset', 'restore', 'unlock', 'suspend'],
                'description': 'Pretends to help with account issues'
            },
            'social_engineering': {
                'keywords': ['update', 'confirm', 'validate', 'secure', 'protection'],
                'description': 'Uses psychological manipulation'
            }
        }
        
    def generate_synthetic_data(self):
        """Generate comprehensive synthetic phishing dataset"""
        print("📊 Generating training data...")
        np.random.seed(42)
        n_samples = 2000
        
        data = []
        
        for i in range(n_samples):
            if i < n_samples // 2:  # Legitimate URLs
                # Safe URL features
                url_length = np.random.randint(15, 50)
                num_special_chars = np.random.randint(0, 3)
                num_digits = np.random.randint(0, 2)
                has_https = np.random.choice([0, 1], p=[0.1, 0.9])
                has_at_symbol = 0
                has_double_slash = 1
                num_subdomains = np.random.randint(0, 2)
                has_ip = 0
                suspicious_tld = 0
                url_entropy = np.random.uniform(1, 3)
                has_suspicious_keywords = 0
                domain_age_days = np.random.randint(365, 3650)
                label = 0
                
            else:  # Phishing URLs
                # Phishing URL features
                url_length = np.random.randint(40, 100)
                num_special_chars = np.random.randint(3, 10)
                num_digits = np.random.randint(2, 8)
                has_https = np.random.choice([0, 1], p=[0.4, 0.6])
                has_at_symbol = np.random.choice([0, 1], p=[0.8, 0.2])
                has_double_slash = np.random.choice([0, 1], p=[0.3, 0.7])
                num_subdomains = np.random.randint(2, 5)
                has_ip = np.random.choice([0, 1], p=[0.9, 0.1])
                suspicious_tld = np.random.choice([0, 1], p=[0.4, 0.6])
                url_entropy = np.random.uniform(3, 6)
                has_suspicious_keywords = np.random.choice([0, 1], p=[0.2, 0.8])
                domain_age_days = np.random.randint(1, 100)
                label = 1
            
            data.append([
                url_length, num_special_chars, num_digits, has_https,
                has_at_symbol, has_double_slash, num_subdomains, has_ip,
                suspicious_tld, url_entropy, has_suspicious_keywords, 
                domain_age_days, label
            ])
        
        columns = self.feature_names + ['label']
        return pd.DataFrame(data, columns=columns)
    
    def detect_phishing_type(self, url, features):
        """Detect specific type of phishing attack"""
        url_lower = url.lower()
        phishing_types = []
        detected_patterns = []
        
        # Check for brand impersonation
        for brand in self.phishing_patterns['brand_impersonation']['keywords']:
            if brand in url_lower:
                phishing_types.append('brand_impersonation')
                detected_patterns.append(f"Impersonates {brand.title()}")
                break
        
        # Check for credential harvesting
        credential_keywords = [kw for kw in self.phishing_patterns['credential_harvesting']['keywords'] if kw in url_lower]
        if credential_keywords:
            phishing_types.append('credential_harvesting')
            detected_patterns.append(f"Harvests credentials using: {', '.join(credential_keywords)}")
        
        # Check for financial phishing
        financial_keywords = [kw for kw in self.phishing_patterns['financial_phishing']['keywords'] if kw in url_lower]
        if financial_keywords:
            phishing_types.append('financial_phishing')
            detected_patterns.append(f"Targets financial data using: {', '.join(financial_keywords)}")
        
        # Check for urgent action
        urgent_keywords = [kw for kw in self.phishing_patterns['urgent_action']['keywords'] if kw in url_lower]
        if urgent_keywords:
            phishing_types.append('urgent_action')
            detected_patterns.append(f"Creates urgency with: {', '.join(urgent_keywords)}")
        
        # Check for account recovery
        recovery_keywords = [kw for kw in self.phishing_patterns['account_recovery']['keywords'] if kw in url_lower]
        if recovery_keywords:
            phishing_types.append('account_recovery')
            detected_patterns.append(f"Fake recovery with: {', '.join(recovery_keywords)}")
        
        # Check for social engineering
        social_keywords = [kw for kw in self.phishing_patterns['social_engineering']['keywords'] if kw in url_lower]
        if social_keywords:
            phishing_types.append('social_engineering')
            detected_patterns.append(f"Uses manipulation: {', '.join(social_keywords)}")
        
        # Additional pattern detection based on features
        if features[7] == 1:  # has_ip
            phishing_types.append('ip_based')
            detected_patterns.append("Uses IP address for obfuscation")
        
        if features[4] == 1:  # has_at_symbol
            phishing_types.append('url_obfuscation')
            detected_patterns.append("Uses @ symbol for URL obfuscation")
        
        if features[8] == 1:  # suspicious_tld
            phishing_types.append('suspicious_domain')
            detected_patterns.append("Uses suspicious TLD")
        
        if features[0] > 80:  # long url_length
            phishing_types.append('long_url')
            detected_patterns.append("Uses excessively long URL")
        
        # Remove duplicates and return
        phishing_types = list(set(phishing_types))
        
        # Determine primary phishing type
        primary_type = "unknown"
        if phishing_types:
            primary_type = phishing_types[0]
            if len(phishing_types) > 1:
                primary_type = "combined_attack"
        
        return {
            'primary_type': primary_type,
            'all_types': phishing_types,
            'detected_patterns': detected_patterns,
            'description': self.get_phishing_description(primary_type, phishing_types)
        }
    
    def get_phishing_description(self, primary_type, all_types):
        """Get detailed description of phishing type"""
        descriptions = {
            'brand_impersonation': 'This URL is impersonating a well-known brand to trick users into entering their credentials.',
            'credential_harvesting': 'This site is designed to capture usernames and passwords through fake login pages.',
            'financial_phishing': 'This attack targets financial information, often mimicking banking or payment sites.',
            'urgent_action': 'This uses urgency and fear to make users act quickly without thinking.',
            'account_recovery': 'This pretends to help with account issues to steal recovery information.',
            'social_engineering': 'This uses psychological manipulation to trick users into revealing information.',
            'ip_based': 'This uses IP addresses instead of domain names to avoid detection.',
            'url_obfuscation': 'This uses special characters and techniques to hide the true destination.',
            'suspicious_domain': 'This uses less common TLDs often associated with malicious sites.',
            'long_url': 'This uses excessively long URLs to hide malicious content and avoid scrutiny.',
            'combined_attack': 'This uses multiple phishing techniques for a more sophisticated attack.',
            'unknown': 'This shows characteristics of phishing but uses uncommon patterns.'
        }
        
        if primary_type in descriptions:
            return descriptions[primary_type]
        return descriptions['unknown']
    
    def get_prevention_tips(self, phishing_type):
        """Get prevention tips based on phishing type"""
        tips = {
            'brand_impersonation': [
                "Always check the official domain name carefully",
                "Look for misspellings or character substitutions",
                "Use official apps or bookmarked URLs",
                "Verify through official communication channels"
            ],
            'credential_harvesting': [
                "Never enter credentials on unfamiliar sites",
                "Check for HTTPS and security indicators",
                "Use password managers that detect fake sites",
                "Enable two-factor authentication"
            ],
            'financial_phishing': [
                "Never click financial links in emails",
                "Type bank URLs directly or use bookmarks",
                "Verify unusual requests by phone",
                "Monitor account activity regularly"
            ],
            'urgent_action': [
                "Legitimate companies don't create false urgency",
                "Take time to verify before acting",
                "Contact the company directly",
                "Check for official communication"
            ],
            'account_recovery': [
                "Never use recovery links from emails",
                "Go directly to the official site",
                "Use official support channels",
                "Verify your recovery options"
            ],
            'social_engineering': [
                "Be skeptical of unsolicited requests",
                "Verify information independently",
                "Don't trust too-good-to-be-true offers",
                "Educate yourself about common tactics"
            ]
        }
        
        return tips.get(phishing_type, [
            "Verify the website through official channels",
            "Don't enter personal information on suspicious sites",
            "Use security software and keep it updated",
            "Educate yourself about phishing techniques"
        ])
    
    def create_analysis_graphs(self, X_train, y_train, X_test, y_test, predictions):
        """Create training analysis graphs"""
        graphs = {}
        
        try:
            plt.style.use('default')
            sns.set_style("whitegrid")
            
            # 1. Feature Importance Graph
            plt.figure(figsize=(8, 5))
            if hasattr(self.model, 'feature_importances_'):
                feature_importance = self.model.feature_importances_
                indices = np.argsort(feature_importance)[::-1][:8]
                
                features_display = [self.feature_names[i].replace('_', ' ').title() for i in indices]
                colors = plt.cm.PuBu(np.linspace(0.4, 0.8, len(indices)))
                
                bars = plt.barh(range(len(indices)), feature_importance[indices], 
                               color=colors, alpha=0.8, edgecolor='white', linewidth=1)
                
                for i, bar in enumerate(bars):
                    width = bar.get_width()
                    plt.text(width + 0.001, bar.get_y() + bar.get_height()/2, 
                            f'{width:.3f}', ha='left', va='center', fontsize=9)
                
                plt.yticks(range(len(indices)), features_display, fontsize=10)
                plt.xlabel('Feature Importance')
                plt.title('Top Feature Importance', fontsize=13, fontweight='bold', pad=15)
                plt.gca().invert_yaxis()
                plt.grid(axis='x', alpha=0.3)
                plt.tight_layout()
                
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', dpi=120, bbox_inches='tight')
                img_buffer.seek(0)
                graphs['feature_importance'] = base64.b64encode(img_buffer.getvalue()).decode()
                plt.close()
            
        except Exception as e:
            print(f"Graph creation error: {e}")
            
        return graphs
    
    def create_prediction_graphs(self, url, features, prediction_result, phishing_analysis):
        """Create Risk Assessment and Feature Contribution graphs"""
        graphs = {}
        
        try:
            plt.style.use('default')
            sns.set_style("whitegrid")
            
            # 1. Risk Assessment Gauge
            plt.figure(figsize=(8, 6))
            risk_score = prediction_result['risk_score']
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Background with theme gradient
            background_gradient = np.linspace(0, 1, 100).reshape(1, -1)
            ax.imshow(background_gradient, extent=[0, 100, 0, 1], aspect='auto', 
                     cmap='Purples', alpha=0.1)
            
            # Risk ranges with theme colors
            risk_ranges = [(0, 40, '#10b981'), (40, 70, '#f59e0b'), (70, 100, '#ef4444')]
            
            for start, end, color in risk_ranges:
                ax.barh(0.3, end - start, left=start, height=0.4, 
                       color=color, alpha=0.8, edgecolor='white', linewidth=2)
            
            # Risk needle
            ax.axvline(x=risk_score, color='#4f46e5', linewidth=6, ymin=0.1, ymax=0.9)
            ax.plot(risk_score, 0.7, 'o', color='#4f46e5', markersize=15, 
                   markeredgecolor='white', markeredgewidth=2)
            
            # Customize
            ax.set_xlim(0, 100)
            ax.set_ylim(0, 1)
            ax.set_yticks([])
            ax.set_xlabel('Risk Score (%)', fontsize=12, fontweight='bold', color='#374151')
            ax.set_title('Risk Assessment', fontsize=16, fontweight='bold', 
                        pad=20, color='#4f46e5')
            
            # Add risk level labels
            risk_labels = ['LOW', 'MEDIUM', 'HIGH']
            label_positions = [20, 55, 85]
            for label, pos in zip(risk_labels, label_positions):
                ax.text(pos, 0.15, label, ha='center', va='center', 
                       fontsize=11, fontweight='bold', color='#374151',
                       bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.9))
            
            # Add current risk value
            ax.text(risk_score, 0.85, f'{risk_score:.1f}%', ha='center', va='center',
                   fontsize=14, fontweight='bold', color='#4f46e5',
                   bbox=dict(boxstyle="round,pad=0.5", facecolor='white', edgecolor='#4f46e5'))
            
            # Style the plot to match theme
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_visible(False)
            ax.spines['bottom'].set_color('#e5e7eb')
            ax.tick_params(axis='x', colors='#6b7280', labelsize=10)
            ax.grid(axis='x', alpha=0.3, color='#e5e7eb')
            
            plt.tight_layout()
            
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=120, bbox_inches='tight',
                       facecolor='white', edgecolor='none', transparent=False)
            img_buffer.seek(0)
            graphs['risk_assessment'] = base64.b64encode(img_buffer.getvalue()).decode()
            plt.close()
            
            # 2. Feature Contribution Assessment
            plt.figure(figsize=(10, 6))
            
            if hasattr(self.model, 'feature_importances_'):
                feature_importance = self.model.feature_importances_
                
                # Calculate meaningful risk contributions
                contributing_features = []
                contribution_scores = []
                feature_colors = []
                
                for i, (feature, value, importance) in enumerate(zip(self.feature_names, features, feature_importance)):
                    # Calculate actual contribution based on feature characteristics
                    if feature in ['url_length', 'num_special_chars', 'num_digits', 'url_entropy']:
                        if feature == 'url_length':
                            normalized_value = min(value / 100, 1.0)
                        elif feature == 'url_entropy':
                            normalized_value = min(value / 6, 1.0)
                        else:
                            normalized_value = min(value / 10, 1.0)
                        contribution = normalized_value * importance * 100
                    elif feature == 'has_https':
                        # HTTPS reduces risk
                        contribution = (1 - value) * importance * 50
                    else:
                        # Boolean features increase risk when present
                        contribution = value * importance * 100
                    
                    if contribution > 1.0:
                        contributing_features.append(feature.replace('_', ' ').title())
                        contribution_scores.append(contribution)
                        
                        # Color based on risk level using theme colors
                        if contribution > 15:
                            feature_colors.append('#ef4444')
                        elif contribution > 8:
                            feature_colors.append('#f59e0b')
                        else:
                            feature_colors.append('#10b981')
                
                if contributing_features:
                    # Sort by contribution
                    sorted_indices = np.argsort(contribution_scores)[::-1]
                    contributing_features = [contributing_features[i] for i in sorted_indices]
                    contribution_scores = [contribution_scores[i] for i in sorted_indices]
                    feature_colors = [feature_colors[i] for i in sorted_indices]
                    
                    # Create horizontal bar chart
                    y_pos = np.arange(len(contributing_features))
                    
                    bars = plt.barh(y_pos, contribution_scores, color=feature_colors, 
                                   alpha=0.8, edgecolor='white', linewidth=1.5)
                    
                    # Add value labels
                    for i, bar in enumerate(bars):
                        width = bar.get_width()
                        plt.text(width + 0.5, bar.get_y() + bar.get_height()/2, 
                                f'{width:.1f}%', ha='left', va='center', 
                                fontsize=10, fontweight='bold', color='#374151')
                    
                    plt.yticks(y_pos, contributing_features, fontsize=11, color='#374151')
                    plt.xlabel('Risk Contribution (%)', fontsize=12, fontweight='bold', color='#374151')
                    plt.title('Feature Contribution Assessment', fontsize=16, fontweight='bold', 
                             pad=20, color='#4f46e5')
                    plt.gca().invert_yaxis()
                    
                    # Style the plot to match theme
                    ax = plt.gca()
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)
                    ax.spines['left'].set_color('#e5e7eb')
                    ax.spines['bottom'].set_color('#e5e7eb')
                    ax.tick_params(axis='x', colors='#6b7280', labelsize=10)
                    ax.tick_params(axis='y', colors='#6b7280', labelsize=10)
                    ax.grid(axis='x', alpha=0.3, color='#e5e7eb')
                    ax.set_axisbelow(True)
                    ax.set_facecolor('#fafafa')
                    
                    plt.tight_layout()
                    
                    img_buffer = io.BytesIO()
                    plt.savefig(img_buffer, format='png', dpi=120, bbox_inches='tight',
                               facecolor='white', edgecolor='none', transparent=False)
                    img_buffer.seek(0)
                    graphs['feature_contribution'] = base64.b64encode(img_buffer.getvalue()).decode()
                    plt.close()
            
        except Exception as e:
            print(f"Prediction graph error: {e}")
            
        return graphs
    
    def extract_features(self, url):
        """Extract features from URL"""
        try:
            # Basic URL features
            url_length = len(url)
            num_special_chars = len(re.findall(r'[^\w\s.]', url))
            num_digits = len(re.findall(r'\d', url))
            has_https = 1 if url.startswith('https') else 0
            has_at_symbol = 1 if '@' in url else 0
            has_double_slash = 1 if '//' in url else 0
            
            # Parse URL for domain analysis
            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc if parsed.netloc else parsed.path.split('/')[0]
            
            # Count subdomains
            num_subdomains = domain.count('.') - 1
            if num_subdomains < 0:
                num_subdomains = 0
                
            # Check for IP address
            has_ip = 1 if re.match(r'\d+\.\d+\.\d+\.\d+', domain) else 0
            
            # Check for suspicious TLDs
            suspicious_tlds = ['.tk', '.ml', '.ga', '.cf', '.gq', '.xyz', '.top', '.loan', '.click']
            suspicious_tld = 1 if any(tld in domain for tld in suspicious_tlds) else 0
            
            # Calculate entropy
            if len(url) > 0:
                prob = [float(url.count(c)) / len(url) for c in set(url)]
                url_entropy = -sum([p * np.log2(p) for p in prob if p > 0])
            else:
                url_entropy = 0
            
            # Check for suspicious keywords
            suspicious_keywords = [
                'login', 'verify', 'account', 'update', 'secure', 'banking', 
                'password', 'signin', 'validation', 'billing', 'payment'
            ]
            has_suspicious_keywords = 1 if any(keyword in url.lower() for keyword in suspicious_keywords) else 0
            
            # Simulate domain age based on features
            if suspicious_tld:
                domain_age_days = np.random.randint(1, 30)
            else:
                domain_age_days = np.random.randint(365, 3650)
            
            features = [
                url_length, num_special_chars, num_digits, has_https,
                has_at_symbol, has_double_slash, num_subdomains, has_ip,
                suspicious_tld, url_entropy, has_suspicious_keywords, 
                domain_age_days
            ]
            
            return features
            
        except Exception as e:
            print(f"Error extracting features: {e}")
            return [0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 365]
    
    def train_model(self):
        """Train the phishing detection model"""
        print("🤖 Training AI Model...")
        try:
            df = self.generate_synthetic_data()
            
            # Prepare features and labels
            X = df.drop('label', axis=1)
            y = df['label']
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Train Random Forest
            print("🌲 Training Random Forest...")
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            self.model.fit(X_train, y_train)
            
            # Evaluate model
            predictions = self.model.predict(X_test)
            accuracy = accuracy_score(y_test, predictions)
            
            self.is_trained = True
            
            # Create analysis graphs
            graphs = self.create_analysis_graphs(X_train, y_train, X_test, y_test, predictions)
            
            # Save model
            joblib.dump(self.model, 'phishing_model.pkl')
            print(f"✅ Model trained successfully! Accuracy: {accuracy:.4f}")
            
            return {
                'success': True,
                'accuracy': float(accuracy),
                'model_used': 'Random Forest',
                'training_samples': len(X_train),
                'graphs': graphs
            }
            
        except Exception as e:
            print(f"❌ Training failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def predict_phishing(self, url):
        """Predict if URL is phishing with type detection"""
        try:
            if not self.is_trained:
                if os.path.exists('phishing_model.pkl'):
                    self.model = joblib.load('phishing_model.pkl')
                    self.is_trained = True
                    print("✅ Loaded pre-trained model")
                else:
                    return {"error": "Model not trained. Please train first."}
            
            # Extract features
            features = self.extract_features(url)
            
            # Make prediction
            prediction = self.model.predict([features])[0]
            probability = self.model.predict_proba([features])[0]
            
            # Calculate risk score
            risk_score = probability[1] * 100
            
            # Determine risk level
            if risk_score >= 70:
                risk_level = "HIGH"
                risk_color = "#ef4444"
            elif risk_score >= 40:
                risk_level = "MEDIUM" 
                risk_color = "#f59e0b"
            else:
                risk_level = "LOW"
                risk_color = "#10b981"
            
            # Feature analysis
            feature_analysis = dict(zip(self.feature_names, features))
            
            # Detect phishing type
            phishing_analysis = self.detect_phishing_type(url, features)
            
            # Get prevention tips
            prevention_tips = self.get_prevention_tips(phishing_analysis['primary_type'])
            
            # Create prediction result
            prediction_result = {
                'url': url,
                'is_phishing': bool(prediction),
                'confidence': float(max(probability)),
                'risk_score': risk_score,
                'risk_level': risk_level,
                'risk_color': risk_color,
                'model_used': self.model_type,
                'feature_analysis': feature_analysis,
                'phishing_analysis': phishing_analysis,
                'prevention_tips': prevention_tips,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Create graphs
            graphs = self.create_prediction_graphs(url, features, prediction_result, phishing_analysis)
            prediction_result['graphs'] = graphs
            
            return prediction_result
            
        except Exception as e:
            print(f"❌ Prediction error: {e}")
            return {"error": f"Prediction failed: {str(e)}"}

# Initialize detector
detector = AdvancedPhishingDetector()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/train', methods=['POST'])
def train_model():
    results = detector.train_model()
    return jsonify(results)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'URL is required'})
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        result = detector.predict_phishing(url)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Request failed: {str(e)}'})

@app.route('/batch_predict', methods=['POST'])
def batch_predict():
    try:
        data = request.get_json()
        urls = data.get('urls', [])
        
        if not urls:
            return jsonify({'error': 'URLs are required'})
        
        results = []
        for url in urls[:5]:
            if url.strip():
                result = detector.predict_phishing(url.strip())
                results.append(result)
        
        return jsonify({
            'success': True,
            'results': results,
            'total_checked': len(results),
            'phishing_count': sum(1 for r in results if r.get('is_phishing'))
        })
        
    except Exception as e:
        return jsonify({'error': f'Batch prediction failed: {str(e)}'})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'model_trained': detector.is_trained,
        'model_type': detector.model_type
    })

if __name__ == '__main__':
    print("🌐 Starting Advanced Phishing Detection System...")
    print("🔧 Initializing components...")
    
    if not os.path.exists('phishing_model.pkl'):
        print("🤖 Training AI model on startup...")
        detector.train_model()
    else:
        print("✅ Using pre-trained model")
        detector.model = joblib.load('phishing_model.pkl')
        detector.is_trained = True
    
    print("🚀 Starting Flask server...")
    print("🎯 Phishing type detection enabled!")
    print("🌍 Access the application at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)