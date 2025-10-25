from uagents import Agent, Context, Model
from dotenv import load_dotenv
import os

class PatientData(Model):
    age: int
# Load environment variables
load_dotenv()

# Configure Anthropic Claude
anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
if not anthropic_api_key:
    raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

# Model configuration
MODEL_NAME = 'claude-3-7-sonnet-20250219'  # Latest Claude model

# Create agent
agent = Agent(
    name="nurse_score",
    seed="nurse_score-seed-phrase-12345",  # Change this for your agent
    port=8000,
    mailbox=True  # Required for Agentverse deployment
)

@agent.on_event("startup")
async def startup(ctx: Context):
    """Initialize agent on startup"""
    ctx.logger.info("🏥 Starting Patient Symptoms Monitor...")
    ctx.logger.info(f"📍 Agent address: {agent.address}")

# Handle requests from the wrapper agent
@agent.on_message(model=PatientData)
async def handle_nurse_score(ctx: Context, sender: str, data: PatientData):
    return