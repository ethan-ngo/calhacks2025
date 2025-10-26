import logging
import json
from collections.abc import AsyncIterable
from typing import Optional, Callable

from dotenv import load_dotenv
from pydantic_core import from_json
from livekit.agents import Agent, AgentSession, ChatContext, FunctionTool, JobContext, ModelSettings, WorkerOptions, cli
from livekit.plugins import openai, silero
from livekit.plugins.turn_detector.english import EnglishModel

logger = logging.getLogger("structured-output")
load_dotenv()

class TriageStructuredResponse(dict):
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

        new_delta = resp["response"][len(last_response):]
        if new_delta:
            yield new_delta
        last_response = resp["response"]


class MyAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "Your name is Apollo. You will listen to the users and fill out the necessary information in TriageStructuredResponse."
                "You are a specialized Emergency Room (ER) triage monitoring agent trained to assess whether a patient’s condition is improving or worsening."
                "Keep responses concise, direct, and professional."
                "Do not speak to the user."
            ),
            stt=openai.STT(model="gpt-4o-transcribe"),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=None  # Remove TTS completely
        )

    async def llm_node(
        self, chat_ctx: ChatContext, tools: list[FunctionTool], model_settings: ModelSettings
    ):
        llm = self.llm
        tool_choice = model_settings.tool_choice if model_settings else None
        async with llm.chat(
            chat_ctx=chat_ctx,
            tools=tools,
            tool_choice=tool_choice,
            response_format=TriageStructuredResponse,
        ) as stream:
            async for chunk in stream:
                yield chunk


async def entrypoint(ctx: JobContext):
    session = AgentSession(
        vad=silero.VAD.load(),
        turn_detection=EnglishModel(),
    )
    await session.start(agent=MyAgent(), room=ctx.room)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
