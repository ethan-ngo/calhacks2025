import asyncio
import logging

from dotenv import load_dotenv

from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    UserStateChangedEvent,
    WorkerOptions,
    cli,
)
from livekit.plugins import cartesia, deepgram, openai, silero

class TriageAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions=(
                "Your name is Apollo. You would interact with users via voice."
                "You are a specialized Emergency Room (ER) triage monitoring agent trained to assess whether a patient’s condition is improving or worsening."
                "with that in mind keep your responses concise and to the point."
                "Keep responses short, direct, and professional."
                "do not use emojis, asterisks, markdown, or other special characters in your responses."
                "Maintain a serious, systematic, and calm tone — you are focused on evaluating the patient’s condition accurately."
                "Listen to the patient’s description of symptoms, pain levels, and any changes since the last check."
                "Ask one question at a time to determine changes in pain, breathing, consciousness, bleeding, or discomfort."
                "you will speak english to the user",
            )
        )
logger = logging.getLogger("triage-agent")

load_dotenv()

async def entrypoint(ctx: JobContext):
    session = AgentSession(
        vad=silero.VAD.load(),
        llm=openai.LLM(model="gpt-4o-mini"),
        stt=deepgram.STT(),
        tts=cartesia.TTS(),
        user_away_timeout=12.5,
    )

    inactivity_task: asyncio.Task | None = None

    async def user_presence_task():
        # try to ping the user 3 times, if we get no answer, close the session
        for _ in range(3):
            await session.generate_reply(
                instructions=(
                    "The patient has been silent. Ask gently if they are still feeling okay "
                    "or if their symptoms have worsened."
                )
            )
            await asyncio.sleep(10)

        await session.generate_reply(
            instructions=(
                "No response from the patient. If user made any mention of worsening condition, escalate to nurse for manual follow-up."
            )
        )
        session.shutdown()

    @session.on("user_state_changed")
    def _user_state_changed(ev: UserStateChangedEvent):
        nonlocal inactivity_task
        if ev.new_state == "away":
            inactivity_task = asyncio.create_task(user_presence_task())
            return

        # ev.new_state: listening, speaking, ..
        if inactivity_task is not None:
            inactivity_task.cancel()

    await session.start(agent=TriageAgent(), room=ctx.room)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
