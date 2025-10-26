from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import sys
from datetime import datetime
from livekit import api
import requests

# Add agents directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agents'))

# Import triage functions
try:
    from triage import calculate_triage_detailed, format_triage_response
    TRIAGE_AVAILABLE = True
    print("✅ Triage functions loaded successfully")
except ImportError as e:
    TRIAGE_AVAILABLE = False
    print(f"❌ Could not import triage functions: {e}")

app = Flask(__name__)
CORS(app)
load_dotenv()

# Agent endpoints
AGENTS = {
    "nurse": "http://127.0.0.1:8000",
    "patient": "http://127.0.0.1:8001"
}

# In-memory storage
patient_histories = {}  # For chat history
patient_data_store = {}  # For patient information from nurse dashboard
triage_alerts = {}  # For tracking patients who need triage updates

@app.route('/nurse/triage', methods=['POST'])
def nurse_triage():
    """Nurse triage assessment - calls triage function directly"""
    try:
        if not TRIAGE_AVAILABLE:
            return jsonify({
                "error": "Triage system unavailable",
                "triage_score": 3
            }), 503
        
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Extract data from payload
        user_id = data.get('userID', 'unknown')
        vitals = data.get('current_vitals', {})
        symptoms = data.get('current_symptoms', '')
        history = data.get('history', '')
        recall_history = data.get('recall_history', '')
        
        print(f"\n🏥 Nurse triage request for: {user_id}")
        print(f"   Symptoms: {symptoms[:100] if isinstance(symptoms, str) else str(symptoms)[:100]}...")
        
        # Call triage function
        assessment = calculate_triage_detailed(
            symptoms=symptoms,
            history=history,
            vitals=vitals,
            recall_history=recall_history
        )
        
        # Extract key info for response
        triage_score = assessment.get('triage_score')
        primary_concern = assessment.get('assessment_summary', {}).get('primary_concern', '')
        
        print(f"✅ Triage complete: Score {triage_score}/5\n")
        
        return jsonify({
            "triage_score": triage_score,
            "triage_level": assessment.get('triage_level'),
            "acuity": assessment.get('acuity'),
            "reasoning": primary_concern,
            "worsened": assessment.get('symptom_progression', {}).get('status') == 'worsening',
            "assessment": assessment,  # Full assessment for dashboard
            "success": True
        })
        
    except Exception as e:
        print(f"❌ Triage error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": str(e),
            "triage_score": 3,  # Default to urgent
            "success": False
        }), 500

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

@app.route('/voice/process', methods=['POST'])
def process_voice_transcription():
    """Process voice transcription and extract structured patient data using Anthropic Claude"""
    try:
        from anthropic import Anthropic
        import json
        
        data = request.json
        transcription = data.get('transcription', '')
        
        if not transcription:
            return jsonify({"error": "No transcription provided"}), 400
        
        # Initialize Anthropic client
        client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        
        # Create prompt for structured extraction
        prompt = f"""You are Apollo, a specialized Emergency Room (ER) triage agent. 
Extract patient information from the following transcription and return it in JSON format.

Transcription: "{transcription}"

Extract and return ONLY a JSON object with these exact fields (use null if information is not mentioned):
{{
  "name": "patient full name or null",
  "age": "age as number or null",
  "gender": "Male/Female/Other or null",
  "weight": "weight in kg as number or null",
  "heart_rate": "heart rate as number or null",
  "temperature": "temperature in Celsius as number or null",
  "respiratory_rate": "respiratory rate as number or null",
  "suggested_triage_level": "1-5 based on severity (1=immediate, 5=non-urgent) or null",
  "patient_notes": "summary of symptoms and complaint"
}}

Triage Level Guidelines:
- Level 1 (Immediate): Life-threatening (chest pain, severe bleeding, difficulty breathing)
- Level 2 (Emergent): High risk, severe pain (fractures, severe burns)
- Level 3 (Urgent): Moderate symptoms (minor fractures, moderate pain)
- Level 4 (Less Urgent): Minor conditions (sprains, cold symptoms)
- Level 5 (Non-Urgent): Minimal symptoms (minor cuts, chronic stable conditions)

Return ONLY the JSON object, no other text."""
        
        # Call Claude API
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        # Extract the response text
        response_text = response.content[0].text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
            response_text = response_text.strip()
        
        # Parse JSON
        patient_data = json.loads(response_text)
        
        return jsonify(patient_data)
        
    except Exception as e:
        print(f"Error processing voice transcription: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Failed to process transcription: {str(e)}"}), 500

@app.route('/getToken', methods=["POST"])
def get_token():
    # Generate a new token every request (kept for backwards compatibility)
    token = (
        api.AccessToken(os.getenv('LIVEKIT_API_KEY'), os.getenv('LIVEKIT_API_SECRET'))
        .with_identity("user_" + os.urandom(4).hex())  # unique identity
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room="my-room",
                can_publish=True,
                can_subscribe=True
            )
        )
    )
    return token.to_jwt()

if __name__ == '__main__':
    print("Starting Flask Medical Triage API...")
    app.run(host='127.0.0.1', port=5000, debug=True)
