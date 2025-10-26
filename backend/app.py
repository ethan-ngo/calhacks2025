from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# Agent endpoints
AGENTS = {
    "nurse": "http://127.0.0.1:8000",
    "patient": "http://127.0.0.1:8001"
}

@app.route('/nurse/triage', methods=['POST'])
def nurse_triage():
    """Nurse triage assessment"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"})
        
        # Call nurse agent
        response = requests.post(f"{AGENTS['nurse']}/triage", json=data)
        response.raise_for_status()
        
        result = response.json()
        
        return jsonify({
            "triage_score": result.get('triage_score'),
            "reasoning": result.get('reasoning'),
            "worsened": result.get('worsened', False)
        })
        
    except requests.RequestException as e:
        return jsonify({"error": f"Failed to connect to nurse agent: {str(e)}"})
    except Exception as e:
        return jsonify({"error": f"Triage failed: {str(e)}"})

@app.route('/patient/assess', methods=['POST'])
def patient_assess():
    """Patient assessment with history"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"})
        
        # Call patient agent
        response = requests.post(f"{AGENTS['patient']}/assess", json=data)
        response.raise_for_status()
        
        result = response.json()
        
        return jsonify({
            "triage_score": result.get('triage_score'),
            "reasoning": result.get('reasoning'),
            "worsened": result.get('worsened', False),
        })
        
    except requests.RequestException as e:
        return jsonify({"error": f"Failed to connect to patient agent: {str(e)}"})
    except Exception as e:
        return jsonify({"error": f"Assessment failed: {str(e)}"})

if __name__ == '__main__':
    print("Starting Flask Medical Triage API...")
    app.run(host='127.0.0.1', port=5000, debug=True)
