import logging

from dotenv import load_dotenv

from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RoomInputOptions,
    RoomOutputOptions,
    RunContext,
    WorkerOptions,
    cli,
    metrics,
)
from livekit.agents.llm import function_tool
from livekit.plugins import silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

# uncomment to enable Krisp background voice/noise cancellation
# from livekit.plugins import noise_cancellation

logger = logging.getLogger("basic-agent")

load_dotenv()

class MyAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="Your name is Apollo. You would interact with users via voice."
            "You are a specialized Emergency Room (ER) triage monitoring agent trained to assess whether a patient’s condition is improving or worsening."
            "with that in mind keep your responses concise and to the point."
            "Keep responses short, direct, and professional."
            "do not use emojis, asterisks, markdown, or other special characters in your responses."
            "Maintain a serious, systematic, and calm tone — you are focused on evaluating the patient’s condition accurately."
            "Listen to the patient’s description of symptoms, pain levels, and any changes since the last check."
            "Ask one question at a time to determine changes in pain, breathing, consciousness, bleeding, or discomfort."
            "you will speak english to the user",
        )

    async def on_enter(self):
        # when the agent is added to the session, it'll generate a reply
        # according to its instructions
        self.session.generate_reply()

    # all functions annotated with @function_tool will be passed to the LLM when this
    # agent is active
    @function_tool
    async def update_triage_level(
        self, context: RunContext, patient_name: str,triage_level: str, notes: str = ""
    ):
        """
        Called when the agent determines the patient's condition has changed.
        Updates the patient's triage level in the system and logs any relevant notes.

        Args:
            patient_name: Name or ID of the patient,
            prev_triage_level: Old triage level(1-5),
            triage_level: New triage level (1-5, 
            1 = Requires immediate life saving intervention, must be seen immediately
            2 = Situation could progress to triage sever without intervention, seen within 10 minutes
            3 = Has the potential to increase in severity if not treated, Seen within 30 minutes
            4 = Not severe or life threatening. seen within 60 minutes
            5 = Not life threatening in any way. Can wait for treatment
            )
            notes: Optional notes about the patient's condition or symptoms
        """

        logger.info(
            f"Updating triage for {patient_name}: level={triage_level}, notes={notes}"
        )

        # Here you could also call a backend API, database, or notify a nurse
        # For now, just log and return confirmation
        return f"Triage level for {patient_name} updated to {triage_level}."


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    # each log entry will include these fields
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt="assemblyai/universal-streaming:en",
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm="openai/gpt-4.1-mini",
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts="cartesia/sonic-2:9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
        # sometimes background noise could interrupt the agent session, these are considered false positive interruptions
        # when it's detected, you may resume the agent's speech
        resume_false_interruption=True,
        false_interruption_timeout=1.0,
    )

    # log metrics as they are emitted, and total usage after session is over
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    # shutdown callbacks are triggered when the session is over
    ctx.add_shutdown_callback(log_usage)

    await session.start(
        agent=MyAgent(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            # uncomment to enable Krisp BVC noise cancellation
            # noise_cancellation=noise_cancellation.BVC(),
        ),
        room_output_options=RoomOutputOptions(transcription_enabled=True),
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
