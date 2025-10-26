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
        super().__init__(
            instructions=
                "Your name is Apollo. You will listen to the users and fill out the necessary information in TriageStructuredResponse."
                "You are a specialized Emergency Room (ER) agent tasked with filling out the patients necessary information."
                "Maintain a serious, systematic, and calm tone — you are focused on collecting the patient's information accurately."
                "Listen to the patient's description of symptoms, pain levels, and any changes since the last check."
                "you will speak to the user once you have finished listening and taking all his data."
                "Whenever I mention the following terms this is what I mean."
                "Triage Level, a 1-5 scale for severity of patient assigning each number to a priority. the definitions for 1-5 are below."
                "1 = Requires immediate life saving intervention, must be seen immediately"
                "2 = Situation could progress to triage severe without intervention, seen within 10 minutes"
                "3 = Has the potential to increase in severity if not treated, seen within 30 minutes"
                "4 = Not severe or life threatening, seen within 60 minutes"
                "5 = Not life threatening in any way, can wait for treatment"
                "Whenever user mentions anything measurable(e.g. weight, height, temperature) do not include the unit only take the number."
                "You will write anything that could be outside the scope of the properties into patient_notes"
                "You will save the information."
                ,
            
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
        async with llm.chat(
            chat_ctx=chat_ctx,
            tools=tools,    
            response_format=TriageStructuredResponse,  # <--- this line enforces schema
        ) as stream:
            async for chunk in stream:
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

    async def transcription_node(self, text: AsyncIterable[str], model_settings: ModelSettings):
        # transcription_node needs to return what the agent would say, minus the TTS instructions
        return Agent.default.transcription_node(
            self, process_structured_output(text), model_settings
        )


async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=True)
    logger.info(f"Agent connected to room: {ctx.room.name}")

    agent = MyAgent(ctx.room)  # Pass room reference to agent
    
    session = AgentSession(
        vad=silero.VAD.load(),
        turn_detection=EnglishModel(),
    )
    
    await session.start(agent=agent, room=ctx.room, room_input_options=RoomInputOptions(close_on_disconnect=False))
    logger.info("Agent session started and listening")

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))