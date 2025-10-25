"""
Patient Symptoms Monitoring Agent for Fetch.ai Agentverse
A medical triage AI agent powered by Anthropic Claude

This agent:
- Receives patient symptoms and current triage score
- Analyzes if symptoms have worsened
- Provides updated triage assessment
- Offers medical guidance and recommendations
"""

import os
from datetime import datetime, timezone
from uuid import uuid4
from dotenv import load_dotenv

from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatMessage,
    ChatAcknowledgement,
    TextContent,
    chat_protocol_spec
)

# Import triage function
from triage import calculate_triage_detailed, format_triage_response

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
    name="patient_monitor",
    seed="patient-monitor-seed-phrase-12345",  # Change this for your agent
    port=8000,
    mailbox=True  # Required for Agentverse deployment
)

# Initialize chat protocol
chat_proto = Protocol(spec=chat_protocol_spec)

# Helper function to create text chat messages
def create_text_chat(text: str) -> ChatMessage:
    """Create a ChatMessage with TextContent"""
    return ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=uuid4(),
        content=[TextContent(text=text, type="text")]
    )


@agent.on_event("startup")
async def startup(ctx: Context):
    """Initialize agent on startup"""
    ctx.logger.info("🏥 Starting Patient Symptoms Monitor...")
    ctx.logger.info(f"📍 Agent address: {agent.address}")
    


@chat_proto.on_message(ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    """Handle incoming chat messages with symptoms and triage info"""
    
    try:
        # Extract text from message content
        user_text = ""
        for item in msg.content:
            if isinstance(item, TextContent):
                user_text = item.text
                break
        
        if not user_text:
            ctx.logger.warning("No text content in message")
            return
        
        # Log incoming message
        ctx.logger.info(f"📨 Symptoms report from {sender}: {user_text[:50]}...")

        
        # Send acknowledgement
        await ctx.send(sender, ChatAcknowledgement(
            timestamp=datetime.now(timezone.utc),
            acknowledged_msg_id=msg.msg_id
        ))
        
        # Get patient history from storage
        patient_histories = ctx.storage.get("patient_histories") or {}
        history = patient_histories.get(sender, [])
        
        ctx.logger.info(f"📚 Retrieved {len(history)} previous messages for {sender}")
        
        # Format recall history for triage calculation
        recall_text = ""
        if history:
            # Format recent history with structured information
            recent_assessments = [h for h in history if h['role'] == 'assistant'][-3:]
            recall_entries = []
            
            for i, h in enumerate(recent_assessments):
                timestamp = h.get('timestamp', 'unknown time')
                triage_score = h.get('triage_score', 'N/A')
                symptoms = h.get('symptoms', 'N/A')
                recall_entries.append(
                    f"Assessment {i+1} ({timestamp}):\n"
                    f"  Symptoms: {symptoms[:100]}...\n"
                    f"  Triage Score: {triage_score}/5"
                )
            
            recall_text = "\n\n".join(recall_entries)
        
        # Generate assessment from Claude
        ctx.logger.info("🤔 Analyzing symptoms with Claude...")
        
        # Calculate triage assessment with full history context
        assessment = calculate_triage_detailed(
            symptoms=user_text,
            history="",  # Can parse from user message if structured
            vitals=None,  # Can parse from user message if structured
            recall_history=recall_text
        )
        
        # Format the response nicely
        response_text = format_triage_response(assessment)
        
        ctx.logger.info(f"✅ Triage Score: {assessment['triage_score']}/5")
        
        # Store structured message in history
        current_timestamp = datetime.now(timezone.utc).isoformat()
        
        # Add user message to history
        history.append({
            'role': 'user',
            'text': user_text,
            'symptoms': user_text,
            'timestamp': current_timestamp,
            'message_id': str(msg.msg_id)
        })
        
        # Add assistant response to history with full assessment details
        history.append({
            'role': 'assistant',
            'text': response_text,
            'symptoms': user_text,  # Keep original symptoms for reference
            'triage_score': assessment['triage_score'],
            'reasoning': assessment['reasoning'],
            'recommendation': assessment['recommendation'],
            'emergency_keywords': assessment.get('emergency_keywords', []),
            'worsened': assessment.get('worsened', False),
            'timestamp': current_timestamp
        })
        
        # Keep last 20 messages (10 exchanges) in storage
        patient_histories[sender] = history[-20:]
        ctx.storage.set("patient_histories", patient_histories)
        
        ctx.logger.info(f"💾 Stored message history ({len(patient_histories[sender])} messages total)")
        
        # Track stats
        total = ctx.storage.get("total_assessments") or 0
        ctx.storage.set("total_assessments", total + 1)
        
        # Send assessment back
        await ctx.send(sender, create_text_chat(response_text))
        
        ctx.logger.info(f"💬 Assessment sent to {sender}")
        
    except Exception as e:
        ctx.logger.error(f"❌ Error processing symptoms: {e}")
        
        # Check for specific error types
        error_str = str(e)
        
        if "rate_limit" in error_str.lower() or "429" in error_str:
            error_msg = """⚠️ **Rate Limit Reached**

I've hit the API rate limits. Please wait a moment and try again.

**What to do:**
- ⏰ Wait 1 minute and try again
- 📊 Check your API usage at console.anthropic.com
"""
        elif "api_key" in error_str.lower() or "401" in error_str:
            error_msg = """⚠️ **API Key Error**

There's an issue with the API key configuration.

**Please check:**
- API key is valid
- API key has proper permissions
- Account has available credits
"""
        else:
            error_msg = f"""❌ **Error Processing Symptoms**

{str(e)[:200]}

Please try:
- Reformatting your symptoms report
- Including both symptoms and current triage score
- Waiting a moment and trying again

If symptoms are severe, please seek immediate medical attention.
"""
        
        await ctx.send(sender, create_text_chat(error_msg))


@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    """Handle message acknowledgements"""
    ctx.logger.debug(f"✓ Message {msg.acknowledged_msg_id} acknowledged by {sender}")


# Include the chat protocol
agent.include(chat_proto, publish_manifest=True)


if __name__ == "__main__":
    print("🏥 Starting Patient Symptoms Monitor...")
    print(f"📍 Agent address: {agent.address}")
    
    if anthropic_api_key:
        print("✅ Anthropic Claude API configured")
        print(f"   Using model: {MODEL_NAME}")
    else:
        print("❌ ERROR: ANTHROPIC_API_KEY not set")
        print("   Please add it to your .env file")
        print("   Get your key from: https://console.anthropic.com")
        exit(1)
    
    print("\n🎯 Agent Features:")
    print("   • Medical triage assessment with Claude 3.5 Sonnet")
    print("   • Symptom worsening detection")
    print("   • Triage score evaluation (1-5 scale)")
    print("   • Patient history tracking")
    print("   • Medical guidance and recommendations")
    print("   • Ready for Agentverse deployment")
    
    print("\n📋 Usage:")
    print("   Send messages with: 'Symptoms: [description], Current Triage Score: [1-5]'")
    print("   Example: 'Symptoms: chest pain and shortness of breath, Current Triage Score: 3'")
    
    print("\n✅ Agent is running! Connect via ASI One or send messages programmatically.")
    print("   Press Ctrl+C to stop.\n")
    
    agent.run()
