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
    cli,
)
from livekit.plugins import openai, silero, assemblyai
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
    def __init__(self) -> None:
        super().__init__(
            instructions=
                "Your name is Apollo. You will listen to the users and fill out the necessary information in TriageStructuredResponse."
                "You are a specialized Emergency Room (ER) triage monitoring agent trained to assess whether a patient’s condition is improving or worsening."
                "with that in mind keep your responses concise and to the point."
                "Keep responses short, direct, and professional."
                "do not use emojis, asterisks, markdown, or other special characters in your responses."
                "Maintain a serious, systematic, and calm tone — you are focused on evaluating the patient’s condition accurately."
                "Listen to the patient’s description of symptoms, pain levels, and any changes since the last check."
                "Ask one question at a time to determine changes in pain, breathing, consciousness, bleeding, or discomfort."
                "you will NOT speak to the user through voice, you are only listening.",
            stt=openai.STT(model="gpt-4o-transcribe"),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=openai.TTS(model="gpt-4o-mini-tts"),
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
            tool_choice=tool_choice,
            response_format=TriageStructuredResponse,
        ) as stream:
            async for chunk in stream:
                yield chunk

    async def tts_node(self, text: AsyncIterable[str], model_settings: ModelSettings):
        instruction_updated = False

        def output_processed(resp: TriageStructuredResponse):
            nonlocal instruction_updated
            if resp.get("voice_instructions") and resp.get("response") and not instruction_updated:
                # when the response isn't empty, we can assume voice_instructions is complete.
                # (if the LLM sent the fields in the right order)
                instruction_updated = True
                logger.info(
                    f"Applying TTS instructions before generating response audio: "
                    f'"{resp["voice_instructions"]}"'
                )
                with open("triage_log.json", "a") as f:
                    json.dump(resp, f)
                    f.write("\n")
                tts = cast(openai.TTS, self.tts)
                tts.update_options(instructions=resp["voice_instructions"])

        # process_structured_output strips the TTS instructions and only synthesizes the verbal part
        # of the LLM output
        return Agent.default.tts_node(
            self, process_structured_output(text, callback=output_processed), model_settings
        )

    async def transcription_node(self, text: AsyncIterable[str], model_settings: ModelSettings):
        # transcription_node needs to return what the agent would say, minus the TTS instructions
        return Agent.default.transcription_node(
            self, process_structured_output(text), model_settings
        )


async def entrypoint(ctx: JobContext):
    session = AgentSession(
        vad=silero.VAD.load(),
        turn_detection=EnglishModel(),
    )
    await session.start(agent=MyAgent(), room=ctx.room)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
