# Task 5: a terminal chat with manual history, and why a chatbot forgets

Task: build a terminal chat that keeps the message history in a Python list. Then cap the history at the last 4 messages and show the forgetting happen.

Script: `day-4/tasks/task5_terminal_chat.py` (uses `chat_messages()` from `tasks/llm_client.py`).
```bash
uv run python tasks/task5_terminal_chat.py                        # chat with the local model, full history
uv run python tasks/task5_terminal_chat.py --cap 4                # keep only the last 4 messages
uv run python tasks/task5_terminal_chat.py --profile gemini       # the hosted model
uv run python tasks/task5_terminal_chat.py --demo --profile gemini    # scripted conversation, with and without the cap
```
Commands inside the chat: `/history` (show the list), `/cap N` (change the cap), `/reset` (clear the list), `/quit`.

## 1. How it works
The model is stateless: it keeps nothing between calls. The chat keeps the conversation itself, in a Python list, and **sends the whole list again on every turn**.

```python
class Chat:
    def __init__(self, profile, system, cap=0):
        self.client, self.model = make_client(profile)
        self.system = system
        self.cap = cap                      # 0 = keep everything
        self.history = []                   # user and assistant messages only

    def messages_to_send(self, user_text):
        return [{"role": "system", "content": self.system},
                *self.history,
                {"role": "user", "content": user_text}]

    def say(self, user_text):
        sent = self.messages_to_send(user_text)
        reply = chat_messages(self.client, self.model, sent)
        self.history += [{"role": "user", "content": user_text},
                         {"role": "assistant", "content": reply.text}]
        if self.cap:
            self.history = self.history[-self.cap:]     # the oldest messages are simply dropped
        return reply, sent
```
- The **system message** is added on top each time and is not counted in the cap.
- After every reply the new pair (user, assistant) is appended; with a cap, `history[-cap:]` throws away the oldest messages.
- With a cap of 4 the list always holds the last 2 exchanges. The next request is system + those 4 + the new question = 6 messages.

## 2. What the model really receives (real list)
Asked "What is my name?" at turn 5, without a cap (10 messages):
```
1. system    'You are a helpful assistant. Answer in one short sentence.'
2. user      'Hi, my name is Asha and I live in Ahmedabad.'
3. assistant 'Hello Asha, it is a pleasure to meet you in Ahmedabad!'
4. user      'I like masala chai.'
5. assistant 'Masala chai is a delicious and comforting choice!'
6. user      'I work as a software developer.'
7. assistant 'That is a great profession, Asha!'
8. user      'My dog is called Moti.'
9. assistant 'Moti is a wonderful name for a dog!'
10. user     'What is my name?'
```
With the cap of 4 (6 messages): the system message, then `I work as a software developer.`, `That is a great profession, Asha!`, `My dog is called Moti.`, `Moti is a wonderful name for a dog!`, and `What is my name?`. The first message, which holds the name and the city, is gone.

## 3. The scripted demo (real output)
Four facts (name and city, tea, job, dog), then two questions that need the first fact.

### Gemini (`gemini-3.1-flash-lite`)
| Turn | Sent without cap | Prompt tokens | Sent with cap 4 | Prompt tokens |
|---|---|---|---|---|
| 1 | 2 messages | 26 | 2 | 26 |
| 2 | 4 | 46 | 4 | 46 |
| 3 | 6 | 65 | 6 | 65 |
| 4 | 8 | 82 | 6 | 55 |
| 5 "What is my name?" | 10 | 99 | 6 | 55 |
| 6 "Which city do I live in?" | 12 | 113 | 6 | 52 |

| Question | Without a cap | With the cap |
|---|---|---|
| What is my name? | "Your name is Asha." | "Your name is Asha." (still right, see below) |
| Which city do I live in? | "You live in Ahmedabad." | **"You live in Mumbai."** (invented) |

### Local `gemma3:270m`
| Turn | Prompt tokens without cap | Prompt tokens with cap 4 |
|---|---|---|
| 1 | 34 | 34 |
| 2 | 62 | 62 |
| 3 | 85 | 85 |
| 4 | 108 | 73 |
| 5 | 129 | 73 |
| 6 | 151 | 72 |

| Question | Without a cap | With the cap |
|---|---|---|
| What is my name? | "My name is Asha." | **"My name is Gemma."** |
| Which city do I live in? | "I am located in Ahmedabad." | **"I am Gemma, a large language model."** |

## 4. What the results show
- **Cost grows with every turn without a cap.** Prompt tokens rose from 26 to 113 (Gemini) and from 34 to 151 (local) over six turns, because every earlier message is sent again. The same history is paid for again each time.
- **A cap keeps the cost flat.** With the cap the prompt size levelled off (55, 55, 52 on Gemini; 73, 73, 72 locally) instead of climbing.
- **A cap makes the model forget what was dropped.** The city was only in the first message. Gemini then **made up** an answer ("Mumbai") with no sign of doubt. The small local model forgot both facts and talked about itself ("I am Gemma").
- **Forgetting is not always complete.** Gemini still knew the name, because the assistant's own reply in turn 3, "That is a great profession, **Asha**!", was still inside the last 4 messages. The name survived through the model's own words. The city had no such trace.
- **A confident wrong answer is the real danger.** "Mumbai" shows that a model does not say "I don't know" when the fact has gone from its input; it fills the gap.
- **A tiny model is weak even with the full history.** `gemma3:270m` confused "I" and "you" ("Hi Asha, I'm Asha"), and in a separate interactive test it answered "I am Gemma, an open-weights Gemma model" to "What is my name?" even with nothing dropped.
- **Exact wording differs between runs**, but the pattern (growing cost, cap that flattens it, facts lost when their message is dropped) is stable.

## 5. A real interactive session (local model, piped input)
```
you> My name is Asha.        model> I am Asha.                         [sent 2 messages, 27 prompt tokens]
you> I like tea.             model> That's wonderful! 😊               [sent 4 messages, 45 prompt tokens]
you> What is my name?        model> I am Gemma, an open-weights Gemma model.   [sent 6 messages, 66 prompt tokens]
you> /history
(the list holds 6 messages; the system prompt is added on top)
    1. user 'My name is Asha.'            2. assistant 'I am Asha.'
    3. user 'I like tea.'                 4. assistant "That's wonderful! 😊"
    5. user 'What is my name?'            6. assistant 'I am Gemma, an open-weights Gemma model.'
you> /cap 2
(cap is now 2)
you> /history
(the list holds 2 messages; the system prompt is added on top)
    1. user 'What is my name?'            2. assistant 'I am Gemma, an open-weights Gemma model.'
```
`/history` shows exactly the list that will be sent next, which is everything the model will know about the chat.

## 6. Why a chatbot forgets (the answer for the day)
A language model only reads the text that arrives with the current request. Each request starts from nothing: nothing from the earlier request is stored inside the model, and its numbers do not change during a conversation. A chat feels continuous only because the application keeps a list of the earlier messages and sends them along again every time.

So a fact is available to the model for exactly as long as the application keeps sending the message that contains it. The moment that message is removed from the list (because it was cut to save cost, or because it no longer fits), the next request carries no trace of it, and the model cannot tell that it ever existed. It will either say it does not know, talk about something else, or invent an answer that sounds plausible.

## 7. Ways to keep more without paying for everything
| Approach | Idea |
|---|---|
| Keep the last N messages | What this task does; simple, but loses the oldest facts |
| Summarise the old messages | Replace them with a short summary; keeps the gist for the price of one extra call |
| Pin important facts | Always send a small fixed list (name, preferences) in the system message |
| Retrieve only what is relevant | Store everything outside, and send only the pieces related to the new question |

## Common mistakes
| Mistake | What happens |
|---|---|
| Sending only the new message | The model knows nothing about the conversation |
| Forgetting to append the assistant's reply | The next turn has no trace of what it said |
| Trimming so that the list starts with an assistant message | Some APIs reject it; trim after each exchange so the list starts with a user message |
| Counting the system message in the cap | The instructions get cut off first |
| Trusting an answer after trimming | The model may invent the missing fact |

## Quick check
- What does the application send on turn 5, and why does it get longer every turn?
- What exactly does `history[-cap:]` remove?
- Why did Gemini still know the name after the cap, but not the city?
- Why is "You live in Mumbai" worse than "I don't know"?
- In my own words, why does a chatbot forget a fact?
