"""One client for every model: local Ollama or hosted Gemini, through the same OpenAI-compatible API.

Only three values differ between the two: the base URL, the API key and the model name. They live in
PROFILES and in the .env file, so the calling code never changes.
"""

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

load_dotenv(Path(__file__).parent.parent / ".env")  # day-4/.env, one level above tasks/


class MissingConfigError(RuntimeError):
    """A setting the profile needs is not in .env."""


@dataclass(frozen=True)
class Profile:
    name: str
    base_url: str
    api_key_env: (
        str | None
    )  # name of the environment variable that holds the key; None = no key needed
    model_env: str  # name of the environment variable that holds the model name
    default_model: str


PROFILES: dict[str, Profile] = {
    "local": Profile(
        name="local",
        base_url="http://localhost:11434/v1",  # Ollama
        api_key_env=None,
        model_env="LOCAL_MODEL",
        default_model="gemma3:270m",
    ),
    "gemini": Profile(
        name="gemini",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key_env="GEMINI_API_KEY",
        model_env="GEMINI_MODEL",
        default_model="",  # model names change often: set GEMINI_MODEL in .env
    ),
}


def make_openai_client(profile_name: str) -> OpenAI:
    """Build the client for a profile. Needs the key (if the profile uses one), not the model name."""
    profile = PROFILES[profile_name]
    api_key = "ollama"  # Ollama ignores it, but the client needs some text
    if profile.api_key_env is not None:
        api_key = os.environ.get(profile.api_key_env, "").strip()
        if not api_key:
            raise MissingConfigError(
                f"{profile.api_key_env} is empty: add your key to day-4/.env"
            )
    return OpenAI(base_url=profile.base_url, api_key=api_key)


def model_name(profile_name: str) -> str:
    """The model name for a profile, from .env (or the profile's default)."""
    profile = PROFILES[profile_name]
    model = os.environ.get(profile.model_env, "").strip() or profile.default_model
    if not model:
        raise MissingConfigError(
            f"{profile.model_env} is empty: add a model name to day-4/.env"
        )
    return model


def make_client(profile_name: str) -> tuple[OpenAI, str]:
    """Return (client, model name) for a profile. Raises MissingConfigError if .env is incomplete."""
    return make_openai_client(profile_name), model_name(profile_name)


@dataclass
class Reply:
    text: str
    prompt_tokens: int
    completion_tokens: int
    seconds: float


Message = dict[str, str]  # {"role": "system" | "user" | "assistant", "content": "..."}


def chat_messages(
    client: OpenAI,
    model: str,
    messages: list[Message],
    temperature: float = 0.0,
    max_tokens: int = 300,
) -> Reply:
    """Send a whole message list (the conversation so far) and return the answer."""
    start = time.perf_counter()
    response = client.chat.completions.create(
        model=model,
        # the SDK wants its own TypedDict types; plain {"role", "content"} dictionaries have the same shape
        messages=cast(list[ChatCompletionMessageParam], messages),
        temperature=temperature,
        max_tokens=max_tokens,
    )
    seconds = time.perf_counter() - start
    usage = response.usage
    return Reply(
        text=(response.choices[0].message.content or "").strip(),
        prompt_tokens=usage.prompt_tokens if usage else 0,
        completion_tokens=usage.completion_tokens if usage else 0,
        seconds=seconds,
    )


def chat(
    client: OpenAI,
    model: str,
    prompt: str,
    temperature: float = 0.0,
    max_tokens: int = 200,
) -> Reply:
    """Send one user message and return the answer with its token counts and timing."""
    return chat_messages(
        client, model, [{"role": "user", "content": prompt}], temperature, max_tokens
    )
