import logging
import json
from collections.abc import AsyncIterable
from typing import Annotated, Callable, Optional, cast
from typing_extensions import TypedDict, NotRequired

from dotenv import load_dotenv
from pydantic import Field
from pydantic_core import from_json
from typing_extensions import TypedDict

from livekit.agents import (
    NOT_GIVEN,
    Agent,
    AgentSession,
    ChatContext,
    FunctionTool,
    JobContext,
    ModelSettings,
    WorkerOptions,
    RoomInputOptions,
    RoomOutputOptions,
    cli,
)
from livekit.plugins import openai, silero
from livekit.plugins.turn_detector.english import EnglishModel

logger = logging.getLogger("structured-output")
load_dotenv()

## This example demonstrates how to use structured output from the LLM to control the TTS.
## The LLM is instructed to provide a TTS directive, which is returned as a TriageStructuredResponse object.
## before generating the response


class TriageStructuredResponse(TypedDict):
    name: Optional[str]
    age: Optional[int]
    gender: Optional[str]
    weight: Optional[int]
    heart_rate: Optional[int]
    temperature: Optional[float]
    respiratory_rate: Optional[int]
    suggested_triage_level: Optional[int]
    patient_notes: Optional[str]
    response: Optional[str]
    voice_instructions: Optional[str]
    finished_talking: Optional[bool]

ordered_keys = [
        "name",
        "age",
        "gender",
        "weight",
        "heart_rate",
        "temperature",
        "respiratory_rate",
        "suggested_triage_level",
        "patient_notes",
        "voice_instructions",
    ]


async def process_structured_output(
    text: AsyncIterable[str],
    callback: Optional[Callable[[TriageStructuredResponse], None]] = None,
) -> AsyncIterable[str]:
    last_response = ""
    acc_text = ""
    async for chunk in text:
        acc_text += chunk
        try:
            resp: TriageStructuredResponse = from_json(acc_text, allow_partial="trailing-strings")
        except ValueError:
            continue

        if callback:
            callback(resp)

        if not resp.get("response"):
            continue

        new_delta = resp["response"][len(last_response) :]
        if new_delta:
            yield new_delta
        last_response = resp["response"]


class MyAgent(Agent):
    def __init__(self, room) -> None:
        self.room = room  # Store room reference to send data
        self.collected_data = {}  # Store collected patient data
        super().__init__(
            instructions=
                "Your name is Apollo. You are a specialized Emergency Room (ER) triage agent."
                "Your job is to collect patient information through conversation and fill out the TriageStructuredResponse."
                "Start by greeting the patient and asking for their name, age, and what brings them to the ER today."
                "Then systematically collect: gender, weight, heart rate, temperature, respiratory rate."
                "Based on their symptoms, assign a triage level (1-5) and provide patient notes."
                "Always be professional, calm, and systematic."
                "Triage Level definitions:"
                "1 = Requires immediate life saving intervention, must be seen immediately"
                "2 = Situation could progress to severe without intervention, seen within 10 minutes"
                "3 = Has the potential to increase in severity if not treated, seen within 30 minutes"
                "4 = Not severe or life threatening, seen within 60 minutes"
                "5 = Not life threatening in any way, can wait for treatment"
                "For measurable values (weight, height, temperature), extract only the number without units."
                "Put any additional information in patient_notes."
                "When you have collected all necessary information, set finished_talking to true.",
            
            # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
            # See all available models at https://docs.livekit.io/agents/models/stt/
            stt="assemblyai/universal-streaming:en",
            # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
            # See all available models at https://docs.livekit.io/agents/models/llm/
            llm="openai/gpt-4.1-mini",
            # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
            # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
            tts="cartesia/sonic-2:9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        )

    async def llm_node(
        self, chat_ctx: ChatContext, tools: list[FunctionTool], model_settings: ModelSettings
    ):
        # not all LLMs support structured output, so we need to cast to the specific LLM type
        llm = cast(openai.LLM, self.llm)
        tool_choice = model_settings.tool_choice if model_settings else NOT_GIVEN
        
        logger.info(f"LLM processing conversation with {len(chat_ctx.messages)} messages")
        
        async with llm.chat(
            chat_ctx=chat_ctx,
            tools=tools,    
            response_format=TriageStructuredResponse,  # <--- this line enforces schema
        ) as stream:
            async for chunk in stream:
                logger.info(f"LLM chunk received: {chunk}")
                yield chunk

    async def conversation_node(self, chat_ctx: ChatContext, model_settings: ModelSettings):
        """Handle the conversation flow and generate structured responses"""
        logger.info(f"Conversation node triggered with {len(chat_ctx.messages)} messages")
        
        # Process the conversation through LLM with structured output
        async for chunk in self.llm_node(chat_ctx, [], model_settings):
            logger.info(f"Conversation chunk: {chunk}")
            yield chunk

    async def tts_node(self, text: AsyncIterable[str], model_settings: ModelSettings):
        instruction_updated = False

        def output_processed(resp: TriageStructuredResponse):
            nonlocal instruction_updated
            logger.info(f"Callback triggered: {resp}\n{resp.get('response')}\n{instruction_updated}")
                # when the response isn't empty, we can assume voice_instructions is complete.
                # (if the LLM sent the fields in the right order)
            if (resp.get("voice_instructions")):
                resp_to_save = {key: resp.get(key) for key in ordered_keys}
                
                # Save to file
                with open("triage_log.jsonl", "a") as f:
                    json.dump(resp_to_save, f)
                    f.write("\n")
                
                # Send data to frontend via LiveKit DataChannel
                try:
                    data_to_send = json.dumps(resp_to_save).encode('utf-8')
                    self.room.local_participant.publish_data(data_to_send, reliable=True)
                    logger.info(f"Sent data to frontend: {resp_to_save}")
                except Exception as e:
                    logger.error(f"Failed to send data to frontend: {e}")

        # process_structured_output strips the TTS instructions and only synthesizes the verbal part
        # of the LLM output
        async for _ in process_structured_output(text, callback=output_processed):
            pass


async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=True)
    logger.info(f"Agent connected to room: {ctx.room.name}")

    agent = MyAgent(ctx.room)  # Pass room reference to agent
    
    session = AgentSession(
        vad=silero.VAD.load(),
        turn_detection=EnglishModel(),
        # Enable preemptive generation for better responsiveness
        preemptive_generation=True,
        # Resume speech if interrupted by background noise
        resume_false_interruption=True,
        false_interruption_timeout=1.0,
    )
    
    await session.start(
        agent=agent, 
        room=ctx.room, 
        room_input_options=RoomInputOptions(
            close_on_disconnect=False,
        ),
        room_output_options=RoomOutputOptions(
            transcription_enabled=True,
        )
    )
    logger.info("Agent session started and listening")

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))