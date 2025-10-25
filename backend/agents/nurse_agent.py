from uagents import Agent, Context, Model
from dotenv import load_dotenv
import os
from triage import calculate_triage_detailed, format_triage_response

class TriageScore(Model):
    triage_score: int
    reasoning: str
    worsened: bool

load_dotenv()

anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
if not anthropic_api_key:
    raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

MODEL_NAME = 'claude-3-7-sonnet-20250219'

agent = Agent(
    name="nurse_score",
    seed="nurse_score-seed-phrase-12345",
    port=8000,
    mailbox=False
)

@agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info("🏥 Starting Patient Symptoms Monitor...")
    ctx.logger.info(f"📍 Agent address: {agent.address}")

@agent.on_message(model=TriageScore)
async def handle_nurse_score(ctx: Context, sender: str, data: TriageScore):
    score = calculate_triage_detailed(data.current_symptoms, data.current_vitals)
    ctx.logger.info(f"✅ Triage Score: {score['triage_score']}/5")
    ctx.logger.info(f"📤 Sending response to {sender}")
    await ctx.send(sender, TriageScore(triage_score=score['triage_score'], reasoning=score['reasoning'], worsened=score['worsened']))
if __name__ == "__main__":
    agent.run()
