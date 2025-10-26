from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
from livekit import api
import requests

app = Flask(__name__)
CORS(app)
load_dotenv()

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
