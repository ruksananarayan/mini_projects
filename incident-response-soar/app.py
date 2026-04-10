# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import hashlib
import pandas as pd
import re
import json

db = SQLAlchemy()

class Incident(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    severity = db.Column(db.String(20), default='medium')
    status = db.Column(db.String(20), default='open')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    source_ip = db.Column(db.String(50))
    destination_ip = db.Column(db.String(50))

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(100), nullable=False)
    alert_type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    severity = db.Column(db.String(20), default='medium')
    confidence = db.Column(db.Float, default=0.5)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='new')
    incident_id = db.Column(db.Integer, db.ForeignKey('incident.id'), nullable=True)
    source_ip = db.Column(db.String(50))
    
    def to_dict(self):
        return {
            'id': self.id, 'source': self.source, 'type': self.alert_type,
            'description': self.description, 'severity': self.severity,
            'confidence': self.confidence, 'timestamp': self.timestamp.isoformat(),
            'status': self.status, 'incident_id': self.incident_id,
            'source_ip': self.source_ip
        }

class Evidence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    evidence_type = db.Column(db.String(100), nullable=False)
    source = db.Column(db.String(200))
    file_path = db.Column(db.String(500))
    collected_at = db.Column(db.DateTime, default=datetime.utcnow)
    incident_id = db.Column(db.Integer, db.ForeignKey('incident.id'))

class EvidenceCollector:
    def collect_logs(self, log_sources, incident_id):
        collected_logs = []
        for source in log_sources:
            filepath = f"./data/evidence/logs_{source}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            with open(filepath, 'w') as f:
                f.write(f"Evidence from {source} for incident {incident_id}")
            collected_logs.append({'evidence_type': 'logs', 'source': source, 'file_path': filepath})
        return collected_logs

class LogParser:
    def parse_log_file(self, log_source, file_path):
        try:
            if log_source == 'firewall':
                df = pd.read_csv(file_path)
                return df.to_dict('records')
            else:
                parsed_logs = []
                with open(file_path, 'r') as f:
                    for line_num, line in enumerate(f, 1):
                        parsed_logs.append({'raw': line.strip(), 'line_number': line_num})
                return parsed_logs
        except Exception as e:
            print(f"Log parsing failed: {str(e)}")
            return []
    
    def detect_anomalies(self, parsed_logs):
        anomalies = []
        failed_attempts = [log for log in parsed_logs if 'DENY' in str(log.get('action', '')) or '404' in str(log)]
        if len(failed_attempts) > 2:
            anomalies.append({'type': 'multiple_denials', 'severity': 'medium', 'count': len(failed_attempts)})
        
        # Detect suspicious IPs
        suspicious_ips = ['203.0.113.', '198.51.100.', '10.0.0.100']
        for log in parsed_logs:
            for ip in suspicious_ips:
                if ip in str(log):
                    anomalies.append({
                        'type': 'suspicious_ip', 
                        'severity': 'high', 
                        'description': f'Suspicious IP detected: {ip}',
                        'log_entry': log
                    })
                    break
        
        return anomalies

class AlertTriage:
    def __init__(self):
        self.threat_intelligence = {
            'suspicious_ips': ['203.0.113.45', '203.0.113.46', '198.51.100.23', '198.51.100.24', '10.0.0.100'],
            'malicious_patterns': ['brute', 'force', 'malware', 'scan', 'injection', 'exploit']
        }
    
    def triage_alert(self, alert_data):
        confidence = alert_data.get('confidence', 0.3)
        severity = alert_data.get('severity', 'low')
        
        # Check suspicious IP
        if alert_data.get('source_ip') in self.threat_intelligence['suspicious_ips']:
            confidence += 0.4
            severity = 'high'
        
        # Check for brute force patterns
        description = alert_data.get('description', '').lower()
        if any(pattern in description for pattern in ['brute', 'force', 'multiple', 'failed']):
            confidence += 0.3
            severity = 'high'
        
        # Check for malware patterns
        if any(pattern in description for pattern in ['malware', 'virus', 'trojan', 'ransomware']):
            confidence += 0.4
            severity = 'high'
        
        confidence = min(confidence, 1.0)
        
        # Final severity determination
        if confidence >= 0.8:
            severity = 'critical'
        elif confidence >= 0.6:
            severity = 'high'
        elif confidence >= 0.4:
            severity = 'medium'
        else:
            severity = 'low'
            
        return {
            'final_severity': severity, 
            'final_confidence': round(confidence, 2),
            'analysis': f'Analyzed: {description}'
        }

class AutomationEngine:
    def process_alert(self, alert_data):
        triage_result = AlertTriage().triage_alert(alert_data)
        
        # Determine actions based on severity
        actions = []
        if triage_result['final_severity'] in ['high', 'critical']:
            actions = ['collect_evidence', 'block_ip', 'notify_team', 'create_incident']
        elif triage_result['final_severity'] == 'medium':
            actions = ['collect_evidence', 'monitor']
        else:
            actions = ['review']
            
        return {
            'triage_result': triage_result, 
            'actions': actions,
            'timestamp': datetime.utcnow().isoformat()
        }

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///incident_response.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

db.init_app(app)

def init_database():
    """Initialize database with proper error handling"""
    try:
        # Drop all tables and recreate (clean start)
        db.drop_all()
        db.create_all()
        print("✅ Database tables created successfully")
        
        # Create sample data
        sample_incidents = [
            Incident(
                title="Brute Force Attack Detected", 
                description="Multiple failed login attempts from suspicious IP", 
                severity="high",
                source_ip="203.0.113.45",
                destination_ip="10.0.0.50"
            ),
            Incident(
                title="Port Scanning Activity", 
                description="TCP port scanning detected from external IP", 
                severity="medium",
                source_ip="198.51.100.23",
                destination_ip="10.0.0.51"
            )
        ]
        db.session.add_all(sample_incidents)
        
        sample_alerts = [
            Alert(
                source="Firewall", 
                alert_type="Brute Force Attempt", 
                description="Multiple failed SSH connections from 203.0.113.45",
                severity="high", 
                confidence=0.85,
                source_ip="203.0.113.45"
            ),
            Alert(
                source="IDS", 
                alert_type="Port Scan", 
                description="TCP port scanning detected from 198.51.100.23",
                severity="medium", 
                confidence=0.65,
                source_ip="198.51.100.23"
            )
        ]
        db.session.add_all(sample_alerts)
        
        db.session.commit()
        print("✅ Sample data loaded successfully")
        
    except Exception as e:
        print(f"❌ Database initialization error: {str(e)}")
        # Try to recreate database
        try:
            db.drop_all()
            db.create_all()
            print("✅ Database recreated after error")
        except Exception as e2:
            print(f"❌ Critical database error: {str(e2)}")
            raise

# Initialize database when app starts
with app.app_context():
    init_database()

# Routes
@app.route('/')
def dashboard():
    try:
        stats = {
            'total_incidents': Incident.query.count(),
            'open_incidents': Incident.query.filter_by(status='open').count(),
            'high_severity': Incident.query.filter(Incident.severity.in_(['high', 'critical'])).count(),
            'total_alerts': Alert.query.count()
        }
        recent_incidents = Incident.query.order_by(Incident.created_at.desc()).limit(5).all()
        recent_alerts = Alert.query.order_by(Alert.timestamp.desc()).limit(5).all()
        return render_template('dashboard.html', **stats, recent_incidents=recent_incidents, recent_alerts=recent_alerts)
    except Exception as e:
        return f"Error loading dashboard: {str(e)}", 500

@app.route('/incidents')
def incidents():
    try:
        incidents_list = Incident.query.order_by(Incident.created_at.desc()).all()
        return render_template('incidents.html', incidents=incidents_list)
    except Exception as e:
        return f"Error loading incidents: {str(e)}", 500

@app.route('/alerts')
def alerts():
    try:
        alerts_list = Alert.query.order_by(Alert.timestamp.desc()).all()
        return render_template('alerts.html', alerts=alerts_list)
    except Exception as e:
        return f"Error loading alerts: {str(e)}", 500

@app.route('/create-incident', methods=['GET', 'POST'])
def create_incident_form():
    if request.method == 'POST':
        try:
            incident = Incident(
                title=request.form.get('title'),
                description=request.form.get('description'),
                severity=request.form.get('severity'),
                source_ip=request.form.get('source_ip'),
                destination_ip=request.form.get('destination_ip')
            )
            db.session.add(incident)
            db.session.commit()
            return redirect(url_for('incidents'))
        except Exception as e:
            return f"Error creating incident: {str(e)}", 500
    
    return render_template('create_incident.html')

@app.route('/create-alert', methods=['GET', 'POST'])
def create_alert_form():
    if request.method == 'POST':
        try:
            alert = Alert(
                source=request.form.get('source'),
                alert_type=request.form.get('alert_type'),
                description=request.form.get('description'),
                severity=request.form.get('severity'),
                confidence=float(request.form.get('confidence', 0.5)),
                source_ip=request.form.get('source_ip')
            )
            db.session.add(alert)
            db.session.commit()
            
            # Process through automation
            automation_engine = AutomationEngine()
            alert_data = alert.to_dict()
            automation_result = automation_engine.process_alert(alert_data)
            
            # Update alert with automation results
            alert.severity = automation_result['triage_result']['final_severity']
            alert.confidence = automation_result['triage_result']['final_confidence']
            alert.status = 'automated'
            db.session.commit()
            
            return redirect(url_for('alerts'))
        except Exception as e:
            return f"Error creating alert: {str(e)}", 500
    
    return render_template('create_alert.html')

@app.route('/upload-logs', methods=['GET', 'POST'])
def upload_logs():
    if request.method == 'POST':
        try:
            log_content = request.form.get('log_content')
            log_type = request.form.get('log_type', 'firewall')
            
            # Save uploaded log
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"uploaded_{log_type}_{timestamp}.log"
            filepath = os.path.join('./data/logs', filename)
            
            with open(filepath, 'w') as f:
                f.write(log_content)
            
            # Parse and analyze
            log_parser = LogParser()
            parsed_logs = log_parser.parse_log_file(log_type, filepath)
            anomalies = log_parser.detect_anomalies(parsed_logs)
            
            return render_template('log_results.html', 
                                parsed_logs=parsed_logs,
                                anomalies=anomalies,
                                log_type=log_type,
                                filename=filename)
            
        except Exception as e:
            return f"Error processing logs: {str(e)}", 500
    
    return render_template('upload_logs.html')

# API Routes
@app.route('/api/incidents', methods=['POST'])
def create_incident():
    try:
        data = request.get_json()
        incident = Incident(
            title=data.get('title', 'New Incident'),
            description=data.get('description', ''),
            severity=data.get('severity', 'medium'),
            source_ip=data.get('source_ip', ''),
            destination_ip=data.get('destination_ip', '')
        )
        db.session.add(incident)
        db.session.commit()
        return jsonify({'id': incident.id, 'message': 'Incident created successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts', methods=['POST'])
def create_alert():
    try:
        data = request.get_json()
        alert = Alert(
            source=data.get('source', 'Unknown'),
            alert_type=data.get('type', 'Alert'),
            description=data.get('description', ''),
            severity=data.get('severity', 'low'),
            confidence=data.get('confidence', 0.5),
            source_ip=data.get('source_ip', '')
        )
        db.session.add(alert)
        db.session.commit()
        
        automation_engine = AutomationEngine()
        automation_result = automation_engine.process_alert(alert.to_dict())
        
        return jsonify({
            'alert_id': alert.id, 
            'automation_result': automation_result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/parse-logs', methods=['POST'])
def parse_logs():
    try:
        data = request.get_json()
        log_content = data.get('log_content', '')
        log_type = data.get('log_type', 'firewall')
        
        # Save temporary log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"temp_{log_type}_{timestamp}.log"
        filepath = os.path.join('./data/logs', filename)
        
        with open(filepath, 'w') as f:
            f.write(log_content)
        
        log_parser = LogParser()
        parsed_logs = log_parser.parse_log_file(log_type, filepath)
        anomalies = log_parser.detect_anomalies(parsed_logs)
        
        return jsonify({
            'parsed_logs_count': len(parsed_logs),
            'anomalies_detected': len(anomalies),
            'anomalies': anomalies,
            'filename': filename
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts/<int:alert_id>/triage', methods=['POST'])
def triage_alert(alert_id):
    try:
        alert = Alert.query.get_or_404(alert_id)
        triage_result = AlertTriage().triage_alert(alert.to_dict())
        alert.severity = triage_result['final_severity']
        alert.confidence = triage_result['final_confidence']
        alert.status = 'triaged'
        db.session.commit()
        return jsonify(triage_result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/collect-evidence/<int:incident_id>', methods=['POST'])
def collect_evidence(incident_id):
    try:
        incident = Incident.query.get_or_404(incident_id)
        evidence = EvidenceCollector().collect_logs(['firewall', 'web_server'], incident_id)
        for item in evidence:
            evidence_record = Evidence(
                evidence_type=item['evidence_type'],
                source=item['source'],
                file_path=item['file_path'],
                incident_id=incident_id
            )
            db.session.add(evidence_record)
        db.session.commit()
        return jsonify({'message': f'Collected {len(evidence)} evidence items'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reset-db', methods=['POST'])
def reset_database():
    """API endpoint to reset database (for development)"""
    try:
        init_database()
        return jsonify({'message': 'Database reset successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('./data/logs', exist_ok=True)
    os.makedirs('./data/evidence', exist_ok=True)
    
    print("🚀 SOAR Platform Starting...")
    print("📊 Dashboard: http://localhost:5000")
    print("📝 Create Incident: http://localhost:5000/create-incident")
    print("🚨 Create Alert: http://localhost:5000/create-alert")
    print("📁 Upload Logs: http://localhost:5000/upload-logs")
    print("🔄 Database reset: POST http://localhost:5000/api/reset-db")
    print("🔧 Debug mode: ON")
    app.run(debug=True, host='0.0.0.0', port=5000)