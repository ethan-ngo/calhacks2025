from uagents import Agent, Context, Model
from dotenv import load_dotenv
import os
import chromadb
from triage import calculate_triage_detailed

# Input model
class PatientData(Model):
    userID: str
    current_symptoms: str
    current_vitals: dict
    history: str = ""
    recall_history: str = ""

# Output model
class TriageScore(Model):
    triage_score: int
    reasoning: str
    worsened: bool

load_dotenv()

anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
if not anthropic_api_key:
    raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

agent = Agent(
    name="nurse_score",
    seed="nurse_score-seed-phrase-12345",
    port=8000,
    mailbox=False
)

# ✅ ADD THIS: Hardcoded test data
TEST_MODE = True  # Set to False to disable auto-testing

HARDCODED_TEST_DATA = {
    "userID": "073290f9-73e6-8842-bddc-b568bfcb84b0",
    "current_symptoms": "feeling scared and anxious",
    "current_vitals": {
        "heart_rate": 110,
        "blood_pressure": "150/95",
        "temperature": 98.6,
        "respiratory_rate": 22
    },
    "history": "",
    "recall_history": "Previous assessment 2 hours ago: Level 3 - stable with moderate symptoms"
}

@agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info("🏥 Starting Patient Triage Agent...")
    ctx.logger.info(f"🔑 Agent address: {agent.address}")
    ctx.logger.info(f"🌐 Running on port: 8000")
    ctx.logger.info("✅ Agent ready to receive messages")
    
    # ✅ ADD THIS: Auto-test on startup if TEST_MODE enabled
    if TEST_MODE:
        ctx.logger.info("🧪 TEST MODE ENABLED - Running self-test...")
        await run_self_test(ctx)

# ✅ ADD THIS: Self-test function
async def run_self_test(ctx: Context):
    """Run a self-test with hardcoded data"""
    try:
        ctx.logger.info("\n" + "="*60)
        ctx.logger.info("🧪 RUNNING SELF-TEST WITH HARDCODED DATA")
        ctx.logger.info("="*60)
        
        # Extract test data
        test_data = HARDCODED_TEST_DATA
        
        ctx.logger.info(f"👤 Patient ID: {test_data['userID']}")
        ctx.logger.info(f"🩺 Symptoms: {test_data['current_symptoms']}")
        ctx.logger.info(f"💓 Vitals: {test_data['current_vitals']}")
        
        # Get patient history from ChromaDB
        history = test_data['history']
        
        if test_data['userID']:
            try:
                ctx.logger.info(f"📂 Fetching patient history from ChromaDB...")
                
                client = chromadb.CloudClient(
                    api_key=os.getenv('CHROMADB_API_KEY'),
                    tenant=os.getenv('CHROMADB_TENANT'),
                    database=os.getenv('CHROMADB_DATABASE')
                )
                
                collection = client.get_collection(test_data['userID'])
                
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
                
                history = "\n\n".join(history_parts)
                ctx.logger.info(f"✅ Retrieved patient history from ChromaDB")
                
            except Exception as e:
                ctx.logger.warning(f"⚠️ Could not fetch patient history: {e}")
                ctx.logger.info(f"📝 Using provided history instead")
        
        print(history)
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
        
        # Score labels
        score_labels = {
            1: "RESUSCITATION - Immediate Life-Saving",
            2: "EMERGENT - High Risk/Severe Distress",
            3: "URGENT - Stable, Multiple Resources",
            4: "LESS URGENT - Stable, One Resource",
            5: "NON-URGENT - Stable, No Resources"
        }
        ctx.logger.info(f"🏷️  Level: {score_labels.get(score['triage_score'], 'Unknown')}")
        
        ctx.logger.info(f"📈 Worsened: {'⚠️ YES - Symptoms have worsened' if score['worsened'] else '✅ NO - Stable or improved'}")
        ctx.logger.info(f"\n📝 REASONING:")
        ctx.logger.info(f"   {score['reasoning']}")
        ctx.logger.info("="*60 + "\n")
        
        # Recommendations based on score
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

@agent.on_message(model=PatientData)
async def handle_triage_request(ctx: Context, sender: str, data: PatientData):
    """Handle incoming triage requests"""
    try:
        ctx.logger.info(f"\n📥 Received triage request from {sender}")
        ctx.logger.info(f"👤 Patient ID: {data.userID}")
        ctx.logger.info(f"🩺 Symptoms: {data.current_symptoms}")
        
        # Get patient history from ChromaDB
        history = data.history
        
        if not history and data.userID:
            try:
                ctx.logger.info(f"📂 Fetching patient history from ChromaDB...")
                
                client = chromadb.CloudClient(
                    api_key=os.getenv('CHROMADB_API_KEY'),
                    tenant=os.getenv('CHROMADB_TENANT'),
                    database=os.getenv('CHROMADB_DATABASE')
                )
                
                collection = client.get_collection(data.userID)
                
                patient_info = collection.get(ids=['patient_information'])
                active_conditions = collection.get(ids=['active_conditions'])
                current_meds = collection.get(ids=['current_medications'])
                
                history_parts = []
                if patient_info['documents']:
                    history_parts.append(patient_info['documents'][0])
                if active_conditions['documents']:
                    history_parts.append(active_conditions['documents'][0])
                if current_meds['documents']:
                    history_parts.append(current_meds['documents'][0])
                
                history = "\n\n".join(history_parts)
                ctx.logger.info(f"✅ Retrieved patient history")
                
            except Exception as e:
                ctx.logger.warning(f"⚠️ Could not fetch patient history: {e}")
        
        # Calculate triage score
        ctx.logger.info(f"🧮 Calculating triage score...")
        score = calculate_triage_detailed(
            symptoms=data.current_symptoms,
            history=history,
            vitals=data.current_vitals,
            recall_history=data.recall_history
        )
        
        ctx.logger.info(f"✅ Triage Score: {score['triage_score']}/5")
        ctx.logger.info(f"📊 Reasoning: {score['reasoning'][:100]}...")
        ctx.logger.info(f"📈 Worsened: {score['worsened']}")
        
        # Send response
        ctx.logger.info(f"📤 Sending response to {sender}")
        await ctx.send(
            sender,
            TriageScore(
                triage_score=score['triage_score'],
                reasoning=score['reasoning'],
                worsened=score['worsened']
            )
        )
        
        ctx.logger.info(f"✅ Response sent successfully")
        
    except Exception as e:
        ctx.logger.error(f"❌ Error during triage: {e}")
        
        try:
            await ctx.send(
                sender,
                TriageScore(
                    triage_score=3,
                    reasoning=f"Error: {str(e)}. Defaulting to moderate urgency.",
                    worsened=False
                )
            )
        except Exception as send_error:
            ctx.logger.error(f"❌ Failed to send error response: {send_error}")

# ✅ OPTIONAL: Add periodic testing (runs every 60 seconds)
# Uncomment this if you want continuous testing
"""
@agent.on_interval(period=60.0)
async def periodic_test(ctx: Context):
    ctx.logger.info("🔄 Running periodic self-test...")
    await run_self_test(ctx)
"""

if __name__ == "__main__":
    agent.run()
