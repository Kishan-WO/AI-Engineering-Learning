"""Show exactly what is sent over HTTP to each profile, and everything that comes back.

    uv run python tasks/task4_show_raw_response.py
    uv run python tasks/task4_show_raw_response.py --profile local

The API key is never printed (the Authorization header is shown as ***).
"""

import argparse
import json
from typing import Any

import httpx

from llm_client import (
    PROFILES,
    MissingConfigError,
    chat,
    make_client,
    make_openai_client,
    model_name,
)

PROMPT = "Say hello in five words."


def shorten(value: Any, limit: int = 110) -> Any:
    """Copy of the JSON with long strings cut, so the whole structure fits on screen."""
    if isinstance(value, dict):
        return {key: shorten(item, limit) for key, item in value.items()}
    if isinstance(value, list):
        return [shorten(item, limit) for item in value]
    if isinstance(value, str) and len(value) > limit:
        return value[:limit] + "..."
    return value


def key_paths(value: Any, prefix: str = "") -> set[str]:
    """Every field name in a JSON value, as a path like choices[].message.content."""
    paths: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else key
            paths.add(path)
            paths |= key_paths(item, path)
    elif isinstance(value, list):
        for item in value:
            paths |= key_paths(item, f"{prefix}[]")
    return paths


def raw_call(profile_name: str) -> dict[str, Any]:
    """Send the request by hand with httpx (no SDK) and print the request and the response."""
    profile = PROFILES[profile_name]
    client = make_openai_client(profile_name)
    url = profile.base_url.rstrip("/") + "/chat/completions"
    body = {
        "model": model_name(profile_name),
        "messages": [{"role": "user", "content": PROMPT}],
        "temperature": 0,
        "max_tokens": 100,
    }
    headers = {
        "Authorization": f"Bearer {client.api_key}",
        "Content-Type": "application/json",
    }

    print(f"\n{'=' * 78}\nPROFILE: {profile_name}\n{'=' * 78}")
    print("\n--- 1. The HTTP request I send")
    print(f"POST {url}")
    print("Authorization: Bearer ***   (hidden)")
    print("Content-Type: application/json")
    print(json.dumps(body, indent=2, ensure_ascii=False))

    response = httpx.post(url, headers=headers, json=body, timeout=90)
    print("\n--- 2. The HTTP response")
    print(
        f"status: {response.status_code}   content-type: {response.headers.get('content-type')}"
    )
    data: dict[str, Any] = response.json()
    print(json.dumps(shorten(data), indent=2, ensure_ascii=False))

    print("\n--- 3. Top-level fields and their types")
    for key, item in data.items():
        print(f"  {key:<20} {type(item).__name__}")
    return data


def sdk_view(profile_name: str) -> None:
    """The same call through the OpenAI SDK: what the Python objects look like."""
    client, model = make_client(profile_name)
    completion = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": PROMPT}],
        temperature=0,
        max_tokens=100,
    )
    print("\n--- 4. The same call through the SDK")
    print(
        f"type(completion) = {type(completion).__module__}.{type(completion).__name__}"
    )
    print(
        f"completion.choices[0].message.content = {completion.choices[0].message.content!r}"
    )
    print(
        f"completion.choices[0].finish_reason   = {completion.choices[0].finish_reason!r}"
    )
    print(f"completion.usage                      = {completion.usage}")
    print(f"client.base_url                       = {client.base_url}")
    print("\n--- 5. My own Reply object (what chat() returns)")
    print(chat(client, model, PROMPT, max_tokens=100))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Show the raw request and response for each profile."
    )
    parser.add_argument("--profile", choices=sorted(PROFILES))
    args = parser.parse_args()

    results: dict[str, dict[str, Any]] = {}
    for name in [args.profile] if args.profile else sorted(PROFILES):
        try:
            results[name] = raw_call(name)
            sdk_view(name)
        except MissingConfigError as error:
            print(f"\n[{name}] skipped: {error}")

    if len(results) == 2:
        first, second = sorted(results)
        a, b = key_paths(results[first]), key_paths(results[second])
        print(
            f"\n{'=' * 78}\nSAME SHAPE? field names compared: {first} vs {second}\n{'=' * 78}"
        )
        print(f"fields in both ({len(a & b)}): {sorted(a & b)}")
        print(f"only in {first}: {sorted(a - b)}")
        print(f"only in {second}: {sorted(b - a)}")


if __name__ == "__main__":
    main()
