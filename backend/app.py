from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import sys
from datetime import datetime
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

# Root endpoint for health checks
@app.route('/')
def home():
    return jsonify({
        "status": "ok",
        "message": "TriageFlow API is running",
        "version": "1.0.0"
    })

# In-memory storage
patient_histories = {}  # For chat history
patient_data_store = {}  # For patient information from nurse dashboard
triage_alerts = {}  # For tracking patients who need triage updates

def generate_vague_response(assessment: dict, is_worsening: bool) -> str:
    """Generate vague but dynamic response for patient"""
    
    triage_score = assessment.get('triage_score', 3)
    status = assessment.get('symptom_progression', {}).get('status', 'unknown')
    
    # Vague responses based on urgency
    if is_worsening:
        responses = [
            "Thank you for updating us on your condition. We've noted your report and medical staff will be notified.",
            "We appreciate you letting us know about your symptoms. Your information has been recorded and the care team has been alerted.",
            "Thank you for the update. We're monitoring your situation and will adjust your care as needed."
        ]
    elif status == 'improving':
        responses = [
            "Thank you for the update. We're glad to hear there's been some improvement. Continue to monitor your symptoms.",
            "We've noted your progress. Please continue to rest and let us know if anything changes.",
            "Thank you for checking in. Your status has been updated in our system."
        ]
    else:
        responses = [
            "Thank you for the information. We're monitoring your condition and will keep you updated.",
            "We've received your update. Please continue to wait and we'll call you when ready.",
            "Thank you for letting us know. Your status has been recorded."
        ]
    
    # Add urgency hint for very urgent cases without being too specific
    if triage_score <= 2:
        return responses[0] + " Please remain in the waiting area - you will be seen shortly."
    elif triage_score == 3:
        return responses[0]
    else:
        return responses[1]


def send_patient_link_sms(phone_number: str, patient_name: str, link: str) -> bool:
    """Send patient portal link via SMS using Twilio"""

    try:
        from twilio.rest import Client

        # Get Twilio credentials from environment
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        from_number = os.getenv('TWILIO_PHONE_NUMBER')

        # Validate credentials
        if not all([account_sid, auth_token, from_number]):
            print("⚠️ Twilio credentials not found in .env file")
            return False

        # Create Twilio client
        client = Client(account_sid, auth_token)

        # Send SMS
        message = client.messages.create(
            body=f"Hello {patientname}, access your ER wait portal: {link}",
            from_=from_number,
            to=phone_number
        )

        print(f"\n📱 SMS Sent Successfully!")
        print(f"   To: {phone_number}")
        print(f"   Message SID: {message.sid}")
        print(f"   Status: {message.status}\n")

        return True

    except ImportError:
        print("❌ Twilio not installed. Install with: pip install twilio")
        return False
    except Exception as e:
        print(f"❌ SMS sending failed: {e}")
        print(f"   Phone: {phone_number}")
        print(f"   Error type: {type(e).name}")
        return False

@app.route('/patient/data/<patient_id>', methods=['GET'])
def get_patient_data(patient_id):
    """Get patient data by ID"""
    patient = patient_data_store.get(patient_id)
    if patient:
        return jsonify({"success": True, "data": patient})
    else:
        return jsonify({"success": False, "data": {}}), 404

@app.route('/patient/chat', methods=['POST'])
def patient_chat():
    """Patient chat endpoint - AI-powered triage assessments"""
    try:
        if not TRIAGE_AVAILABLE:
            return jsonify({
                "response": "Medical assessment system unavailable.",
                "success": False
            }), 503
        
        data = request.json
        if not data or 'message' not in data:
            return jsonify({"error": "No message provided"}), 400
        
        message = data.get('message')
        patient_id = data.get('patientId', 'default_patient')
        
        print(f"\n📨 Received: {message[:50]}... from {patient_id}")
        
        # Get patient history
        history = patient_histories.get(patient_id, [])
        
        # Build recall history
        recall_text = ""
        if history:
            recent = [h for h in history if h.get('role') == 'assistant'][-3:]
            recall_entries = []
            
            for i, h in enumerate(recent):
                timestamp = h.get('timestamp', 'unknown')
                score = h.get('triage_score', 'N/A')
                symptoms = h.get('symptoms', 'N/A')
                recall_entries.append(
                    f"Assessment {i+1} ({timestamp}):\n"
                    f"  Symptoms: {symptoms[:100]}...\n"
                    f"  Triage Score: {score}/5"
                )
            
            recall_text = "\n\n".join(recall_entries)
        
        # Call Claude AI
        print("🤔 Analyzing with Claude AI...")
        assessment = calculate_triage_detailed(
            symptoms=message,
            history="",
            vitals=None,
            recall_history=recall_text
        )
        
        # Format response
        response_text = format_triage_response(assessment)
        
        # Store in history
        current_time = datetime.now().isoformat()
        
        history.append({
            'role': 'user',
            'text': message,
            'symptoms': message,
            'timestamp': current_time
        })
        
        history.append({
            'role': 'assistant',
            'text': response_text,
            'symptoms': message,
            'triage_score': assessment['triage_score'],
            'reasoning': assessment.get('assessment_summary', {}).get('primary_concern', ''),
            'timestamp': current_time
        })
        
        patient_histories[patient_id] = history[-20:]
        
        # Check if triage score has changed (lower number = more urgent)
        current_triage = assessment['triage_score']
        patient_data = patient_data_store.get(patient_id, {})
        original_triage = patient_data.get('triageScore', 5)
        
        # Create alert if triage score has changed significantly (± 1 or more)
        triage_changed = abs(current_triage - original_triage) >= 1
        
        if triage_changed and current_triage != original_triage:
            triage_alerts[patient_id] = {
                'patient_name': patient_data.get('name', 'Unknown'),
                'patient_id': patient_id,
                'original_triage': original_triage,
                'new_triage': current_triage,
                'new_triage_level': assessment.get('triage_level'),
                'acuity': assessment.get('acuity'),
                'reason': assessment.get('assessment_summary', {}).get('primary_concern', ''),
                'symptoms': message,
                'timestamp': current_time,
                'status': 'pending'  # pending, accepted, rejected
            }
            
            if current_triage < original_triage:
                print(f"⚠️ ALERT: Triage WORSENED from {original_triage} to {current_triage}")
            else:
                print(f"📊 ALERT: Triage improved from {original_triage} to {current_triage}")
        
        print(f"✅ Triage Score: {assessment['triage_score']}/5\n")
        
        # Create vague but dynamic response for patient
        vague_response = generate_vague_response(assessment, current_triage < original_triage)
        
        return jsonify({
            "response": vague_response,
            "triage_score": assessment.get('triage_score'),
            "alert_created": triage_changed,
            "triage_direction": "worse" if current_triage < original_triage else "better" if current_triage > original_triage else "same",
            "success": True
        })
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "response": "Error processing request.",
            "success": False,
            "error": str(e)
        }), 500

@app.route('/nurse/submit', methods=['POST'])
def nurse_submit():
    """Store patient data and send portal link to patient's phone"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Generate unique patient ID
        import uuid
        patient_id = str(uuid.uuid4())

        phone_number = data.get('phoneNumber', '')
        patient_name = data.get('name', 'Unknown')

            # Store patient data
        patient_data_store[patient_id] = {
            'name': patient_name,
            'age': data.get('age', ''),
            'gender': data.get('gender', ''),
            'weight': data.get('weight', ''),
            'phoneNumber': phone_number,
            'heartRate': data.get('heartRate', ''),
            'temperature': data.get('temperature', ''),
            'respiratoryRate': data.get('respiratoryRate', ''),
            'bloodPressure': data.get('bloodPressure', ''),
            'painSeverity': data.get('painSeverity', ''),
            'symptoms': data.get('symptoms', ''),
            'triageScore': data.get('triageScore', ''),
            'created_at': datetime.now().isoformat()
        }
        # Generate patient wait link
        patient_link = f"https://calhacks2025-nine.vercel.app/patientwait/{patient_id}"

        print(f"✅ Patient {patient_name} registered with ID: {patient_id}")

        # Send SMS if phone number provided
        sms_sent = False
        sms_error = None

        if phone_number and phone_number.strip():
            try:
                sms_sent = send_patient_link_sms(phone_number, patient_name, patient_link)
                if sms_sent:
                    print(f"📱 SMS sent to {phone_number}")
                else:
                    print(f"⚠️ SMS service not configured - link not sent")
            except Exception as e:
                sms_error = str(e)
                print(f"❌ Failed to send SMS: {e}")
        else:
            print(f"⚠️ No phone number provided - SMS not sent")

        return jsonify({
            "success": True,
            "patient_id": patient_id,
            "patient_link": patient_link,
            "sms_sent": sms_sent,
            "sms_error": sms_error,
            "message": f"Patient registered. {('SMS sent to patient.' if sms_sent else 'No phone number - manual notification required.')}"
        })

    except Exception as e:
        print(f"❌ Error saving patient data: {e}")
        return jsonify({
            "error": str(e),
            "success": False
        }), 500


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
@app.route('/alerts', methods=['GET'])
def get_alerts():
    """Get all pending triage alerts"""
    try:
        # Filter for pending alerts only
        pending_alerts = {
            pid: alert for pid, alert in triage_alerts.items() 
            if alert.get('status') == 'pending'
        }
        
        return jsonify({
            "success": True,
            "alerts": pending_alerts
        })
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "success": False
        }), 500

@app.route('/alerts/<patient_id>', methods=['POST'])
def update_alert(patient_id):
    """Accept or reject a triage alert"""
    try:
        data = request.json
        if not data or 'action' not in data:
            return jsonify({"error": "No action provided"}), 400
        
        action = data.get('action')  # 'accept' or 'reject'
        
        if patient_id not in triage_alerts:
            return jsonify({"error": "Alert not found"}), 404
        
        alert = triage_alerts[patient_id]
        
        if action == 'accept':
            # Update patient's triage score
            if patient_id in patient_data_store:
                patient_data_store[patient_id]['triageScore'] = alert['new_triage']
                patient_data_store[patient_id]['triageLevel'] = alert['new_triage_level']
            
            alert['status'] = 'accepted'
            print(f"✅ Alert accepted for {alert['patient_name']}: {alert['original_triage']} → {alert['new_triage']}")
            
            return jsonify({
                "success": True,
                "message": "Triage updated successfully",
                "new_triage": alert['new_triage']
            })
            
        elif action == 'reject':
            alert['status'] = 'rejected'
            print(f"❌ Alert rejected for {alert['patient_name']}")
            
            return jsonify({
                "success": True,
                "message": "Alert dismissed"
            })
        else:
            return jsonify({"error": "Invalid action"}), 400
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "success": False
        }), 500

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
