from uagents import Agent, Context, Model
from dotenv import load_dotenv
import os
import chromadb
from triage import calculate_triage_detailed

# ============================================================
# REQUEST/RESPONSE MODELS
# ============================================================

class TriageRequest(Model):
    """Request model for triage assessment"""
    userID: str
    current_symptoms: str
    current_vitals: dict = {}
    history: str = ""
    recall_history: str = ""

class TriageResponse(Model):
    """Response model for triage assessment - full dashboard"""
    success: bool
    triage_score: int = None
    triage_level: str = None
    acuity: str = None
    assessment_summary: dict = None
    clinical_findings: dict = None
    patient_history_relevance: dict = None
    esi_rationale: dict = None
    recommended_resources: list = None
    clinical_recommendations: list = None
    symptom_progression: dict = None
    nursing_notes: list = None
    error: str = None

class PatientHistoryRequest(Model):
    """Request model for patient history"""
    userID: str

class PatientHistoryResponse(Model):
    """Response model for patient history"""
    success: bool
    history: str = None
    error: str = None

# ============================================================
# SETUP
# ============================================================

load_dotenv()

# Validate API keys
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
CHROMADB_API_KEY = os.getenv('CHROMADB_API_KEY')
CHROMADB_TENANT = os.getenv('CHROMADB_TENANT')
CHROMADB_DATABASE = os.getenv('CHROMADB_DATABASE')

if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

# Create agent
agent = Agent(
    name="nurse_score",
    seed="nurse_score-seed-phrase-12345",
    port=8000,
    mailbox=False
)

# Test mode
TEST_MODE = False
#Hardcoded test data for self-test
#Set to True to enable self-test on startup

HARDCODED_TEST_DATA = {
    "userID": "073290f9-73e6-8842-bddc-b568bfcb84b0",
    "current_symptoms": "chest pain and shortness of breath, struggling to walk but no sign of injuries, vision is blurry with no signs of wounds",
    "current_vitals": {
        "heart_rate": 110,
        "blood_pressure": "150/95",
        "temperature": 98.6,
        "respiratory_rate": 22
    },
    "history": "",
    "recall_history": "Previous assessment 2 hours ago: Level 3 - stable with moderate symptoms"
}

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def fetch_patient_history(user_id: str) -> str:
    """Fetch patient history from ChromaDB"""
    try:
        if not CHROMADB_API_KEY or not CHROMADB_TENANT or not CHROMADB_DATABASE:
            print("Warning: ChromaDB credentials not configured")
            return ""
        
        client = chromadb.CloudClient(
            api_key=CHROMADB_API_KEY,
            tenant=CHROMADB_TENANT,
            database=CHROMADB_DATABASE
        )
        
        collection = client.get_collection(user_id)
        
        # Fetch all relevant documents
        patient_info = collection.get(ids=['patient_information'])
        active_conditions = collection.get(ids=['active_conditions'])
        past_conditions = collection.get(ids=['past_conditions'])
        current_meds = collection.get(ids=['current_medications'])
        past_meds = collection.get(ids=['past_medications'])
        recent_vitals = collection.get(ids=['recent_vitals'])
        recent_labs = collection.get(ids=['recent_labs'])
        procedures = collection.get(ids=['procedures'])
        
        history_parts = []
        if patient_info['documents']:
            history_parts.append(patient_info['documents'][0])
        if active_conditions['documents']:
            history_parts.append(active_conditions['documents'][0])
        if current_meds['documents']:
            history_parts.append(current_meds['documents'][0])
        if past_conditions['documents']:
            history_parts.append(past_conditions['documents'][0])
        if past_meds['documents']:
            history_parts.append(past_meds['documents'][0])
        if recent_vitals['documents']:
            history_parts.append(recent_vitals['documents'][0])
        if recent_labs['documents']:
            history_parts.append(recent_labs['documents'][0])
        if procedures['documents']:
            history_parts.append(procedures['documents'][0])
        
        return "\n\n".join(history_parts)
        
    except Exception as e:
        print(f"Error fetching patient history: {e}")
        return ""

# ============================================================
# REST API ENDPOINTS
# ============================================================

@agent.on_rest_post("/triage", TriageRequest, TriageResponse)
async def triage_endpoint(ctx: Context, req: TriageRequest) -> TriageResponse:
    """
    Calculate triage score for a patient
    
    POST /triage
    Expected request format:
    {
        "userID": "patient-id",
        "current_symptoms": "chest pain and shortness of breath",
        "current_vitals": {"heart_rate": 110, "blood_pressure": "150/95"},
        "history": "",
        "recall_history": ""
    }
    
    Returns:
    {
        "success": true,
        "triage_score": 2,
        "reasoning": "High-risk cardiac symptoms...",
       // "worsened": true
    }
    """
    try:
        ctx.logger.info(f"\n📥 REST API Request received:")
        ctx.logger.info(f"   Patient ID: {req.userID}")
        ctx.logger.info(f"   Symptoms: {req.current_symptoms}")
        
        # Fetch patient history if not provided
        history = req.history
        if not history and req.userID:
            ctx.logger.info(f"   📂 Fetching patient history from ChromaDB...")
            history = fetch_patient_history(req.userID)
            if history:
                ctx.logger.info(f"   ✅ Retrieved patient history")
            else:
                ctx.logger.info(f"   ⚠️  No history found, continuing without it")
        
        # Calculate triage score
        ctx.logger.info(f"   🧮 Calculating triage score...")
        score = calculate_triage_detailed(
            symptoms=req.current_symptoms,
            history=history,
            vitals=req.current_vitals,
            recall_history=req.recall_history
        )
        
        ctx.logger.info(f"   ✅ Triage Score: {score['triage_score']}/5")
        ctx.logger.info(f"   🏷️  Level: {score.get('triage_level', 'Unknown')}")
        
        return TriageResponse(
            success=True,
            **score  # Unpack entire dashboard
        )
        
    except Exception as e:
        ctx.logger.error(f"   ❌ Error: {e}")
        return TriageResponse(
            success=False,
            error=f"Failed to calculate triage: {str(e)}"
        )

@agent.on_rest_post("/patient/history", PatientHistoryRequest, PatientHistoryResponse)
async def get_patient_history_endpoint(ctx: Context, req: PatientHistoryRequest) -> PatientHistoryResponse:
    """
    Get patient history from ChromaDB
    
    POST /patient/history
    Expected request format: {"userID": "patient-id"}
    """
    try:
        ctx.logger.info(f"\n📥 Fetching history for patient: {req.userID}")
        
        history = fetch_patient_history(req.userID)
        
        if history:
            ctx.logger.info(f"   ✅ Retrieved patient history\n")
            return PatientHistoryResponse(
                success=True,
                history=history
            )
        else:
            ctx.logger.info(f"   ⚠️  No history found\n")
            return PatientHistoryResponse(
                success=False,
                error="No history found for this patient"
            )
            
    except Exception as e:
        ctx.logger.error(f"   ❌ Error: {e}\n")
        return PatientHistoryResponse(
            success=False,
            error=f"Failed to fetch patient history: {str(e)}"
        )

# ============================================================
# AGENT EVENT HANDLERS
# ============================================================

@agent.on_event("startup")
async def startup(ctx: Context):
    """Initialize agent on startup"""
    ctx.logger.info("="*60)
    ctx.logger.info("🏥 NURSE TRIAGE AGENT")
    ctx.logger.info("="*60)
    ctx.logger.info(f"🔑 Agent address: {agent.address}")
    ctx.logger.info(f"🌐 REST API running on: http://localhost:8000")
    ctx.logger.info(f"📋 Available endpoints:")
    ctx.logger.info(f"   POST /triage          - Calculate triage score")
    ctx.logger.info(f"   POST /patient/history - Get patient history")
    ctx.logger.info("="*60)
    ctx.logger.info("✅ Agent ready to receive requests\n")
    
    if TEST_MODE:
        ctx.logger.info("🧪 TEST MODE ENABLED - Running self-test...")
        await run_self_test(ctx)

async def run_self_test(ctx: Context):
    """Run a self-test with hardcoded data"""
    try:
        ctx.logger.info("\n" + "="*60)
        ctx.logger.info("🧪 RUNNING SELF-TEST WITH HARDCODED DATA")
        ctx.logger.info("="*60)
        
        test_data = HARDCODED_TEST_DATA
        
        ctx.logger.info(f"👤 Patient ID: {test_data['userID']}")
        ctx.logger.info(f"🩺 Symptoms: {test_data['current_symptoms']}")
        ctx.logger.info(f"💓 Vitals: {test_data['current_vitals']}")
        
        # Fetch patient history
        history = test_data['history']
        if test_data['userID']:
            ctx.logger.info(f"📂 Fetching patient history from ChromaDB...")
            history = fetch_patient_history(test_data['userID'])
            if history:
                ctx.logger.info(f"✅ Retrieved patient history from ChromaDB")
            else:
                ctx.logger.info(f"📝 Using provided history instead")
        
        # Calculate triage score
        ctx.logger.info(f"\n🧮 Calculating triage score...")
        score = calculate_triage_detailed(
            symptoms=test_data['current_symptoms'],
            history=history,
            vitals=test_data['current_vitals'],
            recall_history=test_data['recall_history']
        )
        
        # Display results
        ctx.logger.info("\n" + "="*60)
        ctx.logger.info("🏥 TRIAGE ASSESSMENT RESULTS")
        ctx.logger.info("="*60)
        ctx.logger.info(f"📊 ESI Triage Score: {score['triage_score']}/5")
        ctx.logger.info(f"🏷️  Level: {score.get('triage_level', 'Unknown')}")
        ctx.logger.info(f"📊 Acuity: {score.get('acuity', 'Unknown')}")
        
        # Show primary concern
        if 'assessment_summary' in score:
            ctx.logger.info(f"\n📝 PRIMARY CONCERN:")
            ctx.logger.info(f"   {score['assessment_summary'].get('primary_concern', 'N/A')}")
            ctx.logger.info(f"   Immediate Action: {'⚠️ YES' if score['assessment_summary'].get('immediate_action_required') else '✅ NO'}")
        
        # Show symptom progression
        if 'symptom_progression' in score:
            status = score['symptom_progression'].get('status', 'unknown')
            ctx.logger.info(f"\n📈 Symptom Status: {status.upper()}")
        
        ctx.logger.info("="*60 + "\n")
        
        if score['triage_score'] == 1:
            ctx.logger.info("🚨 CRITICAL: Immediate life-saving intervention required!")
        elif score['triage_score'] == 2:
            ctx.logger.info("⚠️  URGENT: Patient should be seen immediately!")
        elif score['triage_score'] == 3:
            ctx.logger.info("🟡 MODERATE: Patient needs attention but can wait briefly")
        elif score['triage_score'] == 4:
            ctx.logger.info("🟢 LOW: Patient can safely wait to be seen")
        else:
            ctx.logger.info("⚪ MINIMAL: Could be handled in clinic/urgent care")
        
        ctx.logger.info("\n✅ Self-test completed successfully!\n")
        
    except Exception as e:
        ctx.logger.error(f"❌ Error during self-test: {e}")
        import traceback
        traceback.print_exc()

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    agent.run()