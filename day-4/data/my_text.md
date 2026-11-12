# Sample text for token counting

This file is a small test input for `task1_token_counts.py`. It mixes the kinds of text that tokenise differently: plain English, Hindi, Hinglish, numbers and dates, code, a link, typos and a special-token string.

## 1. The same message in three languages

### English
A chatbot does not remember anything between calls. Every time the app sends a request, it must send the whole conversation again. If the conversation becomes too long, the oldest messages are removed, and the chatbot forgets them.

### Hindi
चैटबॉट एक कॉल से दूसरी कॉल तक कुछ भी याद नहीं रखता। हर बार जब ऐप अनुरोध भेजता है, तो उसे पूरी बातचीत दोबारा भेजनी पड़ती है। अगर बातचीत बहुत लंबी हो जाए, तो सबसे पुराने संदेश हटा दिए जाते हैं और चैटबॉट उन्हें भूल जाता है।

### Hinglish
Chatbot ek call se doosri call tak kuch bhi yaad nahi rakhta. Har baar jab app request bhejta hai, use poori baatcheet dobara bhejni padti hai. Agar baatcheet bahut lambi ho jaye, to sabse purane messages hata diye jate hain aur chatbot unhe bhool jata hai.

## 2. Numbers, dates and money
Order 20481 was placed on 2026-11-12 at 14:35 for Rs. 1,499.50. The phone number is +91 98765 43210 and the pin code is 380001. Pi is 3.14159265358979 and one million is 1,000,000.

## 3. Code
```python
def add_tag(tag: str, tags: list[str] | None = None) -> list[str]:
    if tags is None:
        tags = []
    tags.append(tag)
    return tags
```

## 4. A link, a path and a command
Docs: https://docs.python.org/3/library/argparse.html
Folder: C:\Projects\ai-eng\ai-eng-learning\day-4
Command: uv run python task1_token_counts.py my_text.md

## 5. Typos and odd spelling
helllo wrold, this sentense has sevral mispelled wrds. UPPERCASE WORDS AND lowercase words and MiXeD cAsE.

## 6. A special-token string inside normal text
The text <|endoftext|> appears here as ordinary words. Counting it must not crash the script.

## 7. Emoji and symbols
Great job 🙂 — 100% done ✅ — price ₹499 — temperature 36.6°C.
