"""Day 4, task 5: a terminal chat that keeps the history in a Python list, and a cap that makes it forget.

    uv run python tasks/task5_terminal_chat.py                       # chat with the local model, full history
    uv run python tasks/task5_terminal_chat.py --cap 4               # keep only the last 4 messages
    uv run python tasks/task5_terminal_chat.py --profile gemini      # the hosted model
    uv run python tasks/task5_terminal_chat.py --demo --profile gemini    # a scripted conversation, with and without the cap

Commands inside the chat: /history  /cap N  /reset  /quit
"""

import argparse

from llm_client import (
    PROFILES,
    Message,
    MissingConfigError,
    Reply,
    chat_messages,
    make_client,
)

SYSTEM_PROMPT = "You are a helpful assistant. Answer in one short sentence."

# The scripted conversation: facts first, then questions that need those facts.
DEMO_FACTS = [
    "Hi, my name is Asha and I live in Ahmedabad.",
    "I like masala chai.",
    "I work as a software developer.",
    "My dog is called Moti.",
]
DEMO_QUESTIONS = ["What is my name?", "Which city do I live in?"]


class Chat:
    """A conversation. The model remembers nothing: this object re-sends the history on every call."""

    def __init__(self, profile: str, system: str, cap: int = 0) -> None:
        self.client, self.model = make_client(profile)
        self.system = system
        self.cap = cap  # 0 = keep everything
        self.history: list[Message] = []  # user and assistant messages only

    def messages_to_send(self, user_text: str) -> list[Message]:
        """What the model will receive this turn: the system prompt, the stored history, the new message."""
        return [
            {"role": "system", "content": self.system},
            *self.history,
            {"role": "user", "content": user_text},
        ]

    def say(self, user_text: str) -> tuple[Reply, list[Message]]:
        sent = self.messages_to_send(user_text)
        reply = chat_messages(self.client, self.model, sent)
        self.history += [
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": reply.text},
        ]
        if self.cap:
            self.history = self.history[
                -self.cap :
            ]  # the oldest messages are simply dropped
        return reply, sent


def shorten(text: str, limit: int = 60) -> str:
    return text if len(text) <= limit else text[: limit - 3] + "..."


def show_messages(messages: list[Message]) -> None:
    for number, message in enumerate(messages, 1):
        print(f"    {number}. {message['role']:<9} {shorten(message['content'])!r}")


def run_script(profile: str, cap: int) -> list[Message]:
    """Play the scripted conversation. Returns the messages sent for the first question."""
    chat = Chat(profile, SYSTEM_PROMPT, cap)
    print(
        f"\n--- {'cap = last ' + str(cap) + ' messages' if cap else 'no cap (full history)'}"
    )
    first_question_messages: list[Message] = []
    for turn, text in enumerate(DEMO_FACTS + DEMO_QUESTIONS, 1):
        reply, sent = chat.say(text)
        is_question = text in DEMO_QUESTIONS
        if text == DEMO_QUESTIONS[0]:
            first_question_messages = sent
        marker = "?" if is_question else " "
        print(
            f"  {marker} turn {turn}: sent {len(sent)} messages, {reply.prompt_tokens} prompt tokens"
        )
        print(f"      you:   {text}")
        print(f"      model: {reply.text}")
    return first_question_messages


def demo(profile: str, cap: int) -> None:
    print(f"Profile: {profile}   facts first, then two questions that need them")
    full = run_script(profile, cap=0)
    capped = run_script(profile, cap=cap)
    print("\n=== What the model received when asked 'What is my name?'")
    print(f"\n  without a cap ({len(full)} messages):")
    show_messages(full)
    print(f"\n  with the cap of {cap} ({len(capped)} messages):")
    show_messages(capped)
    print(
        "\nThe name was in the first user message. With the cap that message is gone, so the model never sees it."
    )


def interactive(profile: str, cap: int) -> None:
    chat = Chat(profile, SYSTEM_PROMPT, cap)
    print(
        f"Chat with {chat.model} ({profile}). Cap: {cap or 'none'}. Commands: /history /cap N /reset /quit\n"
    )
    while True:
        try:
            text = input("you> ").strip()
        except EOFError:
            break
        if not text:
            continue
        if text == "/quit":
            break
        if text == "/reset":
            chat.history.clear()
            print("(history cleared)")
            continue
        if text == "/history":
            print(
                f"(the list holds {len(chat.history)} messages; the system prompt is added on top)"
            )
            show_messages(chat.history)
            continue
        if text.startswith("/cap"):
            chat.cap = int(text.split()[1]) if len(text.split()) > 1 else 0
            chat.history = chat.history[-chat.cap :] if chat.cap else chat.history
            print(f"(cap is now {chat.cap or 'none'})")
            continue
        reply, sent = chat.say(text)
        print(f"model> {reply.text}")
        print(
            f"       [sent {len(sent)} messages, {reply.prompt_tokens} prompt tokens, {reply.seconds:.2f}s]"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="A terminal chat with manual history.")
    parser.add_argument("--profile", choices=sorted(PROFILES), default="local")
    parser.add_argument(
        "--cap",
        type=int,
        default=0,
        help="keep only the last N messages (0 = keep all)",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="play a scripted conversation, with and without a cap",
    )
    args = parser.parse_args()
    try:
        if args.demo:
            demo(args.profile, args.cap or 4)
        else:
            interactive(args.profile, args.cap)
    except MissingConfigError as error:
        raise SystemExit(f"[{args.profile}] {error}") from error


if __name__ == "__main__":
    main()
